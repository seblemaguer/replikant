"""Module providing elementary helpers to authenticate in Replikant"""

# Python
from typing_extensions import override
from typing import Callable, Any
import random
import abc

# Flask
from flask import session as flask_session
from flask import current_app, redirect
from werkzeug.wrappers import Response

# Replikant
from replikant.database import Column, db, Model
from replikant.utils import make_global_url
from .base import provider_factory, Provider  # FIXME: provider_factory is not great here, it should be removed


class AuthProviderError(Exception):
    """The generic error of any authentication provider"""

    pass


class NotConnectedError(Exception):
    """The error indicating an issue during the connection phase of the provider"""

    pass


class User(Model):
    """The model of User

    A user is at least a participant, but this can be extended if needed.
    This class needs to be extended to cover the needs of your authentication methodology.
    """

    __abstract__ = True
    __tablename__ = "User"
    id = Column(db.Integer, primary_key=True, autoincrement=True)
    conditions = Column(db.String, default="")

    def has_validated(self, condition: str) -> bool:
        """Check if the user already validated the given condition

        Parameters
        ----------
        value : str
            the condition to check

        Returns
        -------
        bool
            True if the condition is validated, False if not
        """

        list_conditions = self.conditions.split(",")
        return condition in list_conditions

    @property
    def user_id(self) -> str:
        return f"{self.id} [anonymous]"

    def validates(self, condition: str):
        """Record that the user validates the given condition

        Parameters
        ----------
        condition : str
            the given condition the user validates

        """

        if not self.has_validated(condition):
            if self.conditions:
                self.conditions += ",%s" % condition
            else:
                self.conditions += str(condition)

    @override
    def __str__(self):
        the_str = f'User "{self.id}":\n'
        the_str += f"\t- validated_conditions: {self.conditions}"
        return the_str


class AuthProvider(Provider, metaclass=abc.ABCMeta):
    """Default authentication provider"""

    __userBase__: type[User] | None = None
    checkers: dict[str, Callable[[User], bool]] = dict()

    def __init__(self, name: str, local_url_homepage: str, user_model: User | None):
        """Initialisation method

        Parameters
        ----------
        name : str
            The name of the authentication scope
        local_url_homepage : str
            The local URL of the scope requiring the authentication
        user_model : User
            The user model
        """

        super().__init__()
        self.local_url_homepage: str = local_url_homepage
        self.name: str = name
        self.user_model: User | None = user_model
        self._logger.debug(f"Initialisation with (name = {name}, local_url_homepage = {local_url_homepage})")

        try:
            current_app.add_url_rule("/deco/<name>", "deco", self.__class__.disconnect_action)
        except AssertionError:
            pass

        self._logger.info(f'Authentication provided "{name}" is loaded')

        provider_factory.set(name, self)

    def _connect(self, user: User) -> None:
        """Connect a user

        This is done by simply adding the user to the session dictionnary

        Parameters
        ----------
        user : User
            The user to connect
        """
        if self.user_model.__abstract__:
            self.session["user"] = user
        else:
            self.session["user"] = user.id

    def disconnect(self):
        """Disconnect the user

        This is done by simply removing the user to the session dictionnary
        """
        del self.session["user"]

    def validates_connection(self, condition: str | None = None) -> tuple[bool, str]:
        """Check if the user already validated the given condition

        Parameters
        ----------
        condition : str or None
            The optional condition to check to validate the connection

        Returns
        -------
        Tuple[bool, str]
            - True if the connection is validated, False if not
            - the checker name
        """

        if condition is not None:
            if condition != "connected":
                return (AuthProvider.checkers[condition](self.user), condition)
            else:
                return ("user" in self.session, "connected")
        else:
            validated = ("user" in self.session, "connected")
            if not validated[0]:
                return validated

            for checker_name in AuthProvider.checkers:
                if not AuthProvider.checkers[checker_name](self.user):
                    validated = (False, checker_name)
                    break

            return validated

    @classmethod
    def connect_checker(cls, checker_name: str, checker: Callable[[User], bool]):
        """Add a checking routine providing a dynamic condition to validate during the connection

        Parameters
        ----------
        checker_name : str
            the name of the checker
        checker : Callable
            the checking function which will be called during the
            connection
        """
        AuthProvider.checkers[checker_name] = checker

    @classmethod
    def disconnect_action(cls, name: str) -> Response:
        """Disconnect (log-out) the user

        Parameters
        ----------
        name : str
            the name of the provider

        Returns
        -------
        Response
            The flask Response object redirecting the client to the
            proper page after the disconnect
        """
        provider: Provider = provider_factory.get(name)
        if not isinstance(provider, AuthProvider):
            raise Exception(f"{name} is not an authentication provider (type = {provider.__class__})")

        provider.disconnect()
        return redirect(make_global_url(provider.local_url_homepage))

    @property
    def user(self) -> User:
        """Provide an easy way to access the user information

        Returns
        -------
        User
            The model of the user
        """
        if self.user_model.__abstract__:  # type: ignore
            return self.session["user"]
        else:
            return self.user_model.query.filter(self.user_model.id == self.session["user"]).first()  # type: ignore

    @property
    def url_deco(self) -> str:
        """Generates the disconnect address

        Returns
        -------
        str
            The global URL to disconnect the current user
        """
        return make_global_url("/deco/" + self.name)

    @property
    def session(self) -> dict[str, Any]:
        """Provides a convenient wrapper to the flask session for the provider

        Returns
        -------
        Dict[str, Any]
            the session dictionary
        """
        if "authprovider:" + str(self.name) not in flask_session.keys():
            flask_session["authprovider:" + str(self.name)] = {}

        return flask_session["authprovider:" + str(self.name)]


class AnonAuthProvider(AuthProvider):
    """A default anonymous user authentification provider"""

    __userBase__: type[User] | None = User

    @override
    def connect(self):  # type: ignore
        """Connect a user

        The user ID will respect the pattern <anon@XXX> where XXX is a random number
        """
        user_id = "anon@" + str(random.randint(1, 999999999999999))
        self._connect(self.user_model.create(id=user_id))  # type: ignore

    @override
    def validates_connection(self, condition: str | None = None) -> tuple[bool, str]:
        """Check if the user already validated the given condition

        Parameters
        ----------
        condition : str or None
            The optional condition to check to validate the connection

        Returns
        -------
        Tuple[bool, str]
            - True if the connection is validated, False if not
            - the checker name
        """

        if not (super().validates_connection("connected")[0]):
            self.connect()

        return super().validates_connection(condition)

    @override
    def disconnect(self):
        pass


class VirtualAuthProvider(AuthProvider):
    """A virtual user authentication provider.

    A virtual authentication provider is only used a place holder before the definition of the
    actual authentication provider.
    """

    __userBase__: type[User] | None = None

    def __init__(
        self,
        name: str | None = None,
        local_url_homepage: str = "/",
        userModel: User | None = None,
    ):
        """Initialisation method

        Parameters
        ----------
        name : str
            The name of the authentication scope
        local_url_homepage : str
            The local URL of the scope requiring the authentication
        user_model : User
            The user model
        """
        if name is None:
            super().__init__("none", local_url_homepage, userModel)
        else:
            super().__init__(name, local_url_homepage, userModel)

    def connect(self) -> None:
        """A virtual user can't connect,

        Raises
        ------
        NotConnectedError
           all the time, as you can't connect a virtual user
        """
        raise NotConnectedError()
