# coding: utf8
import csv

from flask import current_app

from replikant.utils import AppSingleton
from replikant.database import db, commit_all

from replikant.activities.task.model import Sample


class SystemError(Exception):
    def __init__(self, message: str):
        self.message = message


class SystemFileNotFound(SystemError):
    pass


class System:
    def __init__(self, name: str, data: str, delimiter: str = ",", max_samples: int = -1):
        self._samples: list[Sample] = []
        if name[0] == "/":
            name = name[1:]

        self.name = name
        source_file: str = current_app.config["REPLIKANT_RECIPE_DIR"] + "/systems/" + data

        try:
            reader = csv.DictReader(open(source_file, encoding="utf-8"), delimiter=delimiter)
        except Exception as e:
            raise SystemFileNotFound(f"{source_file} doesn't exist. Fix test.json or add the system's file: {e}")

        assert reader.fieldnames is not None
        self._col_names: list[str] = list(reader.fieldnames)

        # Dynamically create the columns needed to populate all the information related to the current sample
        for col_name in self._col_names:
            Sample.addColumn(col_name, db.String)

        if max_samples < 0:
            max_samples = len(list(csv.DictReader(open(source_file, encoding="utf-8"), delimiter=delimiter)))

        if len(self.samples) == 0:
            for line_id, line in enumerate(reader):
                if line_id >= max_samples:
                    break

                vars = {"system": self.name, "line_id": line_id}

                try:
                    for col_name in self._col_names:
                        vars[col_name] = line[col_name]
                    Sample.create(commit=False, **vars)

                except Exception as e:
                    raise SystemError(f'Issue to read the line {line_id} of the file "{source_file}": {e}')

            commit_all()

    @property
    def samples(self) -> list[Sample]:
        """Get the samples corresponding to the given system

        Returns
        -------
        list[Sample]
            the list of samples

        """

        # FIXME: this is a dirty hack as for now the Sample.__dict__ doesn't contain all the columns
        #        for now, it only returns <class 'sqlalchemy.engine.row.Row'> but not <Sample> object
        if len(self._samples) == 0:
            self._samples = (
                Sample.query.add_columns(Sample.__table__.columns)
                .filter(Sample.system == self.name)
                .order_by(Sample.line_id.asc())
                .all()
            )
            # samples = Sample.query.filter(Sample.system == self.name).order_by(Sample.line_id.asc()).all()

        return self._samples

    @property
    def col_names(self) -> list[str]:
        """Get the names of the columns that the system propose

        Returns
        -------
        list[str]
            the list of columns
        """
        return self._col_names.copy()


class SystemManager(metaclass=AppSingleton):
    def __init__(self):
        self.register: dict[str, System] = {}

    def insert(self, name: str, data: str, delimiter: str = ",", max_samples: int = -1):
        self.register[name] = System(name, data, delimiter, max_samples)
        return self.register[name]

    def get(self, name: str) -> System:
        return self.register[name]
