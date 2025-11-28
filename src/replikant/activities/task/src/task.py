from typing import Any
from typing_extensions import override

# Global/system
from pathlib import Path
import string
import logging

# Data type
import mimetypes
import random
from datetime import datetime, timedelta
import hashlib
import shutil
from collections import OrderedDict

# Flask
from flask import current_app

# Replikant
from replikant.utils import AppSingleton
from replikant.core import ParticipantScope, User, Activity
from replikant.database import ModelFactory
from replikant.activities.task.model import TaskModel

# Current package
from .system import Sample, SystemManager, System
from .selection_strategy import SelectionBase, get_strategy


DEFAULT_CSV_DELIMITER: str = ","


class SampleModelInTransaction:
    def __init__(self, id: int, system_name: str, sample: Sample):
        """Initialisation

        Parameters
        ----------
        id : int
            the ID of the sample
        system_name : str
            The name of the system of the sample
        systemsample : object (FIXME: what is it exactly)
            No idea
        """
        self._logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self._system: System = SystemManager().get(sample.system)
        self._sample = sample
        self.system_name = system_name
        self._ID = id
        self._cache: dict[Path, tuple[str, str]] = dict()
        self._cached = True  # TODO: add as a configuration parameter

        if self._cached:
            # NOTE: under assets as the directory is, by default, visible
            self.CACHE_DIR = Path(current_app.config["REPLIKANT_RECIPE_DIR"] + "/assets/sample_cache/")
            self.CACHE_DIR.mkdir(parents=True, exist_ok=True)

    @property
    def ID(self):
        """Get the ID of the sample

        Returns
        -------
        int
            the ID of the sample

        """
        return self._ID

    def get(self, name: str) -> tuple[str | Path, str]:
        """Retrieve the value (file or string) and the mime type of the given column from the sample

        Parameters
        ----------
        name : str
            Name of the column (see the CSV/TSV file of the system)

        Returns
        -------
        tuple[str | Path, str]
            the value (file or string) and the corresponding mime type

        Raises
        ------
        Exception
            The column doesn't exist
        """

        # Retrieve the value and check the value exists
        mime = "text"
        value = getattr(self._sample, name)
        if value is None:
            raise Exception(f'The column "{name}" doesn\'t exist')

        if len(value) > 100:  # NOTE: 100 characters is a really long filename, so not valid!
            return (value, str(mime))

        # Infer a possible file path, and if not a file, just return the value
        file_path = value
        if not (file_path[0] == "/"):
            file_path = "/" + file_path

        cur_sample_path = Path(current_app.config["REPLIKANT_RECIPE_DIR"] + "/systems" + file_path)
        if not cur_sample_path.is_file():
            return (value, str(mime))

        # Load the cached file if available
        mime, _ = mimetypes.guess_type(cur_sample_path)
        if self._cached:
            if cur_sample_path not in self._cache:
                mime, _ = mimetypes.guess_type(cur_sample_path)
                mime = str(mime).split("/")[0]

                extension = cur_sample_path.suffix

                hashing = hashlib.md5()
                hashing.update(str(cur_sample_path).encode())
                cache_path = self.CACHE_DIR / (str(hashing.hexdigest()) + extension)
                shutil.copy(cur_sample_path, cache_path)

                cache_path = (
                    current_app.config["REPLIKANT_RECIPE_URL"]
                    + "/"
                    + str(cache_path.relative_to(current_app.config["REPLIKANT_RECIPE_DIR"]))
                )
                self._cache[cur_sample_path] = (cache_path, mime)
                cur_sample_path = cache_path
            else:
                cur_sample_path, mime = self._cache[cur_sample_path]

        return cur_sample_path, mime

    @override
    def __str__(self) -> str:
        return str(self.ID)


class TaskError(Exception):
    def __init__(self, message: str):
        self.message = message


class MalformationError(TaskError):
    pass


class TransactionalObject:
    """Wrapper class to deal with transactions to fill the database

    A transaction aims to store temporary information, associated to a given user, which is not yet complete and
    therefore can't be stored in the database. It is therefore used to ensure the passing of data between activities but
    also allows a better handling of recovering sessions.


    As part of a transaction, we also distinguish a "record". A record a specific property which requires a value filled
    as part of the task (i.e., by the participant, not the designer!)

    """

    RECORD_SEP: str = ":"

    def __init__(self, timeout_seconds: int = 3600):
        """Initialisation

        Parameters
        ----------
        time_out_seconds : int
            The timeout in seconds (default: 3600s)
        """
        self._transactions = {}
        self._timeout_seconds = timeout_seconds

    def set_timeout_for_transaction(self, timeout: int) -> None:
        """Setter of the timeout

        Parameters
        ----------
        timeout : int
            The timeout in seconds
        """

        self._timeout_seconds = timeout

    def delete_transaction(self, user: User) -> None:
        """Helper to delete the transactions of a given user

        Parameters
        ----------
        user : UserModel
            The given user
        """
        del self._transactions[user.id]

    def create_transaction(self, user: User) -> None:
        """Helper to create a transaction space for a given user

        Parameters
        ----------
        user : UserModel
            The given user
        """
        self._transactions[user.id] = {"date": datetime.now()}

    def get_transactions(self) -> list[dict[str, Any]]:
        """Retrieve the list of available transactions

        Available transactions are the ones which haven't been
        processed AND not yet timed out

        Returns
        -------
        list[dict[str, Any]]
            The list of transactions
        """

        transactions = []
        to_del = []

        # Retrieve all the transactions
        for user_id in self._transactions.keys():
            transaction = self._transactions[user_id]

            trans_date = transaction["date"] + timedelta(seconds=self._timeout_seconds)
            if (self._timeout_seconds is not None) and (trans_date < datetime.now()):
                to_del.append(user_id)
            else:
                transactions.append(transaction)

        # Drop the timed out transactions
        for transaction_key_to_del in to_del:
            del self._transactions[transaction_key_to_del]

        return transactions

    def has_transaction(self, user: User) -> bool:
        """Helper to know if a given user has some transactions waiting to be processed

        Parameters
        ----------
        user : UserModel
            The given user

        Returns
        -------
        bool
            True if the user has some transactions to be processed, False else
        """
        return user.id in self._transactions

    def get_transaction(self, user: User) -> dict[str, Any]:
        """Retrieve the transactions of a given user

        Should be called after checking if the user has some transactions to be processed

        Parameters
        ----------
        user : UserModel
            the given user

        Returns
        -------
        Dict[str, Any]
            the transactions of the given user
        """
        return self._transactions[user.id]

    def get_or_create_transaction(self, user: User) -> dict[str, Any]:
        if not self.has_transaction(user):
            self.create_transaction(user)
        return self.get_transaction(user)

    def set_in_transaction(self, user: User, name: str, obj: Any) -> None:
        self._transactions[user.id][name] = obj

    def get_in_transaction(self, user: User, name: str) -> Any:
        if name not in self._transactions[user.id]:
            return None
        else:
            return self._transactions[user.id][name]

    def create_row_in_transaction(self, user: User) -> str:
        ID = "".join((random.choice(string.ascii_lowercase) for _ in range(20)))

        # Row not created, just create it
        if not (ID in self._transactions[user.id].keys()):
            self._transactions[user.id][ID] = None

        # Returns the ID of the row
        return ID

    def create_new_record(self, user: User, name: str | None = None) -> str:
        # Dictionary "record name" -> list of field names
        user_transaction = self.get_or_create_transaction(user)
        all_records = user_transaction.setdefault("records", OrderedDict())

        if name is None:
            name = "record" + str(abs(hash("record" + str(len(all_records)))) % int(1e9))

        # Ensure valid record_name
        name = name.replace(TransactionalObject.RECORD_SEP, "_")
        return name

    def add_field_to_record(self, user: User, field_name: str, record_name: str | None = None) -> str:
        # Retrieve the record (create it if necessary)
        user_transaction = self.get_or_create_transaction(user)
        all_records = user_transaction.setdefault("records", dict())
        if len(all_records) == 0:
            record_name = self.create_new_record(user, name=record_name)
        elif record_name is None:
            record_name = next(reversed(all_records))

        # Ensure record name to be usable (FIXME: underscore may not be the best idea...)
        record_name = record_name.replace(TransactionalObject.RECORD_SEP, "_")
        current_fields = self.get_fields_for_record(user, record_name)
        if field_name not in current_fields:
            current_fields.append(field_name)

        return record_name

    def get_all_records(self, user: User):
        user_transaction = self.get_or_create_transaction(user)
        all_records = user_transaction.setdefault("records", OrderedDict())
        return all_records

    def get_record(self, user: User, name: str | None = None) -> str:
        all_records = self.get_all_records(user)

        # No records, let's just create one directly
        if len(all_records) == 0:
            return self.create_new_record(user, name=name)

        if name is None:
            return next(reversed(all_records))
        elif name in all_records:
            return name
        else:
            return self.create_new_record(user, name=name)

    def get_fields_for_record(self, user: User, record_name: str):
        user_transaction = self.get_or_create_transaction(user)
        all_records = user_transaction.setdefault("records", OrderedDict())
        current_fields = all_records.setdefault(record_name, list())
        return current_fields


class Task(TransactionalObject):
    def __init__(self, name: str, config) -> None:
        """Constructor

        Parameters
        ----------
        name: str
            The name of the section
        config: ????
            The configuration of the task

        """
        super().__init__()

        self.name = name
        self._logger = logging.getLogger(f"{__name__} ({self.name})")

        # Load systems
        self.systems = {}
        for cur_system in config["systems"]:
            delimiter = DEFAULT_CSV_DELIMITER
            if "delimiter" in cur_system:
                delimiter = cur_system["delimiter"]

            max_samples = -1
            if "max_samples" in cur_system:
                max_samples = int(cur_system["max_samples"])

            self.systems[cur_system["name"]] = SystemManager().insert(
                cur_system["name"], cur_system["data"], delimiter, max_samples
            )

        # Create Task table in the database
        self.model = ModelFactory().create(self.name, TaskModel, commit=True)
        ParticipantScope.get_user().addRelationship(self.model.__name__, self.model, uselist=True)

        # Initialize the sample selection strategy
        selection_strategy_name = "LeastSeenSelection"
        if "selection_strategy" in config:
            selection_strategy_name = config["selection_strategy"]
            # kwargs = dict()
            if not isinstance(selection_strategy_name, str):
                # kwargs = selection_strategy_name["kwargs"]
                selection_strategy_name = selection_strategy_name["name"]

            # in case we describe
            self._logger.info(f'The selection strategy is user defined to "{selection_strategy_name}"')
        else:
            self._logger.info('The selection strategy is defaulted to "LeastSeenSelection"')

        self._selection_strategy: SelectionBase = get_strategy(selection_strategy_name, self.systems)

    def nb_steps_complete_by(self, user: User) -> int:
        """Get the number of steps completed by a given user

        Parameters
        ----------
        user: UserModel
           The scrutinized user

        Returns
        -------
        int
            The number of steps completed by the user
        """
        all_steps = set()
        for record in getattr(user, self.model.__name__):
            if record.operation_type == "record":
                all_steps.add(record.step_idx)
        return max(all_steps) + 1 if all_steps else 0

    def get_step(
        self, id_step: int, user: User, nb_systems: int, is_intro_step: bool = False
    ) -> dict[str, SampleModelInTransaction]:
        """Get the samples needed for one step of the task

        Parameters
        ----------
        id_step: int
            The index of the step
        user: UserModel
            The model of the participant to the step
        nb_systems: int
            The number of system wanted for the current step
        is_intro_step: bool
            Flag to indicate if the current step is an introduction step or not

        Returns
        -------
        Dict[str, SampleModelTemplate]
            The dictionnary associating which each system (name) the sample used
        """

        # Resume the task, if a transaction hasn't been finalised
        choice_for_systems = dict()
        if self.has_transaction(user):
            return self.get_in_transaction(user, "choice_for_systems")

        # Select samples (FIXME: 1 is hardcoded here)
        selected_samples = self._selection_strategy.select_samples(user, id_step, nb_systems, 1)
        for system_name, samples in selected_samples.items():
            choice_for_systems[system_name] = samples[0]

        # Now we are ready to create the transaction
        self.create_transaction(user)

        # For each system, select the samples
        for system_name in choice_for_systems.keys():
            syssample = choice_for_systems[system_name]
            id_in_transaction = self.create_row_in_transaction(user)
            self.set_in_transaction(user, id_in_transaction, (system_name, syssample.id))
            choice_for_systems[system_name] = SampleModelInTransaction(id_in_transaction, system_name, syssample)

        # Define if it is an introduction step
        self.set_in_transaction(user, "intro_step", is_intro_step)

        # Set the systems/samples information
        self.set_in_transaction(user, "choice_for_systems", choice_for_systems)

        # Validate everything
        return choice_for_systems


class TaskManager(metaclass=AppSingleton):
    """Helper to manage the tasks.

    This class is a singleton and should not be accessed directly.
    The user should use task_manager which is the variable dedicated for the management
    """

    def __init__(self):
        """Initialisation which simply setup the register"""

        self._register: dict[str, Task] = dict()

    def register(self, name: str, activity_config: Activity, force: bool = False) -> Task:
        """Register a task

        This method uses the configuration to instanciate a Task
        object and then add it to the register dictionary

        Parameters
        ----------
        name : str
            the name of the task
        activity_config : Stage
            The Stage object required to instantiate the task

        Returns
        -------
        Task
            The instance of the newly created task

        """
        if (name in self._register) and (not force):
            raise Exception(f"Trying to register the task {name} a second time")

        self._register[name] = Task(name, activity_config)
        return self._register[name]

    def has(self, name: str) -> bool:
        """Check if the task "name" has been registered

        Parameters
        ----------
        name : str
            the name of the task

        Returns
        -------
        bool
            True if it has been registered, False else

        """
        return name in self._register

    def get(self, name: str) -> Task:
        """Get the task given its name

        Parameters
        ----------
        name : str
            the name of the task

        Returns
        -------
        Task
            the instance of the task

        Raises
        ------
        KeyError
            if the task has not been registered and therefore doesn't
            exist
        """
        if name not in self._register:
            raise KeyError(f"the task {name} has not been registered, check your configuration file")

        return self._register[name]

    def list_tasks(
        self,
    ) -> list[Task]:
        return [t for _, t in self._register.items()]


task_manager = TaskManager()
