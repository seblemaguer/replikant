# coding: utf8
# license : CeCILL-C

# Import Libraries
import json

import threading

from flask import current_app, request

from replikant.core import campaign_instance
from replikant.database import ModelFactory, db
from replikant.utils import redirect

from .model import Form

sem_form = threading.Semaphore()


class FormError(Exception):
    def __init__(self, message: str):
        super().__init__()
        self.message: str = message


class FileNotFound(FormError):
    pass


class MalformationError(FormError):
    pass


with campaign_instance.register_activity(__name__) as scope:

    @scope.route("/", methods=["GET"])
    @scope.valid_connection_required
    def main_default():
        # Get the current activity and the user
        activity = scope.current_activity

        # Create Form table and link the user to this form
        if ModelFactory().has(activity.name, Form):
            form_activity = ModelFactory().get(activity.name, Form)
            user = scope.auth_provider.user
            res = form_activity.query.filter_by(user_id=user.id)
            if res.first() is None:
                return scope.render_template(path_template=activity.template)
            else:
                next_urls: dict[str, str] = activity.next_local_urls
                if len(next_urls.keys()) > 1:
                    raise Exception("")
                activity_name = list(next_urls.keys())[0]
                return redirect(next_urls[activity_name])
        else:
            return scope.render_template(path_template=activity.template)

    @scope.route("/save", methods=["POST"])
    @scope.valid_connection_required
    def save():
        activity = scope.current_activity
        user = scope.auth_provider.user

        sem_form.acquire()
        if not ModelFactory().has(activity.name, Form):
            form_activity = ModelFactory().create(activity.name, Form)
        else:
            form_activity = ModelFactory().get(activity.name, Form)
            assert form_activity is not None  # NOTE: why is this needed?

        user.addRelationship(form_activity.__name__, form_activity, uselist=False)

        user = scope.auth_provider.user
        user_form_for_this_activity = getattr(user, form_activity.__name__)

        if user_form_for_this_activity is None:
            resp = form_activity.create(user_id=user.id)
            try:
                for field_key in request.form.keys():
                    if field_key.endswith("[]"):
                        value = request.form.getlist(field_key)
                        field_key = field_key.replace("[]", "")
                        value = ", ".join(value)
                    else:
                        value = request.form[field_key]

                    form_activity.addColumn(field_key, db.String)
                    resp.update(**{field_key: value})

                for field_key in request.files.keys():
                    form_activity.addColumn(field_key, db.BLOB)
                    with request.files[field_key].stream as f:
                        resp.update(**{field_key: f.read()})

            except Exception as ex:
                resp.delete()
                raise ex

        sem_form.release()

        next_urls: dict[str, str] = activity.next_local_urls
        if len(next_urls.keys()) > 1:
            raise Exception("")
        activity_name = list(next_urls.keys())[0]
        return redirect(next_urls[activity_name])


with campaign_instance.register_activity(__name__, subname="autogen") as scope_autogen:

    @scope_autogen.route("/", methods=["GET"])
    @scope_autogen.valid_connection_required
    def main_autogen():
        activity = scope_autogen.current_activity

        # On récup le json
        try:
            with open(
                current_app.config["REPLIKANT_RECIPE_DIR"] + "/" + activity.get("data"),
                encoding="utf-8",
            ) as form_json_data:
                form_json_data = json.load(form_json_data)
        except Exception:
            raise FileNotFound(
                "Issue when loading: " + current_app.config["REPLIKANT_RECIPE_DIR"] + "/" + activity.get("data")
            )

        names = []
        for component in form_json_data["components"]:
            if "id" not in component:
                raise MalformationError(
                    "An ID is required for each component in "
                    + current_app.config["REPLIKANT_RECIPE_DIR"]
                    + "/"
                    + activity.get("data")
                )

            if not (component["id"].replace("_", "").isalnum()):
                raise MalformationError(
                    "ID: " + component["id"] + " is incorrect. Only alphanumeric's and '_' symbol caracteres are allow."
                )

            if component["id"] in names:
                raise MalformationError("ID: " + component["id"] + " is already defined.")

            names.append(component["id"])

        # On ajoute le template à l'étape
        activity.update("template", "dynamic_form.tpl")
        activity.set_variable("form_json_data", form_json_data)

        return redirect(scope.url_for(scope.get_endpoint_for_local_rule("/")))
