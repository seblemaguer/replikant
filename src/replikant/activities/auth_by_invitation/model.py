import random
import string

from replikant.core.participant_scope import Participant
from replikant.database import Column, db


class InvitedParticipant(Participant):
    token = Column(db.String, unique=True, nullable=False)
    active = Column(db.Boolean, nullable=False)
    LEN_TOKEN = 20

    def __init__(self, email: str):
        super().__init__()
        self.id = email
        self.token = "".join((random.choice(string.ascii_lowercase) for _ in range(InvitedParticipant.LEN_TOKEN)))
        self.active = False
