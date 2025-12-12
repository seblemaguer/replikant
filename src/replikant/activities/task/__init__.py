# coding: utf8

from replikant.activities.task.src.task import SampleModelInTransaction
from werkzeug import Response
from flask import request, abort

# Replikant
from replikant.core import campaign_instance
from replikant.utils import redirect
from replikant.database import commit_all

# Current package
from .src import task_manager, TransactionalObject


class TaskAlternateError(Exception):
    pass


class MalformationError(TaskAlternateError):
    def __init__(self, message):
        self.message = message


with campaign_instance.register_activity(__name__) as scope:

    @scope.route("/", methods=["GET"])
    @scope.valid_connection_required
    def main():
        """Entry point for the Task

        This function prepare the template and defines some key helper
        internal functions to generate the information required during
        the save activity. These functions are:
          - get_syssamples which provides the list of selected samples per *given system*
          - save_field_name which *has to be called* to get the field value (score, preference selection...)
            during the saving

        """

        # Get the current Activity and the corresponding task
        activity = scope.current_activity
        if not task_manager.has(activity.name):
            task = task_manager.register(activity.name, activity)
        else:
            task = task_manager.get(activity.name)

        # Define steps information
        nb_systems_per_step = int(activity["nb_systems_per_step"]) if ("nb_systems_per_step" in activity) else 1
        if nb_systems_per_step <= 0:
            nb_systems_per_step = len(list(task.systems.keys()))

        max_steps = int(activity["nb_steps"])  # TODO: add a default if ("nb_steps" in activity) else 0
        nb_intro_steps: int = int(activity["nb_intro_steps"]) if ("nb_intro_steps" in activity) else 0

        # Load transaction information
        transaction_timeout_seconds = activity["transaction_timeout_seconds"]
        if transaction_timeout_seconds is not None:
            task.set_timeout_for_transaction(int(transaction_timeout_seconds))

        # Get the user
        user = scope.auth_provider.user

        # Get the current step
        cur_step = task.nb_steps_complete_by(user)

        # Find out the current step is an introduction or not
        is_intro_step = False
        if cur_step < nb_intro_steps:
            is_intro_step = True

        if cur_step < max_steps:
            syssamples_for_this_step = task.get_step(
                cur_step, user, nb_systems=nb_systems_per_step, is_intro_step=is_intro_step
            )

            def _get_samples(*system_names):
                systems = []
                if len(system_names) == 0:
                    for syssample in syssamples_for_this_step.values():
                        systems.append(syssample)
                else:
                    for name_system in system_names:
                        systems.append(syssamples_for_this_step[name_system])

                return systems

            def _generate_field_name(sample: SampleModelInTransaction, basename: str, record_name: str | None = None):
                basename = basename.replace(TransactionalObject.RECORD_SEP, "_")

                # Make sure the record exist and get a real name if record name is None
                user = scope.auth_provider.user
                record = task.get_record(user, record_name)

                # ID of the field
                ID = TransactionalObject.RECORD_SEP.join(["save", record, basename, str(sample.ID)])

                # Associate field to record
                _ = task.add_field_to_record(user, ID, record_name)

                return ID

            def _prepare_new_record(name: str):
                # Record new record for current step and current user
                user = scope.auth_provider.user
                _ = task.create_new_record(user, name)
                return name

            # scope.logger.debug(f"Sample selected for this step are {get_syssamples()}")

            # Update information related to the steps
            if is_intro_step:
                max_steps = nb_intro_steps
            else:
                max_steps = max_steps - nb_intro_steps
                cur_step = cur_step - nb_intro_steps

            parameters = {
                "max_steps": max_steps,
                "step": cur_step + 1,
                "intro_step": is_intro_step,
                "list_samples": _get_samples,
            }
            filters = {
                "generate_field_name": _generate_field_name,
                "prepare_new_record": _prepare_new_record,
            }

            # Complete the parameters with additional config
            for k in activity.keys():
                if (k not in parameters) and (k.lower() != "template"):
                    parameters[k] = activity.get(k)

            return scope.render_template(path_template=activity.template, parameters=parameters, filters=filters)
        else:
            next_urls: dict[str, str] = activity.next_local_urls
            if len(next_urls.keys()) > 1:
                raise Exception("More than one folloing URL is not yet supported for a step of a task")
            activity_name = list(next_urls.keys())[0]
            return redirect(next_urls[activity_name])

    @scope.route("/save", methods=["POST"])
    @scope.valid_connection_required
    def save() -> Response:
        """Saving routine of the task

        This method is called after the submission of the form
        implemented in the template associated to the step of the
        task.
        This method does:
          0. requiring a exclusive access to the db to avoid concurrency issue
          1. parsing the values of each *field* recorded by the method =save_field_name*
          2. filling the database *and creating new columns if necessary!*

        """
        activity = scope.current_activity
        task = task_manager.get(activity.name)  # TaskManager(activity).get(activity.name)
        user = scope.auth_provider.user
        skip_after_n_step = activity.get("skip_after_n_step")

        # Log the request form for debugging purposes
        scope.logger.debug("#### The request form ####")
        scope.logger.debug(request.form)  # TODO: prettify!
        scope.logger.debug("#### <END>The request form ####")

        # Initialize the number of intro steps
        nb_intro_steps: int = int(activity["nb_intro_steps"]) if ("nb_intro_steps" in activity) else 0
        cur_step: int = task.nb_steps_complete_by(user)

        # Validate is the current step is an introduction step
        intro_step = False
        if cur_step < nb_intro_steps:
            intro_step = True

        # Fail if there is no transactions associated to the user
        if not task.has_transaction(user):
            raise Exception("No information about the current user is available stack (likely a connection timeout)")

        # Save
        all_records = task.get_all_records(user)
        for _, all_field_names in all_records.items():
            try:
                # Save responses from the user
                for field_type, field_list in [
                    ("string", request.form),
                    ("file", request.files),
                ]:
                    for field_key in field_list.keys():
                        if (field_key[:5] == "save:") and (field_key in all_field_names):
                            # Several values can be returned for one key (MultiDict)
                            #    -> use d.get_list(key) instead d[key]
                            if len(field_list.getlist(field_key)) > 1:
                                field_value = str(field_list.getlist(field_key))
                            else:
                                field_value = field_list[field_key]

                            # Get the name of the info to save
                            field_key = field_key[5:]
                            (
                                _,
                                field_name,
                                obfuscated_sample,
                            ) = field_key.split(TransactionalObject.RECORD_SEP)
                            name_col = field_name

                            # Extract the sample information
                            system, syssample_id = task.get_in_transaction(user, obfuscated_sample)
                            sample_id = int(syssample_id)

                            # Get the value of the info
                            value = ""
                            if field_type == "string":
                                sysval = task.get_in_transaction(user, field_value)
                                if sysval is None:
                                    value = field_value
                                else:
                                    _, syssample_id = sysval
                                    value = syssample_id

                            else:
                                with field_value.stream as f:
                                    value = f.read()

                            scope.logger.info(f"([sample={sample_id}, system={system}] - {name_col}: {value})")
                            _ = task.model.create(
                                user_id=user.id,
                                intro=intro_step,
                                step_idx=cur_step,
                                sample_id=sample_id,
                                info_type=name_col,
                                info_value=value,
                                operation_type="record",
                                commit=False,
                            )
                        elif field_key[:5] != "save:":
                            name_col = field_key
                            value = field_list[field_key]
                            # Extract the sample information
                            info = task.get_in_transaction(user, value)
                            if info is None:
                                raise Exception(
                                    "If the field name is not generated to be part of the transaction, "
                                    + "it means the value should contain the obfusted sample: "
                                    + f"field_name={name_col}, field_value={value}"
                                )
                            system, syssample_id = info
                            sample_id = int(syssample_id)

                            scope.logger.info(f"([sample={sample_id}, system={system}] - {name_col}: True)")
                            _ = task.model.create(
                                user_id=user.id,
                                intro=intro_step,
                                step_idx=cur_step,
                                sample_id=sample_id,
                                info_type=name_col,
                                info_value=True,
                                operation_type="record",
                                commit=False,
                            )
                        else:
                            raise Exception(f"The field structure is not support: {field_key}")

            except Exception as e:
                task.delete_transaction(user)
                raise e

        # Commit the results and clean the transations of the user
        commit_all()
        task.delete_transaction(user)

        if skip_after_n_step is not None:
            if (cur_step + 1) % skip_after_n_step == 0:
                next_urls: dict[str, str] = activity.next_local_urls
                if len(next_urls.keys()) > 1:
                    raise Exception("Only, one following step is supported here, configuration seems bogus")
                activity_name = list(next_urls.keys())[0]
                return redirect(next_urls[activity_name])

        return redirect(scope.url_for(scope.get_endpoint_for_local_rule("/")))

    @scope.route("/monitor", methods=["POST"])
    @scope.valid_connection_required
    def monitor() -> Response:
        """Saving routine of the task

        This method is called after the submission of the form
        implemented in the template associated to the step of the
        task.
        This method does:
          0. requiring a exclusive access to the db to avoid concurrency issue
          1. parsing the values of each *field* recorded by the method =save_field_name*
          2. filling the database *and creating new columns if necessary!*

        """
        # NOTE: to debug in case some is wrong, just run the following line
        activity = scope.current_activity
        task = task_manager.get(activity.name)  # TaskManager(activity).get(activity.name)
        user = scope.auth_provider.user

        # Log the request form for debugging purposes
        scope.logger.debug("#### The request form ####")
        scope.logger.debug(request.json)  # TODO: prettify
        scope.logger.debug("#### <END>The request form ####")

        # Initialize the number of intro steps
        nb_intro_steps = int(activity.get("nb_intro_steps"))
        cur_step: int = task.nb_steps_complete_by(user)

        # Validate is the current step is an introduction step
        intro_step = False
        if nb_intro_steps >= cur_step:
            intro_step = True

        # Lock DB so we can update it (NOTE SLM: not sure that's what this does!)
        if not task.has_transaction(user):
            abort(408)

        try:
            # Get the JSON data sent in the POST request
            # FIXME: deal with multiple samples would be great
            monitoring_info = request.json
            obfuscated_sample_id = monitoring_info.get("sample_id")
            info_type = monitoring_info.get("info_type")
            info_value = monitoring_info.get("info_value")

            # TODO: should be generalised
            if isinstance(info_value, str) and info_value.startswith("sampleid:"):
                _, syssample_id = task.get_in_transaction(user, info_value.replace("sampleid:", ""))
                info_value = int(syssample_id)
            elif isinstance(info_value, list):
                values = []
                for cur_value in info_value:
                    if isinstance(cur_value, str) and cur_value.startswith("sampleid:"):
                        scope.logger.debug(f"Monitoring current value[list]: {cur_value}")
                        _, syssample_id = task.get_in_transaction(user, cur_value.replace("sampleid:", ""))
                        cur_value = int(syssample_id)
                    values.append(str(cur_value))
                info_value = f"[{','.join(values)}]"

            # Retrieve the sample information
            system, syssample_id = task.get_in_transaction(user, obfuscated_sample_id)
            sample_id = int(syssample_id)

            # Insert info in the model
            scope.logger.info(f"([sample={sample_id}, system={system}] - {info_type}: {info_value})")
            _ = task.model.create(
                user_id=user.id,
                intro=intro_step,
                step_idx=cur_step,
                sample_id=sample_id,
                info_type=info_type,
                info_value=info_value,
                operation_type="monitor",
                commit=False,
            )
        except Exception as e:
            scope.logger.error(e, stack_info=True, exc_info=True)
            return Response(status=500)

        # Commit the results and clean the transations of the user
        commit_all()

        return Response(status=204)
