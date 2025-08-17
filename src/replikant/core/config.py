# coding: utf8
# license : CeCILL-C

# Global/Systems
from typing import Any
import pathlib
import logging
from collections import deque

# Yaml
from yaml import load

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader


class ConfigError(Exception):
    pass


class Config:
    def __init__(self, configuration_file: pathlib.Path):
        super().__init__()

        # Define logger
        self._logger = logging.getLogger(self.__class__.__name__)

        self._data: dict[str, Any] = dict()
        self.load_file(configuration_file)

        self._logger.info(f"WebService configuration made using {configuration_file}")

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def list_scopes(self) -> list[str]:

        # No activities to instanciate
        if "activities" not in self._data:
            return []

        list_scopes: list[str] = []
        for mod in self._data["activities"].keys():
            list_scopes.append(mod)

        return list_scopes

    def list_admin_units(self) -> list[str]:

        # No specific admin units to instanciate
        if ("admin" not in self._data) or ("units" not in self._data["admin"]):
            return []

        list_units: list[str] = []
        for cur_mod in self._data["admin"]["units"].keys():
            list_units.append(cur_mod)

        return list_units

    def get_admin_entrypoint(self) -> str:
        return self._data["admin"]["entrypoint"]

    def list_reachable_activities(self, start: str = "") -> list[str]:

        if not start:
            start = self._data["entrypoint"]

        next_activities: deque[str] = deque()
        next_activities.append(start)

        list_activities: list[str] = list()
        while next_activities:
            # Retrieve current activity information
            current_activity_name: str = next_activities.popleft()
            current_activity: dict[str, Any] = self._data["activities"][current_activity_name]
            list_activities.append(current_activity_name)

            #
            if "next" in current_activity:
                if isinstance(current_activity["next"], list):
                    for next_activity in current_activity["next"]:
                        if next_activity not in next_activities:
                            next_activities.append(next_activity)
                elif isinstance(current_activity["next"], str):
                    if current_activity["next"] not in next_activities:
                        next_activities.append(current_activity["next"])
                else:
                    type_next = type(current_activity["next"])
                    raise ConfigError(
                        f"The next activity field only accepts a list of names or one name, not a {type_next}"
                    )
        return list_activities

    def get_entrypoint(self) -> str:
        return self._data["entrypoint"]

    def load_file(self, configuration_file: pathlib.Path):
        try:
            with open(configuration_file, encoding="utf-8") as config_stream:
                self._data = load(config_stream, Loader=Loader)
        except Exception:
            raise ConfigError(f"Issue when loading {configuration_file}.", configuration_file)

    def get_scope_config(self, scope_name: str) -> dict[str, Any]:
        config: dict[str, Any] = dict()
        config["variables"] = self._data["variables"]
        if ("activities" in self._data) and (scope_name in self._data["activities"]):
            for k, v in self._data["activities"][scope_name].items():
                config[k] = v
        return config

    def get_admin_config(self, unit_name: str) -> dict[str, Any]:
        return self._data["admin"]["units"][unit_name]

    def get_activity_config(self, activity_name: str) -> dict[str, Any]:
        config: dict[str, Any] = self._data["activities"][activity_name]
        if ("next" in config.keys()) and (isinstance(config["next"], str)):
            config["next"] = [config["next"]]
        return config

    def get_activities_config(self, activities_name: list[str]) -> dict[str, Any]:
        configs: dict[str, Any] = dict()
        for activity_name in activities_name:
            configs[activity_name] = self.get_activity_config(activity_name)

        return configs
