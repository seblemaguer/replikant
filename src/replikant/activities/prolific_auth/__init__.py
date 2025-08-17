# coding: utf8
# license : CeCILL-C

# Import Libraries
from flask import request

from replikant.core import campaign_instance, ParticipantScope
from replikant.utils import redirect
import logging

from .provider import ProlificAuthProvider

ParticipantScope.set_auth_provider(ProlificAuthProvider)

logger = logging.getLogger()

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

        # Authenticate
        prolific_pid: str = request.form["PROLIFIC_PID"]
        study_id: str = request.form["STUDY_ID"]
        session_id: str = request.form["SESSION_ID"]

        if not prolific_pid:
            raise Exception("The participant ID is not defined")

        if not study_id:
            logger.warning("The study ID is not defined")

        if not session_id:
            logger.warning("The session ID is not defined")

        assert isinstance(scope.auth_provider, ProlificAuthProvider)
        scope.auth_provider.connect(prolific_pid, study_id, session_id)

        # Move to the next activity
        activity = scope.current_activity
        next_urls: dict[str, str] = activity.next_local_urls
        if len(next_urls.keys()) > 1:
            raise Exception("Multiple next activitys from the logging page are not yet supported")
        activity_name = list(next_urls.keys())[0]
        return redirect(next_urls[activity_name])
