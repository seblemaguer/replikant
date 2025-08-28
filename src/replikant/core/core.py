# python
from typing import Any
import logging
from logging import Logger
import importlib
import copy


from werkzeug import Response
from flask import request, current_app

from ..utils import redirect

# Replikant core imports
from .providers import provider_factory
from .providers.content import TemplateProvider
from .config import Config
from .admin_scope import AdminScope
from .participant_scope import ParticipantScope, ActivityGraph
from .providers.auth import VirtualAuthProvider, AnonAuthProvider


class CampaignInstanceError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class InitialiseEvaluation(CampaignInstanceError):
    def __init__(self, message: str):
        super().__init__(message)


class Campaign:
    """Entry point of the campaign instance

    This class deals with all the instantiations necessary for the evaluation campaign to be functionnal.
    This implies:
      - loading the scopes, admin units and participant activities
      - registering the different rules and providers

    To do so, a configuration object is necessary
    """

    def __init__(
        self,
        config: Config | None = None,
    ):
        """Initialisation method

        Just initialise the different fields. If a configuration
        object is provided, it also load all the components necessary
        for the campaign to run

        Parameters
        ----------
        config : Config| None
            The optional configuration object
        """
        # Define logger
        self._logger: Logger = logging.getLogger(self.__class__.__name__)
        self._config: Config | None = config
        self.activities: set[str] = set()
        self._activity_graph: ActivityGraph | None = None

        # The admin scope do not require a complicated setup, let' just deal with them in
        self._admin_entrypoint: str = ""
        self._admin_units: dict[str, AdminScope] = dict()

        if config is not None:
            self.load_config(config)

    def load_config(self, config: Config):
        """Load the configuration and setup the campaign instance

        Parameters
        ----------
        config : Config
            The new configuration to be loaded
        """
        self._config = config

        # self._load_participant_scopes()
        self._load_admin_units()
        self._load_activities()

        # Register the providers some important information
        provider_factory.get(TemplateProvider.NAME).register_recipe()  # type: ignore
        if isinstance(ParticipantScope.get_auth_provider(), VirtualAuthProvider):
            ParticipantScope.set_auth_provider(AnonAuthProvider)

        # Register the instance entry points
        current_app.add_url_rule("/", "entrypoint", self.goto_entrypoint)
        current_app.add_url_rule("/admin/", "entrypoint_admin", self.goto_admin_entrypoint)

    def _load_participant_scopes(self):
        """Load the participant scopes and fill the list of available participant scopes"""
        assert self._config is not None

        activity_scopes: list[str] = self._config.list_scopes()
        for cur_scope in activity_scopes:
            self._instanciate_activity(cur_scope)

    def _load_admin_units(self):
        """Load the admin units and fill the list of available admin units

        This helper also prepare the admin entry point
        """
        assert self._config is not None

        # Load admin units
        admin_units: list[str] = self._config.list_admin_units()
        for cur_unit in admin_units:
            self._instanciate_admin_unit(cur_unit)

        # Load the entry point unit
        self._admin_entrypoint = self._config.get_admin_entrypoint()
        self._instanciate_admin_unit(self._admin_entrypoint)

    def _load_activities(self):
        """Load the different participant activities of the campaigns

        This helper also prepare the campaign entry point
        """
        assert self._config is not None

        # Define the graph
        activities: list[str] = self._config.list_reachable_activities()
        activity_configs = self._config.get_activities_config(activities)
        self._activity_graph = ActivityGraph(self._config.get_entrypoint(), activities, activity_configs)
        for cur_activity in self._activity_graph.list_activities().values():
            self._instanciate_activity(cur_activity.mod_rep)

    def _instanciate_admin_unit(self, name_type: str):
        """Instanciate an admin unit and add it to the list of available admin units

        Parameters
        ----------
        name_type : str
            The name of the type of the module
        """

        name_elts = name_type.split(":")
        name_type = name_elts[0]

        # The name is admin unit is already loaded
        if name_type in self.activities:
            return

        self._logger.info(f'Loading admin unit "{name_type}"')

        _ = importlib.import_module(f"replikant.admin_units.{name_type}")
        self.activities.add(name_type)

    def _instanciate_activity(self, name_type: str):
        """Instanciate an activity and add it to the list of available activities

        Parameters
        ----------
        name_type : str
            The name of the type of the module

        """
        name_elts = name_type.split(":")
        name_type = name_elts[0]

        # The name is module is already loaded
        if name_type in self.activities:
            return

        self._logger.info(f'Loading activity "{name_type}"')

        try:
            _ = importlib.import_module(f"replikant.activities.{name_type}")
            self.activities.add(name_type)
        except Exception:
            raise InitialiseEvaluation(f'The activity type "{name_type}" is invalid, please fix the configuration file')

    def goto_entrypoint(self) -> Response:
        """Generate the HTTP response to go to the entry point of the campaign

        Returns
        -------
        Response
            The HTTP Response
        """

        assert self._config is not None
        assert self._activity_graph is not None

        args_GET: list[str] = []
        for args_key in request.args.keys():
            args_GET.append(f"{args_key}={request.args[args_key]}")

        redirect_url: str = f"{self.get_entrypoint()}?{'&'.join(args_GET)}"
        return redirect(redirect_url)

    def get_entrypoint(self) -> str:
        assert self._activity_graph is not None
        return self._activity_graph.get_entry_point_local_url()

    def goto_admin_entrypoint(self) -> Response:
        """Generate the HTTP response to go to the admin entry point of the campaign

        Returns
        -------
        Response
            The HTTP Response
        """
        args_GET: list[str] = []
        for args_key in request.args.keys():
            args_GET.append(f"{args_key}={request.args[args_key]}")

        admin_unit = self.get_admin_units()[self._admin_entrypoint]
        redirect_url: str = f"/{admin_unit.local_url()}/?{'&'.join(args_GET)}"
        return redirect(redirect_url)

    def register_activity(self, name: str, subname: str | None = None) -> ParticipantScope:
        assert self._activity_graph is not None
        assert self._config is not None

        # Get the activity and connect it to the activity graph
        activity_name = name.replace("replikant.activities.", "")
        activity = ParticipantScope(namespace=activity_name, subname=subname)
        self._activity_graph.connect_activity(activity_name, activity)

        # Define the config of the activity/participant scope
        config: dict[str, Any] = self._config.get_scope_config(activity_name)
        activity.set_config(config)

        return activity

    def register_admin_unit(self, name: str, subname: str | None = None) -> AdminScope:
        assert self._config is not None
        unit_name = name.replace("replikant.admin_units.", "")

        # Generate config by merging global unit config with more specific ones
        # NOTE: dirty hack in case of dictionnary, only 1 level supported (else everything is overriden)
        config = self._config.get_scope_config(unit_name)
        config = copy.deepcopy(config)

        for k, v in self._config.get_admin_config(unit_name).items():
            if k not in config:
                config[k] = v
            elif isinstance(v, dict):
                for k2, v2 in v.items():
                    config[k][k2] = v2
            else:
                config[k] = v

        self._logger.debug(f"=====> Admin unit configuration: {config}")

        # Instanciate the admin scope and register it!
        admin_scope = AdminScope(namespace=unit_name, subname=subname)
        admin_scope.set_config(config)
        self._admin_units[unit_name] = admin_scope
        return admin_scope

    def get_admin_units(self) -> dict[str, AdminScope]:
        return self._admin_units

    def get_activity_graph(self) -> ActivityGraph | None:
        return self._activity_graph


campaign_instance: Campaign = Campaign()
