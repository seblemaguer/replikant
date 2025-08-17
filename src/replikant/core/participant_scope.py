"""
replikant.core.Stage
===================

Module which defines all utilities to represent a activity in the pipeline

"""

from typing import Any, Callable, ParamSpec
from typing_extensions import override

from flask import g as flask_global
from flask import url_for as flask_url_for
from flask import session as flask_session

from replikant.utils import make_global_url

from .scope import Scope
from .providers import provider_factory, TemplateProvider
from .providers.auth import User

P = ParamSpec("P")


class ActivityError(Exception):
    """Default exception if an error happens at a specific activity."""

    pass


class ActivityNotFound(ActivityError):
    """Exception raised if the wanted activity doesn't exist."""

    pass


class Participant(User):
    __tablename__ = "Participants"


class Activity:
    """Definition of activity for a participant to do.

    Attributes
    ----------
    name: string
       The name of the activity
    params: ???
       The parameters needed by the activity to be executed properly
    mod_name: string
       The name of the activity
    mod_rep: string
       the name of the corresponding python module instanciating the participant scope
    """

    def __init__(self, name: str, config: dict[str, Any]):
        """Constructor

        Parameters
        ----------
        self: Stage
            The current object
        name: string
            The name of the activity
        data: None
            Not used (FIXME: check)
        """
        self.name: str = name
        self._config = config
        self._next_activities: dict[str, Activity] = dict()

        self._mod_name: str = self._config["type"]
        self._mod_rep: str = self._config["type"].split(":")[0]

        # Get rid of unwanted keywords (FIXME: it should not be there)
        del self._config["type"]
        if "next" in self._config:
            del self._config["next"]

    def add_next_activity(self, activity_name: str, activity: "Activity"):
        self._next_activities[activity_name] = activity

    @property
    def mod_rep(self) -> str:
        return self._mod_rep

    def update(self, name: str, val: object):
        """Method to update the value of a parameter of the activity

        Parameters
        ----------
        self: Stage
            The current object
        name: string
            The name of the parameter to update
        val: object
            The value of the parameter to update

        Raises
        ------
        AssertionError if name value is "type" or "name"
        """
        assert not (name == "type") and not (name == "name")

        if name not in self._config:
            self._config[name] = None

        self._config[name] = val

    @property
    def session(self):
        """Method to retrieve the information associated with the current
        activity from the current session.

        This method is treated as a property.

        Returns
        -------
        dict: the session dictionnary

        """
        if "activity:" + self.name not in flask_session.keys():
            flask_session["activity:" + self.name] = {}

        return flask_session["activity:" + self.name]

    @property
    def next_local_urls(self) -> dict[str, str]:
        """Generates the local URL of the next activity (treated a property)"""

        next_activities_url: dict[str, str] = dict()

        for next_activity_name, next_activity in self._next_activities.items():
            next_activities_url[next_activity_name] = next_activity.local_url

        return next_activities_url

    def has_next_activity(self):
        """Method which indicates if the current activity has a next activity

        Parameters
        ----------
        self: self
            The current object

        Returns
        -------
        bool: true if the activity has a next activity, false else
        """
        return self._next_activities

    @property
    def template(self) -> str | None:
        """Method to get the template associated with the current activity.

        This method is treated as a property.

        Parameters
        ----------
        self: self
            The current object

        Returns
        -------
        str | None: the template name/subpath or None

        """
        if "template" not in self._config:
            return None

        template = self._config["template"]
        template_path = provider_factory.get(TemplateProvider.NAME).get(template)
        return template_path

    @property
    def variables(self) -> dict[str, Any]:
        """Method to get all the variables associated with the current activity.
        This also includes the session variables. Each variable is
        identified by a string name.

        This method is treated as a property.

        Returns
        -------
        dict: the dictionnary of variables

        """
        variables: dict[str, Any] = dict()

        if "variables" in self._config:
            variables = self._config["variables"]

        if "session_variable" in self.session:
            for session_variable_name in self.session["session_variable"].keys():
                variables[session_variable_name] = self.session["session_variable"][session_variable_name]

        return variables

    def get_variable(self, name: str, default_value: object) -> object:
        """Method to get the value of a variable. If the variable is not
        available, the provided default value is returned.

        Parameters
        ----------
        name: string
            The name of the variable
        default_value: object
            The default value to return if the variable is not available

        Returns
        -------
        object: the value of the variable, if present, the default value else

        """
        if not (name in self.variables):
            return default_value

        return self.variables[name]

    def set_variable(self, name: str, value: object):
        """Method to set the value of a variable identified by its name.

        If the variable doesn't exist, a new SESSION variable will be created.

        Parameters
        ----------
        name: string
            The name of the variable
        value: object
            The new value of the variable

        """
        if not ("session_variable" in self.session):
            self.session["session_variable"] = {}
        self.session["session_variable"][name] = value

    @property
    def local_url(self):
        """Method to generate the URL of the current activity

        This method is treated as a property.

        Returns
        -------
        string: the URL of the current activity
        """
        return "/" + ParticipantScope.name_type + "/" + self._mod_name + "/" + self.name + "/"

    def __getitem__(self, name: str) -> object:
        """Method to get the value of a parameter

        Parameters
        ----------
        name: string
            The name of the parameter of the current activity

        Returns
        -------
        object: The value of the parameter

        Raises
        ------
        KeyError: if the name of the parameter is not available
        """
        if not self.has(name):
            raise KeyError(f"{name} is not part of the activity configuration")

        return self.get(name)

    def __contains__(self, name) -> bool:
        return self.has(name)

    def get(self, name: str) -> object | None:
        """Method to get the value of a parameter

        Parameters
        ----------
        name: string
            The name of the parameter of the current activity

        Returns
        -------
        object: The value of the parameter or None if the parameter doesn't exist
        """
        if name in self._config:
            return self._config[name]
        else:
            return None

    def has(self, name: str) -> bool:
        """Method to check if the value of a parameter is set

        Parameters
        ----------
        name: string
            The name of the parameter of the current activity

        Returns
        -------
        boolean: True if the parameter exists and has a value, False else
        """
        return name in self._config

    def keys(self) -> set[str]:
        return set(self._config.keys())

    def get_scope_name(self) -> str:
        return self._mod_name

    @override
    def __str__(self) -> str:
        str_rep = f"Activity({self.name}, {self._mod_name})\n"
        str_rep += f"\t- config = {self._config}\n"
        str_rep += f"\t- next_activities = {self._next_activities}"
        return str_rep


class ParticipantScope(Scope):
    """Class which defines the entry point of a activity.

    A activity is composed of subactivities which are instance of the class Stage.

    Attributes
    ----------
    current_activity: Stage
         The current subactivity
    """

    user_base = Participant
    name_type = "run"
    homepage = "/"

    def __init__(self, namespace: str, subname: str | None = None):
        super().__init__(namespace, subname)
        self._activities: dict[str, Activity] = dict()

    def add_activity(self, activity_name: str, activity: Activity):
        self._activities[activity_name] = activity

    @override
    def local_rule(self) -> str:
        """Method which defines the rule to access the current activity

        Returns
        -------
        string: the rule to access the current activity
        """
        return "/" + self.__class__.name_type + "/" + self.get_mod_name() + "/<activity_name>"

    @property
    def current_activity(self) -> Activity:
        """Method which allows to access the current activity from the flask/Werkzeug proxy.

        This method is treated as a property.

        Returns
        -------
        Stage: the current activity
        """
        return flask_global.activity

    # FIXME: invalid override
    @override
    def render_template(
        self,
        path_template: str | None = None,
        args: dict[str, Any] = dict(),
        variables: dict[str, Any] | None = None,
        parameters: dict[str, Any] | None = None,
        filters: dict[str, Callable] | None = None,
    ) -> str:
        """Method which renders the given template."""
        internal_args: dict[str, Any] = dict()
        internal_args.update(self._config["variables"])
        internal_args["THIS_SCOPE"] = "scope:" + str(self.scope_rep)

        # Save the URL of the next step
        global_url_next: dict[str, str] = dict()
        if len(self.current_activity.next_local_urls.keys()) > 1:
            for local_url_next_name, local_url_next in self.current_activity.next_local_urls.items():
                global_url_next[local_url_next_name] = make_global_url(local_url_next)

        elif len(self.current_activity.next_local_urls.keys()) == 1:
            local_url_next = next(iter(self.current_activity.next_local_urls.values()))
            global_url_next["default"] = make_global_url(local_url_next)
            internal_args["url_next"] = global_url_next

        if variables is not None:
            internal_args.update(variables)

        if parameters is not None:
            internal_args.update(parameters)
        internal_args.update(args)

        # Achieve the rendering
        return super().render_template(path_template, args=internal_args, filters=filters)

    @override
    def url_for(self, endpoint: str, activity_name: str | None = None, **kwargs) -> str:  # type: ignore
        """Method to generate a dynamic URL given a specific endpoint and
        potential activity name. If the activity name is None, the current
        activity name is used.

        Parameters
        ----------
        endpoint: string
            the end point
        activity_name: string
            The name of the activity
        kwargs: dict
            Any additionnal parameters which should be forwarded

        Returns
        -------
        string: the generated URL
        """

        if activity_name is None:
            activity_name = self.current_activity.name

        return flask_url_for(endpoint, activity_name=activity_name, **kwargs)

    def get_endpoint_for_local_rule(self, rule: str) -> str:
        """Method to generate the end point for the given local rule

        Parameters
        ----------
        rule: string
            The rule

        Returns
        -------
        string: the generated endpoint
        """
        return f"{self.name}.local_url@{rule.replace('.', '_')}"

    @override
    def route(self, rule: str, **options: Any) -> Callable[..., Any]:
        """Method to define the route decorator which will be in charge of
        redericting the client to the given rule.

        Parameters
        ----------
        rule: str
            The rule which will be redirected too
        options: dict
            Additional options to pass to the redirection pipeline

        Returns
        -------
        Callable[..., Any]
            The wrapping function
        """

        def decorated(lambda_fun: Callable[P, Any]) -> Any:
            def view_wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
                # Retrieve the activity name AND do NOT propagate it!
                activity_name: str = str(kwargs["activity_name"])
                del kwargs["activity_name"]

                # Just some nice debugging information to determine where we are
                self._logger.debug("Goto ==> %s" % activity_name)
                self._logger.debug("Current session:")
                for k in flask_session.keys():
                    self._logger.debug(" - %s: %s" % (k, flask_session[k]))

                # Define the the current activity
                flask_global.activity = self._activities[activity_name]

                return lambda_fun(*args, **kwargs)

            self.add_url_rule(rule, f"local_url@{rule.replace('.', '_')}", view_wrapper, **options)

            return view_wrapper

        return decorated

    @property
    def logger(self):
        return self._logger


class ActivityGraph:
    def __init__(self, entry_point: str, list_activities: list[str], activities_config: dict[str, Any]):
        self._entry_point: str = entry_point
        self._dependency_graph: dict[str, list[str]] = dict()
        self._dict_activities: dict[str, Activity] = dict()

        self._load_activities(list_activities, activities_config)

    def connect_activity(self, activity_name: str, participant_scope: ParticipantScope):
        for cur_activity_name, activity in self._dict_activities.items():
            if activity.mod_rep == activity_name:
                participant_scope.add_activity(cur_activity_name, activity)

    def _load_activities(self, list_activities: list[str], activities_config: dict[str, Any]):

        # Generate dependency graph
        for activity_name in list_activities:
            cur_activity_config = activities_config[activity_name]
            if "next" in cur_activity_config:
                self._dependency_graph[activity_name] = cur_activity_config["next"]

        # Instanciate the activities
        for activity_name in list_activities:
            self._dict_activities[activity_name] = Activity(activity_name, activities_config[activity_name])

        # Now define the dependencies
        for activity_name in list_activities:
            if activity_name in self._dependency_graph.keys():
                for next_activity in self._dependency_graph[activity_name]:
                    self._dict_activities[activity_name].add_next_activity(
                        next_activity, self._dict_activities[next_activity]
                    )

    def get_activity(self, name: str) -> Activity:
        return self._dict_activities[name]

    def has_next_activity(self, activity: str) -> bool:
        return (activity in self._dependency_graph.keys()) and (len(self._dependency_graph[activity]) > 0)

    def get_next_activities(self, name: str) -> list[Activity]:
        assert self.has_next_activity(name)

        # Get the names first
        next_activities: list[Activity] = []
        for name_next_activity in self._dependency_graph[name]:
            cur_activity: Activity = self._dict_activities[name_next_activity]
            next_activities.append(cur_activity)

        return next_activities

    def get_entry_point_local_url(self) -> str:
        return self._dict_activities[self._entry_point].local_url

    def list_activities(self) -> dict[str, Activity]:
        return self._dict_activities
