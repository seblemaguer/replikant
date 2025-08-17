# coding: utf8
# license : CeCILL-C

# Import Libraries
from replikant.core import ParticipantScope
from replikant.database import Model, Column, ForeignKey, db, declared_attr

user_model = ParticipantScope.get_user()


class Form(Model):
    __abstract__ = True

    id = Column(db.Integer, primary_key=True)

    @declared_attr
    def user_id(cls):
        return Column(db.String, ForeignKey(user_model.__tablename__ + ".id"), nullable=False, unique=True)
