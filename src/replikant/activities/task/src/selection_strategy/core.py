import threading
import logging

from replikant.core import User
from ..system import System
from ...model import Sample

MUTEX_SELECTION = threading.Semaphore()


class SelectionBase:
    def __init__(
        self,
        systems: dict[str, System],
        references: list[str] = [],
        include_references: bool = False,
    ):
        self._systems = systems
        self._references = references
        self._include_reference = include_references
        self._logger = logging.getLogger(self.__class__.__name__)

    def select_samples(self, user: User, id_step: int, nb_systems: int, nb_samples: int) -> dict[str, list[Sample]]:
        """Select sample method

        This method is a wrapper on _select_samples to ensure an exclusive access to the critical section

        Parameters
        ----------
        user : User
            the user
        id_step: int
            The current step for the given participant
        nb_systems : int
            the number of systems
        nb_samples : int
            the number of samples

        Returns
        -------
        dict[str, list[SampleModel]]
            A dictionnary associating the sample to its ID

        """
        MUTEX_SELECTION.acquire()
        to_return = self._select_samples(user, id_step, nb_systems, nb_samples)
        MUTEX_SELECTION.release()

        return to_return

    def _select_samples(self, user: User, id_step: int, nb_systems: int, nb_samples: int) -> dict[str, list[Sample]]:
        """Select sample method

        This method should be overriden by the subclasses

        Parameters
        ----------
        user : User
            the user
        id_step: int
            The current step for the given participant
        nb_systems : int
            the number of systems
        nb_samples : int
            the number of samples

        Returns
        -------
        dict[str, list[SampleModel]]
            A dictionnary associating the sample to its ID

        """
        raise NotImplementedError(f'The class "{self.__class__.__name__}" should override the method "_select_samples"')

    @property
    def systems(self):
        return self._systems
