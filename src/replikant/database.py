"""replikant.database
=================

This module provides the necessary classes to encapsulate the
interaction with the database.  Its implementation is mainly based on
the cookiebuffer-flask repository and especially from the following
class:
https://github.com/cookiecutter-flask/cookiecutter-flask/blob/master/%7B%7Bcookiecutter.app_name%7D%7D/%7B%7Bcookiecutter.app_name%7D%7D/database.py

"""

from typing import Self
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from sqlalchemy import text
from sqlalchemy.schema import CreateTable
from sqlalchemy.inspection import inspect
from sqlalchemy.ext.declarative import declared_attr
import pandas as pd
import threading
from .utils import AppSingleton

__all__ = [
    "declared_attr",
    "Column",
    "ForeignKey",
    "relationship",
    "commit_all",
    "DataBaseError",
    "MalformationError",
    "ForbiddenColumnName",
    "Model",
    "ModelFactory",
    "extract_dataframes",
]

# Instanciate database
db = SQLAlchemy()

sem = threading.Semaphore()

# Alias common SQLAlchemy names
Column = db.Column
ForeignKey = db.ForeignKey
relationship = db.relationship


# Helper's function
def commit_all():
    db.session.commit()


class DataBaseError(Exception):
    """Default exception class for database error

    Attributes
    ==========
      message: string
        The error message
    """

    def __init__(self, message):
        """Constructor which simply set the message of the exception

        Parameters
        ----------
        self: DataBaseError
            The current exception
        message: string
            The message of the exception
        """
        self.message = message


class ConstraintsError(DataBaseError):
    """Exception raised when a SQL constraint is violated"""

    pass


class MalformationError(DataBaseError):
    """Exception raised when a SQL query is malformed"""

    pass


class ForbiddenColumnName(DataBaseError):
    """Exception raised when the name given to the column to be created is
    forbidden (i.e. reserved SQL keywords)
    """

    pass


class Model(db.Model):
    """Base model class that includes CRUD convenience methods."""

    __abstract__ = True
    __tablename__: str | None = None

    @classmethod
    def addRelationship(cls, name, TargetClass, **kwargs):
        sem.acquire()
        if not (hasattr(cls, name)):
            setattr(cls, name, relationship(TargetClass.__name__, **kwargs))
        sem.release()

    @classmethod
    def addColumn(cls, name, col_type, *constraints):
        assert cls.__tablename__ is not None
        sem.acquire()
        if not (hasattr(cls, name)):
            column = Column(col_type, *constraints)
            setattr(cls, name, column)

            if not (name.replace("_", "").isalnum()):
                raise MalformationError(
                    "Col name:" + name + " is incorrect. Only alphanumeric's and '_' symbol caracteres are allowed."
                )

            if inspect(db.engine).has_table(cls.__tablename__):
                name_columns_in_table = [
                    col_in_table["name"] for col_in_table in inspect(db.engine).get_columns(cls.__tablename__)
                ]
                if name not in name_columns_in_table:
                    column_type = column.type.compile(db.engine.dialect)
                    with db.engine.begin() as conn:
                        conn.execute(text(f"ALTER TABLE '{cls.__tablename__}' ADD COLUMN {name} {column_type}"))

                    if len(constraints) > 0:
                        raise ConstraintsError(
                            f"Table {cls.__tablename__} already existing. "
                            + "Due to SQLite limitation, you can't add a constraint via "
                            + "ALTER TABLE ___ ADD COLUMN ___ ."
                        )
        else:
            column = getattr(cls, name)

        sem.release()
        return column

    def update(self, commit=True, **kwargs):
        """Update specific fields of a record."""
        for attr, value in kwargs.items():
            setattr(self, attr, value)
        return commit and self.save() or self

    def save(self, commit=True):
        """Save the record."""
        db.session.add(self)
        if commit:
            db.session.commit()
        return self

    def delete(self, commit=True):
        """Remove the record from the database."""
        db.session.delete(self)
        return commit and db.session.commit()

    @classmethod
    def create(cls, commit=True, **kwargs) -> Self:
        """Create a new record and save it the database."""
        instance = cls(**kwargs)
        return instance.save(commit=commit)


class ModelFactory(metaclass=AppSingleton):
    def __init__(self):
        self.register = {}

    def get(self, name_table, base):
        try:
            return self.register[base.__name__ + "_" + name_table]
        except Exception:
            return None

    def has(self, name_table, base):
        table_name = base.__name__ + "_" + name_table

        # Register already knows the table
        if table_name in self.register:
            return True

        sem.acquire()

        if inspect(db.engine).has_table(table_name):
            self.register[table_name] = type(
                table_name,
                (
                    base,
                    Model,
                ),
                {
                    "__tablename__": table_name,
                    "__table_args__": {
                        "extend_existing": True,
                        # "autoload": True,
                        "autoload_with": db.engine,
                    },
                },
            )
            sem.release()
            return True
        else:
            sem.release()
            return False

    def create(self, table_suffix, base, commit=True):
        table_name = base.__name__.replace("Model", "") + "_" + table_suffix

        sem.acquire()
        if not (table_name in self.register):
            if Model in base.__bases__:
                assert base.__abstract__

            if inspect(db.engine).has_table(table_name):
                self.register[table_name] = type(
                    table_name,
                    (
                        base,
                        Model,
                    ),
                    {
                        "__tablename__": table_name,
                        "__table_args__": {
                            "extend_existing": True,
                            # "autoload": True,
                            "autoload_with": db.engine,
                        },
                    },
                )
            else:
                self.register[table_name] = type(
                    table_name,
                    (
                        base,
                        Model,
                    ),
                    {
                        "__tablename__": table_name,
                        "__table_args__": {"extend_existing": True},
                    },
                )

        if commit:
            model_cls = self.register[table_name]
            if not (inspect(db.engine).has_table(model_cls.__tablename__)):
                model_cls.__table__.create(db.engine)
            table = model_cls
        else:
            table = self.register[table_name]

        sem.release()

        return table

    def commit(self, model_cls):
        """Commit the model to the database"""

        sem.acquire()
        if not (inspect(db.engine).has_table(model_cls.__tablename__)):
            model_cls.__table__.create(db.engine)
        sem.release()

        return model_cls


def extract_dataframes(names: list[str] | None = []) -> dict[str, pd.DataFrame]:
    """Extract the pandas DataFrame for each required (or all the available) tables in the database

    If the list of names is empty or none, all the tables are returned

    Parameters
    ----------
    names : list[str]|None
        the list of table names

    Returns
    -------
    dict[str, pd.DataFrame]
        A dictionnary associated a table name to its dataframe

    Raises
    ------
    Exception
        if at least one requested table does not exist in the database
    """
    #
    inspection = inspect(db.engine)
    all_table_names = inspection.get_table_names()
    if (not names) or (names is None):
        names = all_table_names
    else:
        diff_names = [element for element in names if element not in all_table_names]
        if diff_names:
            raise Exception(f"The elements {diff_names} are not known tables")

    dict_res = dict()
    for name_table in names:
        # Generate the dataframe corresponding to the table
        df = pd.read_sql_query(f"SELECT * FROM {name_table}", db.engine)
        dict_res[name_table] = df

    return dict_res


def export_schema() -> tuple[list[str], list[str]]:
    """Generate the SQL script to recreate and refill the database

    Returns
    -------
    str
        the content of the SQL script
    """
    metadata = MetaData()
    metadata.reflect(bind=db.engine)

    ddl_statements = []
    for table in metadata.sorted_tables:
        ddl = str(CreateTable(table).compile(bind=db.engine))
        ddl_statements.append(ddl + ";")

    dml_statements = []
    with db.engine.connect() as conn:
        for table in metadata.sorted_tables:
            result = conn.execute(table.select()).mappings().all()
            for row in result:
                values = {col.name: row[col.name] for col in table.columns}
                insert_sql = (
                    table.insert().values(**values).compile(bind=db.engine, compile_kwargs={"literal_binds": True})
                )
                dml_statements.append(str(insert_sql) + ";")

    return ddl_statements, dml_statements
