# coding: utf8
# license : CeCILL-C

# Import Libraries
from flask import current_app, request
from flask_mail import Mail, Message

from replikant.core import ParticipantScope, AdminScope
from replikant.utils import redirect, make_global_url

from .provider import UserAuth, BadCredential

current_app.config.setdefault("MAIL_SERVER", "smtp.googlemail.com")
current_app.config.setdefault("MAIL_PORT", 587)
current_app.config.setdefault("MAIL_USE_TLS", True)
current_app.config.setdefault("MAIL_USERNAME", "pseudo@gmail.com")
current_app.config.setdefault("MAIL_DEFAULT_SENDER", "pseudo@gmail.com")
current_app.config.setdefault("MAIL_PASSWORD", "password")

ParticipantScope.set_authProvider(UserAuth)
mail = Mail()
userModel = ParticipantScope.get_user()

with ParticipantScope(__name__) as scope:

    @scope.route("/", methods=["GET"])
    def main():
        activity = scope.current_activity

        if scope.auth_provider.validates_connection("connected"):
            return redirect(activity.local_url_next)
        else:
            try:
                token = request.args.get("token")
                scope.auth_provider.connect(token=token)
                return scope.render_template("legal.tpl", token=token)
            except BadCredential:
                pass

            return scope.render_template()

    @scope.route("/register", methods=["POST"])
    def register():
        activity = scope.current_activity

        if scope.auth_provider.validates_connection("connected"):
            return redirect(activity.local_url_next)
        else:
            try:
                token = request.args.get("token")
                scope.auth_provider.connect(token=token)
                scope.auth_provider.user.update(active=True)

                return redirect(activity.local_url_next)
            except BadCredential:
                pass

            return scope.render_template()


with AdminScope(__name__) as am:
    # Routes
    @am.route("/")
    @am.valid_connection_required
    def panel():
        return am.render_template("admin/panel.tpl")

    @am.route("/send_invitation")
    @am.valid_connection_required
    def invitation():
        return am.render_template("admin/send_invitation.tpl")

    @am.route("/send_invitation/send", methods=["POST"])
    @am.valid_connection_required
    def send_invitation():
        try:
            emails = request.form["emails"].split(",")
            message = "<html><body><p>" + request.form["message"].replace("\n", "</p><p>") + "</p>"
            title_message = request.form["title_message"]
            for email in emails:
                bdd_mistake = False
                user = None
                try:
                    user = userModel.create(email=email)
                    message = (
                        message
                        + "<p><a href='"
                        + make_global_url("/?token=" + str(user.token))
                        + "'>"
                        + make_global_url("/?token=....")
                        + "</a></p></body></html>"
                    )
                except Exception:
                    bdd_mistake = True

                if not (bdd_mistake):
                    try:
                        msg = Message(title_message, recipients=[email])
                        msg.html = message
                        mail.send(msg)
                    except Exception:
                        if user is not None:
                            user.delete()
                        return redirect(
                            am.url_for(am.get_endpoint_for_local_rule("/configuration")) + "?falseCredential"
                        )

            return redirect(am.url_for(am.get_endpoint_for_local_rule("/pending_invitation")))

        except Exception:
            return redirect(am.url_for(am.get_endpoint_for_local_rule("/configuration")) + "?falseCredential")

    @am.route("/pending_invitation")
    @am.valid_connection_required
    def pending_invitation():
        users = userModel.query.all()
        return am.render_template("/admin/pending.tpl", users=users)

    @am.route("/configuration", methods=["GET"])
    @am.valid_connection_required
    def config():
        config = {}

        falseCredential = False
        if request.args.get("falseCredential") is not None:
            falseCredential = True

        config["MAIL_SERVER"] = current_app.config["MAIL_SERVER"]
        config["MAIL_PORT"] = current_app.config["MAIL_PORT"]
        config["MAIL_USE_TLS"] = current_app.config["MAIL_USE_TLS"]
        config["MAIL_USERNAME"] = current_app.config["MAIL_USERNAME"]
        config["MAIL_PASSWORD"] = current_app.config["MAIL_PASSWORD"]

        return am.render_template("/admin/config.tpl", falseCredential=falseCredential, **config)

    @am.route("/configuration/update", methods=["POST"])
    @am.valid_connection_required
    def update_config():
        current_app.config["MAIL_SERVER"] = request.form["MAIL_SERVER"]
        current_app.config["MAIL_PORT"] = request.form["MAIL_PORT"]
        current_app.config["MAIL_USE_TLS"] = request.form["MAIL_USE_TLS"]
        current_app.config["MAIL_USERNAME"] = request.form["MAIL_USERNAME"]
        current_app.config["MAIL_DEFAULT_SENDER"] = request.form["MAIL_USERNAME"]
        current_app.config["MAIL_PASSWORD"] = request.form["MAIL_PASSWORD"]

        mail.init_app(current_app)

        return redirect(am.url_for(am.get_endpoint_for_local_rule("/")))
