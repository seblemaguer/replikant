"""
replikant.core.providers.base
=============================

Module which provides the mechanics to deal with content (template, authentication, assets, ...) providers.
"""

import logging


class ProviderError(Exception):
    """Baseline exception class for any erroces caused by a provider."""

    pass


class UndefinedError(ProviderError):
    """Exception raised if the wanted provider is undefined

    Attributes
    ----------
    name_provider: string
        The name to which no provider is corresponding to.
    """

    def __init__(self, name_provider: str):
        super().__init__()
        self.name_provider = name_provider


class Provider:
    """Abstract provider class"""

    def __init__(self):  # type: ignore
        self._logger: logging.Logger = logging.getLogger(self.__class__.__name__)


class ProviderFactory:  # metaclass=AppSingleton):
    """Factory class to generate providers

    Attributes
    ----------
    _logger: Logger
        The internal logger
    providers: dict
        The dictionnary associating the provider name to its instance
    """

    def __init__(self):  # type: ignore
        """Constructor"""

        # Define logger
        self._logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self._providers: dict[str, Provider] = dict()

    def get(self, name: str) -> Provider:
        """Help to return a provider given its name

        Parameters
        ----------
        name : str
            the name of the provider

        Returns
        -------
        Provider
            the provider

        Raises
        ------
        UndefinedError
            if no provider corresponds to the given name
        """

        try:
            return self._providers[name]
        except Exception:
            raise UndefinedError(name)

    def exists(self, name: str) -> bool:
        """Determine if a provider associated to a given name exists

        Parameters
        ----------
        name : str
            The name of the provider

        Returns
        -------
        bool
            True if the provider exists, False else
        """

        return name in self._providers.keys()

    def set(self, name: str, provider: Provider) -> None:
        """Method to associate a given provider to a given name.

        If the given name already has a provider associated to it, this provider will be replaced.


        Parameters
        ----------
        name : str
            the name of the provider
        provider : Provider
            the provider to associate to the given name
        """

        if ProviderFactory().exists(name):
            oldprovider = ProviderFactory().get(name)
            old_name = oldprovider.__class__.__name__
            self._logger.debug(
                f'{old_name} is overwritten by {provider.__class__.__name__} for provider named "{name}".'
            )

        self._providers[name] = provider


# NOTE: create a single provider factory
provider_factory = ProviderFactory()
