from flask import request

from replikant.core import campaign_instance, ParticipantScope
from replikant.utils import redirect

from .provider import EmailAuthProvider
from .model import NotAnEmail

ParticipantScope.set_auth_provider(EmailAuthProvider)


with campaign_instance.register_activity(__name__) as scope:

    @scope.route("/", methods=["GET"])
    def main():
        activity = scope.current_activity

        if scope.auth_provider.validates_connection("connected")[0]:
            next_urls: dict[str, str] = activity.next_local_urls
            if len(next_urls.keys()) > 1:
                raise Exception("Multiple next activitys from the logging page are not yet supported")
            activity_name = list(next_urls.keys())[0]
            return redirect(next_urls[activity_name])
        else:
            return scope.render_template(path_template=activity.template)

    @scope.route("/register", methods=["POST"])
    def register():
        activity = scope.current_activity
        email: str = request.form["email"]

        try:
            assert isinstance(scope.auth_provider, EmailAuthProvider)
            scope.auth_provider.connect(email)
        except NotAnEmail as e:
            scope.logger.error(f"Problem with the email: {e}")
            return redirect(scope.url_for(scope.get_endpoint_for_local_rule("/")))

        next_urls: dict[str, str] = activity.next_local_urls
        if len(next_urls.keys()) > 1:
            raise Exception("Multiple next activitys from the logging page are not yet supported")
        activity_name = list(next_urls.keys())[0]
        return redirect(next_urls[activity_name])
