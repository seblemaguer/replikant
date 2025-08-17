from replikant.core.participant_scope import Participant
from replikant.database import Column, db

import re


class NotAnEmail(Exception):
    def __init__(self, email: str):
        super().__init__()
        self.email = email


EMAIL_REGEX = re.compile(r"^([\w\.\-]+)@([\w\-]+)((\.([\w-]){2,63}){1,3})$")


class EmailParticipant(Participant):
    email = Column(db.String, unique=True, nullable=False)

    def __init__(self, email: str):
        super().__init__()

        # Validate email
        if not re.fullmatch(EMAIL_REGEX, email):
            raise NotAnEmail(email)

        # Set the email as the ID
        self.email = email

    @property
    def user_id(self) -> str:
        return f"{self.email}"
