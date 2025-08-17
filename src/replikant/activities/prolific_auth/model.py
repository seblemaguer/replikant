# coding: utf8
# license : CeCILL-C

from replikant.core.participant_scope import Participant
from replikant.database import Column, db


class ProlificParticipant(Participant):
    user_id = Column(db.String, unique=True, nullable=False)
    study_id = Column(db.String, nullable=False)
    session_id = Column(db.String, nullable=False)

    def __init__(self, user_id: str, study_id: str, session_id: str):
        super().__init__()

        self.user_id = user_id

        # Get other fields
        self.study_id = study_id
        self.session_id = session_id
