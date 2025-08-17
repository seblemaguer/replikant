# coding: utf8

import logging

# Replikant
from replikant.core import campaign_instance
from replikant.activities.task import task_manager

logger = logging.getLogger()

with campaign_instance.register_activity(__name__) as scope:

    @scope.route("/", methods=["GET"])
    @scope.valid_connection_required
    def main():
        """Entry point for the activity

        This function prepare the template and defines some key helper
        internal functions to generate the information required during
        the save activity. These functions are:
          - get_syssamples which provides the list of selected samples per *given system*
          - save_field_name which *has to be called* to get the field value (score, preference selection...)
            during the saving

        """

        # Get the current Activity and the corresponding task
        summary_activity = scope.current_activity
        next_urls: dict[str, str] = summary_activity.next_local_urls

        # Get the user
        user = scope.auth_provider.user

        activitys = campaign_instance.get_activity_graph().list_activities()
        list_task_sections = []
        section_information = dict()
        for k, activity in activitys.items():
            if activity.get_scope_name() == "task":
                # Force the registering of the task
                if not task_manager.has(activity.name):
                    task = task_manager.register(activity.name, activity)
                else:
                    task = task_manager.get(activity.name)

                # Retrieve the information
                max_steps = int(activity["nb_steps"])  # TODO: add a default if ("nb_steps" in activity) else 0
                cur_step = task.nb_steps_complete_by(user)

                # Generate the required parameters for the template
                section_information[activity.name] = {
                    "label": activity["label"] if "label" in activity else activity.name,
                    "url": next_urls[activity.name],
                    "cur_step": cur_step,
                    "max_steps": max_steps,
                }
                list_task_sections.append(activity.name)
            else:
                logger.debug(f"ignore {k} because {activity.get_scope_name()}")

        parameters = {"list_task_sections": list_task_sections, "section_information": section_information}

        # Complete the parameters with additional config
        for k in summary_activity.keys():
            if (k not in parameters) and (k.lower() != "template"):
                parameters[k] = summary_activity.get(k)

        return scope.render_template(path_template=summary_activity.template, parameters=parameters)
