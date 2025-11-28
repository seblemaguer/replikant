# coding: utf8
from datetime import datetime

from replikant.database import Model, Column, ForeignKey, db, declared_attr
from replikant.core import ParticipantScope

usermodel = ParticipantScope.get_user()


class Sample(Model):
    """Model which represent a sample

    A sample is identified by an \"id\" and is associated to a \"system\"
    """

    __tablename__ = "Sample"

    id = Column(db.Integer, primary_key=True)
    system = Column(db.String, nullable=False)
    line_id = Column(db.Integer, nullable=False)

    def __str__(self) -> str:
        return str(self.__dict__)


class TaskModel(Model):
    """Model which represents a test.

    A test is composed by different steps and each row of the table corresponds to one of these steps.

    A step is identified by an \"id\", has a \"date\" when it was created, and index (\"step_idx\") and a flag
    indicating if it is an introduction step (\"intro\")
    """

    __abstract__ = True

    id = Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False)
    step_idx = db.Column(db.Integer, nullable=False)
    intro = db.Column(db.Boolean, nullable=False)
    sample_id = db.Column(db.Integer, ForeignKey(Sample.__tablename__ + ".id"), nullable=False)
    info_type = db.Column(db.String, nullable=False)
    info_value = db.Column(db.String, nullable=False)
    operation_type = db.Column(db.String, nullable=False)

    def __init__(self, *args, **kwargs):
        self.intro = False
        super().__init__(*args, **kwargs)
        self.date = datetime.now()

    @declared_attr
    def user_id(cls):
        return Column(db.String, ForeignKey(usermodel.__tablename__ + ".id"))
