from replikant.core import campaign_instance

with campaign_instance.register_activity(__name__, subname="visitor") as scope:

    @scope.route("/", methods=["GET"])
    def main_visitor():
        activity = scope.current_activity
        authProvider = scope.auth_provider

        # Complete the parameters with additional config
        parameters = dict()
        for k in activity.keys():
            if (k not in parameters) and (k.lower() != "template"):
                parameters[k] = activity.get(k)

        if authProvider.validates_connection("connected")[0]:
            return scope.render_template(path_template=activity.template, parameters=parameters)

            # NOTE: the rediction is faulty as virtual leads to automatically to connected anonymous user
            # NOTE: Redirection based on remembering what was the last visited page

            # if activity.has_next_activity():
            #     return redirect(activity.local_url_next)
            # else:
            #     return scope.render_template(template=activity.template)
        else:
            return scope.render_template(path_template=activity.template, parameters=parameters)


with campaign_instance.register_activity(__name__, subname="user") as scope_user:

    @scope_user.route("/", methods=["GET"])
    @scope_user.valid_connection_required
    def main_user():
        activity = scope_user.current_activity

        # Complete the parameters with additional config
        parameters = dict()
        for k in activity.keys():
            if (k not in parameters) and (k.lower() != "template"):
                parameters[k] = activity.get(k)

        return scope.render_template(path_template=activity.template, parameters=parameters)
