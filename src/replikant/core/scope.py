# Python
from typing import Any, Callable, ParamSpec
from types import TracebackType
from typing_extensions import override
import abc
import logging

# Flask
from flask import Blueprint, current_app, abort
from flask import render_template as flask_render_template

# Replikant
from replikant.core.providers.content import AssetsProvider
from replikant.utils import make_global_url, make_absolute_path
from replikant.database import Model

from .providers import provider_factory, Provider, TemplateProvider
from .providers.auth import AuthProvider, User, VirtualAuthProvider

P = ParamSpec("P")


class ScopeError(Exception):
    """Default exception for scope errors

    Attributes
    ----------
    message: string
        The error message
    """

    def __init__(self, message: str, ex: Exception | None = None):
        super().__init__()
        self.message = message
        self.ex = ex

    @override
    def __str__(self):
        return f"{self.message}: {self.ex}"


class MalformationError(ScopeError):
    """Exception raised when something is malformed"""

    pass


class MalformationTemplateError(MalformationError):
    """Exception raised when a template is malformed

    Attributes
    ==========
    file: string or File
       The template file
    """

    def __init__(self, tpl_file: str, ex: Exception):
        super().__init__(f'The template "{tpl_file}" is malformed', ex)


class NotAnAuthProvider(ScopeError):
    """Exception raised when the provider given is not an AuthProvider"""

    pass


class NotAUserModel(ScopeError):
    """Exception raised when an object is not instanciating the UserModel class"""

    pass


class OverwritingClassAttributesForbidden(ScopeError):
    """Exception raised when an object is not instanciating the UserModel class"""

    pass


class UserModelAttributesMeta(type(Model)):
    @override
    def __setattr__(self, name: str, val: Any):
        if hasattr(self, "__lock__"):
            if self.__lock__ and not (name == "__lock__"):  # type: ignore
                if hasattr(self, name):
                    raise OverwritingClassAttributesForbidden(f"Class Attributes: {name} already existing.", None)

        super().__setattr__(name, val)


class Scope(Blueprint, abc.ABC):
    """The baseline scope class"""

    NAMESPACE_SEPARATOR: str = ":"
    default_checker_handlers: dict[str, Callable[[User | None], bool]] = dict()
    user_base: type[User] | None = None
    name_type: str = "<invalid>"
    homepage: str = "<invalid>"

    def __init__(self, namespace: str, subname: str | None = None):
        """Initialisation method

        Parameters
        ----------
        namespace : str
            The namespace which indicates the class of the scope
        subname : str, optional
            The subname of the scope for better identification
        """

        # Define logger
        self._logger = logging.getLogger(f"{self.__class__.__name__} ({namespace}{Scope.NAMESPACE_SEPARATOR}{subname})")
        self._config: dict[str, Any] = dict()
        self._namespace = namespace  # .split(".")
        self._subname = subname
        self._checker_handlers: dict[str, Callable[[User | None], bool]] = dict()
        self.scope_rep = self._namespace  # [2]

        super().__init__(self.__class__.name_type + Scope.NAMESPACE_SEPARATOR + self.get_mod_name(), namespace)

        if not (provider_factory.exists("auth_mod_" + self.__class__.name_type)):
            self.__class__.set_auth_provider(VirtualAuthProvider)

    def set_config(self, config: dict[str, Any]):
        """Set the configuration of the scope (clear all previous keys!)

        Parameters
        ----------
        data : dict[str, Any]
            the new configuration of the scope
        """

        self._config = config

    def update_config(self, config: dict[str, Any]):
        """Update the current configuration of the scope using the information of a given configuration dictionary

        Parameters
        ----------
        config : dict[str, Any]
            the given configuration dictionary

        """

        for key, val in config.items():
            self._config[key] = val

    def get_config(self) -> dict[str, Any] | None:
        """Get the configuration of the scope

        Returns
        -------
        dict[str, Any] | None
            the configuration of the scope

        """

        return self._config

    def connect_checker_handler(self, name: str, handler: Callable[[User | None], bool]):
        """Add a connection checking handler

        Parameters
        ----------
        name : str
            The name of the condition
        handler : Callable[[User | None], bool]
            The handler to validate/unvalidate the condition necessary
            for the connection
        """
        self._checker_handlers[name] = handler

    def disconnect_checker_handler(self, name: str):
        """Remove a connection condition

        Parameters
        ----------
        name : str
            The name of the condition to remove

        """
        _ = self._checker_handlers.pop(name, None)

    @abc.abstractmethod
    def url_for(self, end_point: str, **kwargs: Any) -> str:
        """Generates the URL for the scope

        This is an abstract method here

        Parameters
        ----------
        end_point : str
            The URL end point
        **kwargs: ignore
        """
        raise NotImplementedError("This is an abstract method")

    def __enter__(self):
        """Prepare scope execution

        This mainly consists of preparing the templates (for now)
        """

        self._logger.info(f"Registering scope: {self.scope_rep}")
        template_provider: Provider = provider_factory.get("templates")
        if isinstance(template_provider, TemplateProvider):
            template_provider.register_scope(self.scope_rep)
        return self

    def __exit__(self, exctype: type[BaseException] | None, excinst: BaseException | None, exctb: TracebackType | None):
        """This mainly consists of registering the blueprint

        Raises
        ------
        MalformationError
            The scopes already exists and therefore can't be executed

        """

        try:
            current_app.register_blueprint(self, url_prefix=self.local_rule())
            self._logger.info("%s is loaded and bound to: %s" % (self.get_mod_name(), self.local_rule()))
        except Exception:
            raise MalformationError(f"There are already a {self.__class__.__name__} scope named: {self.get_mod_name()}")

    def local_rule(self) -> str:
        """Generate the local rule to be appended to the URL

        This is simply a concatenation of the name_type and the mod_name

        Returns
        -------
        str
            the local rule
        """
        return f"/{self.__class__.name_type}/{self.get_mod_name()}"

    def get_mod_name(self) -> str:
        """Generate the mod name

        This is simply a concatenation of the mod rep and the subname
        (if available)

        Returns
        -------
        str
            the mod name
        """
        if self._subname is None:
            return self.scope_rep
        else:
            return self.scope_rep + ":" + self._subname

    def valid_connection_required(self, f: Callable[P, bool]) -> Callable[P, bool]:
        """Geenerate wrapper to validate the connection

        Parameters
        ----------
        f : Callable[P, bool]
            TODO: I have no idea here!

        Returns
        -------
        Callable[P, bool]
            The wrapper function

        Raises
        ------
        Exception
            If there is no handler for the connection
        """

        def wrapper(*args: P.args, **kwargs: P.kwargs) -> bool:
            (user_validates, condition) = self.auth_provider.validates_connection()

            if not user_validates:
                if condition == "connected":
                    abort(401)
                elif condition in self._checker_handlers:
                    return self._checker_handlers[condition](Scope.get_user())
                elif condition in self.__class__.default_checker_handlers:
                    return self.__class__.default_checker_handlers[condition](Scope.get_user())
                else:
                    raise Exception(f'No handler to deal with invalid condition "{condition}"')

            return f(*args, **kwargs)

        return wrapper

    @property
    def auth_provider(self) -> AuthProvider:
        """Provider the access to the current authentication provider

        Returns
        -------
        AuthProvider
            The authentication provider

        """
        return self.__class__.get_auth_provider()

    @classmethod
    def connect_default_checker_handler(cls, name: str, handler: Callable[[User | None], bool]):
        """Add a new default condition checker

        Parameters
        ----------
        name : str
            The name of the condition to check at a scope level
        handler : Callable[[User | None], bool]
            The function which is doing the checking
        """

        cls.default_checker_handlers[name] = handler

    @classmethod
    def disconnect_default_checker_handler(cls, name: str):
        """Remove a checker from the default condition checker list

        Parameters
        ----------
        name : str
            The name of the condition
        """

        _ = cls.default_checker_handlers.pop(name, None)

    @classmethod
    def get_auth_provider(cls) -> AuthProvider:
        """Retrieve the authentication provider of the scope

        Returns
        -------
        AuthProvider
            The authentication provider of the scope

        Raises
        ------
        Exception
            if the provider of the class is mistyped and is not an authentication provider
        """

        if not (provider_factory.exists(f"auth_mod_{cls.name_type}")):
            cls.set_auth_provider(VirtualAuthProvider)

        provider: Provider = provider_factory.get(f"auth_mod_{cls.name_type}")
        if not isinstance(provider, AuthProvider):
            raise Exception("The provider is not an authentication provider (not a subclass of AuthProvider)")

        return provider

    @classmethod
    def set_auth_provider(cls, cls_auth: type[AuthProvider]):
        """Define the authentication provider

        Parameters
        ----------
        cls_auth : type[AuthProvider]
            The authentication provider class
        """
        cls.init_user(cls_auth)
        if cls_auth == VirtualAuthProvider:
            _ = cls_auth("auth_mod_" + cls.name_type, cls.homepage, None)
        else:
            _ = cls_auth("auth_mod_" + cls.name_type, cls.homepage, cls.get_user())

    @classmethod
    def get_user(cls) -> User | None:
        """Get the user model of the current scope

        Returns
        -------
        User | None
            The user model
        """

        return cls.user

    @classmethod
    def init_user(cls, cls_auth: type[AuthProvider]):
        """Initialise the user model associated to the scope

        Parameters
        ----------
        cls_auth : type[AuthProvider]
            The authentication provider class

        Raises
        ------
        MalformationError
            TODO: unclear why this is necessary
        """

        user_base: type[User] | None = cls_auth.__userBase__
        table_name: str = cls.user_base.__tablename__
        table_type: str = cls.__name__

        if not hasattr(cls, "user_model"):
            cls.user = UserModelAttributesMeta(
                table_type,
                (
                    User,
                    Model,
                ),
                {"__abstract__": True, "__tablename__": table_name},
            )
            setattr(cls.user, "__lock__", True)

        if user_base is not None:
            if hasattr(cls, "user_model_init"):
                if user_base in list(cls.user.__bases__):
                    pass
                else:
                    raise MalformationError("Two differents auth provider defined for " + cls.__name__ + ".")
            else:
                cls.user.__lock__ = False
                cls.user = UserModelAttributesMeta(
                    table_type,
                    (cls.user, user_base),
                    {"__abstract__": False, "__tablename__": table_name},
                )
                setattr(cls.user, "__lock__", True)
                cls.user_model_init = True

    def render_template(
        self,
        path_template: str | None = None,
        args: dict[str, Any] = dict(),
        variables: dict[str, Any] | None = None,
        parameters: dict[str, Any] | None = None,
        filters: dict[str, Callable] | None = None,
    ) -> str:
        """Renders the given template

        Parameters
        ----------
        path_template: str
            The path to the template
        args: Dict[str, str]
            The dictionnary of arguments
        variables: Dict[str, str]
            The dictionnary of variables
        parameters: Dict[str, str]
            The dictionnary of parameters

        Returns
        -------
        str
            the rendered template
        """

        # Add variables & parameters to args
        args.update(self._config["variables"])
        if variables is not None:
            args.update(variables)
        if parameters is not None:
            args.update(parameters)

        # Add homepage and authentication
        try:
            args["auth"] = provider_factory.get(f"auth_mod_{self.__class__.name_type}")
            args["homepage"] = make_global_url(self.__class__.homepage)
        except Exception:
            args["auth"] = VirtualAuthProvider()
            args["homepage"] = make_global_url("/")

        # FIXME: this should be more jinja friendly
        def _read_file(filename: str) -> str:
            with open(make_absolute_path(filename)) as f:
                return f.read()

        def _get_asset(name: str, rep: str | None = None) -> str:
            asset_provider: AssetsProvider = provider_factory.get(AssetsProvider.NAME)  # type: ignore
            assert_local_url = asset_provider.local_url(name, rep)
            return make_global_url(assert_local_url)

        args["get_asset"] = _get_asset
        args["get_template"] = provider_factory.get(TemplateProvider.NAME).get  # type: ignore

        # Add filters which cannot be annotated
        current_app.jinja_env.filters["to_url"] = make_global_url
        if filters is not None:
            for filter_id, filter in filters.items():
                current_app.jinja_env.filters[filter_id] = filter

        # Get the scope default template
        if path_template is None:
            path_template = f"{self.scope_rep}.tpl"

        provider: TemplateProvider = provider_factory.get("templates")  # type: ignore
        path_template = provider.get(path_template)

        try:
            return flask_render_template(path_template, **args)
        except Exception as ex:
            raise MalformationTemplateError(path_template, ex)
