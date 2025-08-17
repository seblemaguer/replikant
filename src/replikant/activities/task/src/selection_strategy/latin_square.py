import numpy as np

from replikant.core import User
from ...model import Sample
from ..system import System
from .core import SelectionBase


def williams_latin_square(n: int) -> np.array:
    """Helper to generate a latin square using the William's design strategy

    Parameters
    ----------
    n : int
        the size of the square

    Returns
    -------
    np.array
        the generated latin square

    Raises
    ------
    ValueError
        if n is below 2 which makes no sense
    """
    if n < 2:
        raise ValueError("n must be at least 2")

    square = np.zeros((n, n), dtype=int)

    # Generate the numeric Latin square
    for i in range(n):
        for j in range(n):
            if j % 2 == 0:
                square[i, j] = (i + j // 2) % n
            else:
                square[i, j] = (n + i - (j + 1) // 2) % n

    return square


class LatinSquareSelection(SelectionBase):
    """Class implementing the selection strategy based on the Latin Square paradigm"""

    def __init__(self, systems: dict[str, System], randomize: bool = False) -> None:
        """Constructor

        Parameters
        ----------
        systems: dict[str, System]
            The dictionnary of systems indexed by their names
        randomize: bool
            Flag to determine if a randomization should be done on top of the LS selection [default: False]
        """
        super().__init__(systems)

        # Prepare the core
        list_systems = list(systems.keys())

        self._samples = [None] * (len(list_systems) ** 2)
        # self._samples = [sample.id for _, cur_system in systems.items() for sample in cur_system[0].system_samples]

        # Compute the latin square using the William's design
        square = williams_latin_square(len(list_systems))
        self._logger.debug(f"Generating latin square of shape {square.shape}")

        # Generate the groups
        self._groups = np.zeros(square.shape).astype(int)
        for seq_idx in range(square.shape[0]):
            for sample_idx in range(square.shape[1]):
                system_idx = square[seq_idx][sample_idx]
                self._logger.debug(
                    f"Number of samples for system {systems[list_systems[system_idx]][0]} => "
                    + f"{len(systems[list_systems[system_idx]][0].system_samples)} [{len(self._samples)}]"
                )
                sample = systems[list_systems[system_idx]][0].system_samples[sample_idx]
                self._groups[seq_idx][sample_idx] = sample.id - 1
                self._samples[sample.id - 1] = sample

        self._logger.debug(f"The square obtain for {len(list_systems)} systems:\n{self._groups}")

        if randomize:
            for seq_idx in range(square.shape[0]):
                np.random.shuffle(self._groups[seq_idx])
            self._logger.debug(f"Randomization required, new square:\n{self._groups}")

    def _select_samples(self, user: User, id_step: int, nb_systems: int, nb_samples: int) -> dict[str, list[Sample]]:
        """Method to select the samples using the Latin Square strategy.

        For now, only one system & one sample is supported

        Parameters
        ----------
        user: User
            The participant
        id_step: int
            The current step for the given participant
        nb_systems: int
            The desired number of systems
        nb_samples: int
            The desired number of samples

        Returns
        -------
        dict[str, list[SampleModel]]
            The dictionary providing for a system name the associated sample embedded in a list

        Raises
        ------
        AssertError
             if nb_systems or nb_samples are different from 1
        """

        assert nb_systems == 1, f"For the latin-square algorithm, we can only select one system, {nb_systems} are asked"
        assert nb_samples == 1, f"For the latin-square algorithm, we can only select one sample, {nb_samples} are asked"

        # Get the user group
        user_group = user.id % self._groups.shape[0]
        self._logger.debug(f"{user.id} has the user group {user_group}")

        # Get the samples now
        sample_idx = id_step % self._groups.shape[1]
        sample = self._samples[self._groups[user_group][sample_idx]]

        # Select the samples
        self._logger.debug(f"Select samples for user {user.user_id}")
        dict_samples = dict()
        dict_samples[sample.system] = [sample]

        self._logger.info(f"This is what we will give to {user.user_id}: {dict_samples}")

        return dict_samples
