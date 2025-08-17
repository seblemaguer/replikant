from typing import Any
import numpy as np
import math
import random

from replikant.core import User
from ...model import Sample
from ..system import System
from .core import SelectionBase


class LeastSeenSelection(SelectionBase):
    """Class implementing the selection strategy based on the "least seen" paradigm:
     1. list the least seen system(s)
     2. for the the least system(s), select the least seen sample(s)

    Everything is then randomized and *NO ORDER* is ensured.
    """

    def __init__(self, systems: dict[str, System]) -> None:
        """Constructor

        Parameters
        ----------
        systems: dict[str, System]
            The dictionnary of systems indexed by their names
        """
        super().__init__(systems)

        # Initialize content elements
        self._samples = [sample.id for _, cur_system in systems.items() for sample in cur_system.samples]

        # Initialize counters
        self._system_counters: dict[str, int] = dict([(cur_system, 0) for cur_system in systems.keys()])
        self._sample_counters: dict[Any, int] = dict([(cur_sample, 0) for cur_sample in self._samples])

    def select_systems(self, nb_systems: int) -> list[str]:
        """Select a certain amount systems among the least seen ones

        Parameters
        ----------
        nb_systems: int
            The desired number of systems for one step

        Returns
        -------
        list[str]
            the list of names of the selected systems
        """

        # Sort systems by descending order of usage
        pool_systems = sorted(self._system_counters.items(), key=lambda item: item[1])

        # Assert/Fix the number of required systems
        assert (nb_systems <= len(pool_systems)) and (nb_systems != 0), (
            f"The required number of systems ({nb_systems}) is greater than the available number of systems "
            + f"({len(pool_systems)}) or it is 0"
        )

        # Preparing pool of systems
        if nb_systems > 0:
            min_count = math.inf
            tmp_pool = []
            for system, count in pool_systems:
                if count > min_count:
                    break

                tmp_pool.append((system, count))
                min_count = count

            pool_systems = tmp_pool

        # Ignore the counting from now, we are only interested with the systems themselves
        pool_systems = [system[0] for system in pool_systems]

        # Shuffle the systems to guarantee variation in the presentation order
        random.shuffle(pool_systems)

        # Select the desired number of systems
        pool_systems = pool_systems[:nb_systems]
        for p in pool_systems:
            self._system_counters[p] += 1

        return pool_systems

    def internal_select_samples(self, system_name: str, nb_samples: int) -> list[Sample]:
        """Select a given number of samples of a given system

        Parameters
        ----------
        system_name: str
           The name of the system
        nb_samples: int
           The desired number of sample

        Returns
        -------
        list[Sample]
            The list of selected samples
        """
        # Subset the list of samples
        dict_samples = dict([(sample.id, sample) for sample in self.systems[system_name].samples])
        sample_subset = {sample_id: self._sample_counters[sample_id] for sample_id in dict_samples.keys()}

        # Sort by counting the pool of samples
        pool_samples = sorted(sample_subset.items(), key=lambda item: item[1])

        # Assert/Fix the number of required samples
        assert (nb_samples <= len(pool_samples)) and (nb_samples != 0), (
            f"The required number of samples ({nb_samples}) is greater than the available number of samples "
            + f"({len(pool_samples)}) or it is 0"
        )

        # Preparing pool of samples
        if nb_samples > 0:
            min_count = math.inf  # NOTE: Infinite is hardcoded here!
            tmp_pool = []
            for sample, count in pool_samples:
                if count > min_count:
                    break

                tmp_pool.append((sample, count))
                min_count = count

            pool_samples = tmp_pool

        # Ignore the counting from now, we are only interested with the samples themselves
        pool_samples = [sample[0] for sample in pool_samples]

        # Shuffle the samples to guarantee variation in the presentation order
        random.shuffle(pool_samples)

        # Select the desired number of samples
        pool_samples = pool_samples[:nb_samples]
        for p in pool_samples:
            self._sample_counters[p] += 1

        return [dict_samples[sample_id] for sample_id in pool_samples]

    def _select_samples(self, user: User, id_step: int, nb_systems: int, nb_samples: int) -> dict[str, list[Sample]]:
        """Method to select a given number of samples for a given number of systems for a specific user

        The selection strategy is twofold:
           1. select the desired number of least systems
           2. for each selected system, select the least seen samples (the desired number of samples for each system)

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
        dict[str, list[Sample]]
            The dictionary providing for a system name the associated sample embedded in a list
        """

        # Select the systems
        self._logger.debug(f"Select systems for user {user.user_id}")
        pool_systems = self.select_systems(nb_systems)
        self._logger.debug(f"Current state of the current system counters: {self._system_counters}")

        # Select the samples
        self._logger.debug(f"Select samples for user {user.user_id}")
        dict_samples = dict()
        for system_name in pool_systems:
            dict_samples[system_name] = self.internal_select_samples(system_name, nb_samples)

        self._logger.info(f"This is what we will give to {user.id}: {dict_samples}")

        return dict_samples


class LeastSeenSampleAlignedSelection(LeastSeenSelection):
    """Select the same "sample" for each wanted systems

     This strategy consists of selecting:
       1. list the least seen system(s)
       2. for the the least system(s), select the least seen sample(s)

    The order will be randomized but
    """

    def __init__(self, systems: dict[str, System]) -> None:
        """Constructor

        Parameters
        ----------
        systems: dict[str, System]
            The dictionnary of systems indexed by their names
        """
        super().__init__(systems)

        system_name = list(systems.keys())[0]
        nb_systems = len(self.systems[system_name].samples)
        self._sample_counters = [0 for _ in range(nb_systems)]

    def _select_samples(self, user: User, id_step: int, nb_systems: int, nb_samples: int) -> dict[str, list[Sample]]:
        """Method to select a given number of samples for a given number of systems for a specific user

        The selection strategy is twofold:
           1. select the desired number of least systems
           2. for each selected system, select the least seen samples (the desired number of samples for each system)

        Parameters
        ----------
        user: User
            The participant
        id_step: int
            The current step for the given participant
        nb_systems: int
            The desired number of systems
        nb_samples: int
            This is ignored as it should be 1 sample per system

        Returns
        -------
        dict[str, list[Sample]]
            The dictionary providing for a system name the associated sample embedded in a list
        """

        # Select the systems
        self._logger.debug(f"Select systems for user {user.user_id}")
        pool_systems = self.select_systems(nb_systems)
        self._logger.debug(f"Current state of the current system counters: {self._system_counters}")

        # Select the samples
        self._logger.debug(f"Select samples for user {user.user_id}")

        min_value = min(self._sample_counters)
        min_indices = [i for i, value in enumerate(self._sample_counters) if value == min_value]
        random.shuffle(min_indices)
        min_index = min_indices[0]
        self._sample_counters[min_index] += 1

        dict_samples = dict()
        for system_name in pool_systems:
            dict_samples[system_name] = [self.systems[system_name].samples[min_index]]

        self._logger.info(f"This is what we will give to {user.user_id}: {dict_samples}")

        return dict_samples


class LeastSeenPerUserSelection(LeastSeenSelection):
    """Class implementing the selection strategy based on the "least seen" (user focused) paradigm:
    1. list the least seen system(s)
    2. for the the least system(s), select the least seen sample(s)
    """

    def __init__(self, systems: dict[str, System]) -> None:
        """Constructor

        Parameters
        ----------
        systems: dict[str, System]
            The dictionnary of systems indexed by their names
        """
        super().__init__(systems)

        self._user_history = dict()

    def select_user_systems(self, user_history: dict[str, list[str]], nb_systems: int) -> list[str]:
        # Get the list of available systems sorted in ascending order
        system_count_list = [(sys_name, len(seen_samples)) for sys_name, seen_samples in user_history.items()]
        system_count_list.sort(key=lambda x: x[1])

        # Get the cutting edge
        cut_idx = 1
        start_count = system_count_list[0][1]
        for cut_idx, cur_elt in enumerate(system_count_list[1:], 1):
            if cur_elt[1] != start_count:
                break

        # Subset and shuffle
        if cut_idx < nb_systems:
            pool_systems = system_count_list[:nb_systems]
        else:
            pool_systems = system_count_list[:cut_idx]
        random.shuffle(pool_systems)

        return pool_systems[:nb_systems]

    def user_select_samples(self, user_history: list[str], system_name: str, nb_samples: int) -> list[Sample]:
        """Select a given number of samples of a given system

        Parameters
        ----------
        system_name: str
           The name of the system
        nb_samples: int
           The desired number of sample

        Returns
        -------
        list[Sample]
            The list of selected samples
        """
        # Subset the list of samples
        dict_samples = dict([(sample.id, sample) for sample in self.systems[system_name].samples])
        sample_subset = {
            sample_id: self._sample_counters[sample_id]
            for sample_id in dict_samples.keys()
            if sample_id not in user_history
        }

        # Sort by counting the pool of samples
        pool_samples = sorted(sample_subset.items(), key=lambda item: item[1])

        # Assert/Fix the number of required samples
        self._logger.debug(f"Number of samples {nb_samples} from a pool of {len(pool_samples)} samples is required")
        if nb_samples > len(pool_samples):
            self._logger.error(f"This should not happen but here is the history for info: {user_history}")
            return [dict_samples[sample] for sample in user_history[-nb_samples:]]
        else:
            assert (nb_samples <= len(pool_samples)) and (nb_samples > 0), (
                f"The required number of samples ({nb_samples}) is greater "
                + f"than the available number of samples {len(pool_samples)} or it is 0"
            )

        # Subset to get the desired number of samples and shuffle to guarantee variation in the presentation order
        # NOTE: to ensure variability, we first need to take into account the pool of samples seens
        #       the same amount of time
        nb_id_samples = 0
        for nb_id_samples in range(1, len(pool_samples)):
            if pool_samples[nb_id_samples - 1][1] != pool_samples[nb_id_samples][1]:
                break

        if nb_id_samples > nb_samples:
            pool_samples = pool_samples[:nb_id_samples]
            random.shuffle(pool_samples)
            pool_samples = pool_samples[:nb_samples]
        else:
            pool_samples = pool_samples[:nb_samples]
            random.shuffle(pool_samples)

        # Select the desired number of samples
        for sample in pool_samples:
            self._sample_counters[sample[0]] += 1
            user_history.append(sample[0])

        return [dict_samples[sample[0]] for sample in pool_samples]

    def _select_samples(self, user: User, id_step: int, nb_systems: int, nb_samples: int) -> dict[str, list[Sample]]:
        """Method to select a given number of samples for a given number of systems for a specific user

        The selection strategy is twofold:
           1. select the desired number of least systems
           2. for each selected system, select the least seen samples (the desired number of samples for each system)

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
        dict[str, list[Sample]]
            The dictionary providing for a system name the associated sample embedded in a list
        """

        if user.id not in self._user_history:
            self._user_history[user.id] = dict([(cur_system, list()) for cur_system in self.systems.keys()])
        self._logger.debug(f"History status of the current user: {self._user_history[user.id]}")

        # Select the systems
        self._logger.debug(f"Select systems for user {user.user_id}")
        pool_systems = self.select_user_systems(self._user_history[user.id], nb_systems)

        # Select the samples
        self._logger.debug(f"Select samples for user {user.user_id}")
        dict_samples = dict()
        for system_name in pool_systems:
            dict_samples[system_name] = self.user_select_samples(
                self._user_history[user.id][system_name], system_name, nb_samples
            )

        self._logger.info(f"This is what we will give to {user.user_id}: {dict_samples}")

        return dict_samples


class LeastSeenMixedSelection(LeastSeenSelection):
    """ """

    def __init__(self, systems: dict[str, System]) -> None:
        """Constructor

        Parameters
        ----------
        systems: dict[str, System]
            The dictionnary of systems indexed by their names
        """
        super().__init__(systems)

        # Just make sure that all the systems have the same utterances (just count check!)
        self._nb_utts = 0
        for sys_name, sys in systems.items():
            if self._nb_utts == 0:
                self._nb_utts = len(sys.samples)
            elif len(sys.samples) != self._nb_utts:
                raise Exception(
                    "For this strategy all the systems should have the same utterance aligned in the same order, "
                    + f"{sys_name} seems to be different"
                )
            else:
                self._nb_utts = len(sys.samples)

        self._system_names = list(systems.keys())
        self._counters = np.zeros((len(self._system_names), self._nb_utts)).astype(int)
        self._user_counters = dict()
        self._user_history = dict()

    def _select_samples(self, user: User, id_step: int, nb_systems: int, nb_samples: int) -> dict[str, list[Sample]]:
        """Method to select a given number of samples for a given number of systems for a specific user

        The selection strategy is twofold:
           1. select the desired number of least systems
           2. for each selected system, select the least seen samples (the desired number of samples for each system)

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
        dict[str, list[Sample]]
            The dictionary providing for a system name the associated sample embedded in a list
        """

        assert (nb_systems == 1) & (
            nb_samples == 1
        ), f"Only 1 sample (not {nb_samples}) for 1 system (not {nb_systems}) is supported for this selection mode"

        # Retrieve user history
        if user.id not in self._user_counters:
            # self._user_history[user.id] = dict([(cur_system, list()) for cur_system in self.systems.keys()])
            self._user_history[user.id] = []
            self._user_counters[user.id] = np.zeros((len(self._systems), self._nb_utts)).astype(int)
        user_counters = self._user_counters[user.id]

        # Prepare some helpers to refine the filtering
        system_counters = np.sum(user_counters, axis=1)
        pool_systems = np.where(system_counters == system_counters.min())[0].astype(int)
        utt_counters = np.sum(user_counters, axis=0)
        pool_utts = np.where(utt_counters == utt_counters.min())[0].astype(int)

        # First get the minimal seen information (=> generate overall mask)
        min_overall_counters = np.min(self._counters)
        overall_mask = np.argwhere(self._counters == min_overall_counters)

        # Generate the user mask
        mask = np.argwhere(user_counters == np.min(user_counters))
        subset_cells = np.isin(mask[:, 0], pool_systems) & np.isin(mask[:, 1], pool_utts)
        mask = mask[subset_cells, :]

        # Apply user mask to overall mask
        subset_cells = np.isin(overall_mask[:, 0], mask[:, 0]) & np.isin(overall_mask[:, 1], mask[:, 1])
        overall_mask = overall_mask[subset_cells, :]
        if overall_mask.shape[0] != 0:
            mask = overall_mask

        # No luck up to now, just select a random samples, but put a priority on the system
        if mask.shape[0] == 0:
            mask = np.argwhere(user_counters == np.min(user_counters))
            subset_cells = np.isin(mask[:, 0], pool_systems)
            mask = mask[subset_cells, :]

        # NOTE: for debug
        if mask.shape[0] == 0:
            self._logger.warning(f"[{user.id}] For whatever reason, we don't have any available slot")
            self._logger.warning(f"[{user.id}] Here is the user counter status:\n")
            self._logger.warning(f"{user_counters}")
            self._logger.warning(f"[{user.id}] Here is the the overall counter:\n")
            self._logger.warning(f"{self._counters}")
            raise Exception("This make no sense")

        np.random.shuffle(mask)
        mask = mask[0]

        # Update counters
        user_counters[mask[0], mask[1]] += 1
        self._counters[mask[0], mask[1]] += 1

        # And now get the samples
        pool_samples = [self.systems[self._system_names[mask[0]]].samples[mask[1]]]
        dict_samples = dict()
        for sample in pool_samples:
            if sample.system not in dict_samples:
                dict_samples[sample.system] = []
            dict_samples[sample.system].append(sample)
            self._user_history[user.id].append(sample.id)

        self._logger.info(f"This is what we will give to {user.user_id}: {dict_samples}")

        # self._logger.warning(f"[{user.id}] History status: {self._user_history[user.id]}")
        self._logger.debug(f"[{user.id}] Utt history status:\n {self._user_counters[user.id]}")
        self._logger.debug(f"[=] Utt history status:\n {self._counters}\n")

        return dict_samples
