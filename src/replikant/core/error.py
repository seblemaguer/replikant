# coding: utf8
# license : CeCILL-C

import datetime
from typing import Any, ParamSpec
import logging
import traceback

from flask import render_template as flask_render_template
from flask import Flask
from flask import request
from werkzeug.exceptions import HTTPException

from replikant.utils import make_global_url

from .core import campaign_instance, ParticipantScope
from .providers import provider_factory, TemplateProvider, AssetsProvider
from .providers.auth import VirtualAuthProvider

P = ParamSpec("P")


class ErrorHandler:
    """Class which defines how errors are handled."""

    def __init__(self, app: Flask, config: dict[str, Any]):
        """Constructor

        Parameters
        ----------
        self: ErrorHandler
            The current object
        """
        self._logger = logging.getLogger(self.__class__.__name__)
        self._config: dict[str, Any] = config

        # Define the default handler to be the method "error"
        app.register_error_handler(Exception, self.error)

    def error(self, e: Exception) -> str:
        """The error handler routine entry point.

        It is also in charge of execution the alternative handler, if one is defined for the type of error
        given in parameters.

        Parameters
        ----------
        self: ErrorHandler
            The current object
        e: Exception
            The exception to handle
        """

        # Add user information (TODO: for now the user is not known!)
        try:
            auth = ParticipantScope.get_auth_provider()
            user_id = auth.user.user_id
        except Exception:
            auth = VirtualAuthProvider()
            user_id = "Not Connected"

        # Deal and show error information on the server side
        code: int = 500
        error_stacktrace = ""
        for eline in traceback.format_exc().splitlines():
            error_stacktrace += f"{eline}\n"
        if (isinstance(e, HTTPException)) and (e.code is not None):
            code = e.code

        if code == 500:
            self._logger.critical(f'[{user_id}] Error "{e}"')
            self._logger.critical(f"[{user_id}] Traceback:\n{error_stacktrace}")
        else:
            self._logger.error(f"[{user_id}] Error 404 - could not access url: {request.url}")
            if code != 404:
                self._logger.error(f"[{user_id}] Traceback:\n{error_stacktrace}")

        variables: dict[str, Any] = self._config["variables"]

        def _get_asset(name: str, rep: str | None = None) -> str:
            asset_provider: AssetsProvider = provider_factory.get(AssetsProvider.NAME)  # type: ignore
            return make_global_url(asset_provider.local_url(name, rep))

        # Add overall information
        variables.update({"now": datetime.datetime.now(), "source_url": request.url})
        variables.update({"auth": auth})

        # Add eror information
        variables.update({"code": code, "error_message": str(e)})
        if (code < 400) or (code >= 500):
            variables["error_stacktrace"] = error_stacktrace

        # Render the error page
        template_provider: TemplateProvider = provider_factory.get(TemplateProvider.NAME)  # type: ignore
        if code == 401:
            return flask_render_template(
                template_name_or_list=template_provider.get("auth_failed.tpl"),
                get_template=provider_factory.get(TemplateProvider.NAME).get,  # type: ignore
                get_asset=_get_asset,
                entry_point=make_global_url(campaign_instance.get_entrypoint()),
                **variables,
            )
        else:
            return flask_render_template(
                template_name_or_list=template_provider.get("error.tpl"),
                get_template=provider_factory.get(TemplateProvider.NAME).get,  # type: ignore
                get_asset=_get_asset,
                **variables,
            )


error_handler: ErrorHandler | None = None
