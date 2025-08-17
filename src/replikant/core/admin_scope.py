from typing import Any, Callable, ParamSpec
from replikant.core.providers.auth import User
from replikant.core.providers.base import Provider, provider_factory
from replikant.core.providers.content import TemplateProvider
from typing_extensions import override

from flask import abort
from flask import url_for as flask_url_for
from .scope import Scope

P = ParamSpec("P")


class Administrator(User):
    __tablename__ = "Administrators"

    def __init__(self):
        super().__init__()


class AdminScope(Scope):
    user_base = Administrator
    name_type = "admin"
    homepage = "/admin"

    @override
    def local_rule(self) -> str:
        return f"/{self.__class__.name_type}/{self.get_mod_name()}/"

    @override
    def render_template(
        self,
        path_template: str | None = None,
        args=dict(),
        variables=dict(),
        parameters=dict(),
        filters: dict[str, Callable] | None = None,
    ) -> str:
        internal_args = dict()
        internal_args.update(self._config["variables"])
        internal_args.update(args)
        if variables is not None:
            internal_args.update(variables)
        if parameters is not None:
            internal_args.update(parameters)

        internal_args["THIS_SCOPE"] = "scope:" + str(self.scope_rep)

        return super().render_template(path_template=path_template, args=internal_args, filters=filters)

    @override
    def url_for(self, endpoint: str, **kwargs: Any) -> str:
        return flask_url_for(endpoint, **kwargs)

    def get_endpoint_for_local_rule(self, rule: str):
        return f"{self.name}.local_url@{rule.replace('.', '_')}"

    @override
    def route(self, rule: str, **options: Any) -> Callable[..., Any]:
        def decorated(f: Callable[P, Any]) -> Any:
            def wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
                return f(*args, **kwargs)

            self.add_url_rule(rule, "local_url@" + str(rule.replace(".", "_")), wrapper, **options)

            return wrapper

        return decorated

    @override
    def valid_connection_required(self, f: Callable[P, bool]) -> Callable[P, bool]:
        def wrapper(*args: P.args, **kwargs: P.kwargs):
            (user_validates, condition) = self.auth_provider.validates_connection()

            if not user_validates:
                if condition == "connected":
                    abort(401)
                # else:
                #     raise Exception("No handler to deal with invalid condition \"%s\"" % condition)

            return f(*args, **kwargs)

        return wrapper

    def local_url(self) -> str:
        return f"{self.__class__.name_type}/{self.get_mod_name()}/"

    @override
    def __enter__(self):
        """Prepare scope execution

        This mainly consists of preparing the templates (for now)
        """

        self._logger.info(f"Registering scope: {self.scope_rep}")
        template_provider: Provider = provider_factory.get("templates")
        if isinstance(template_provider, TemplateProvider):
            template_provider.register_admin_unit(self.scope_rep)
        return self
