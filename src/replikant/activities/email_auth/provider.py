# Python
from replikant.core.providers.auth import AuthProvider
from .model import EmailParticipant


class EmailAuthProvider(AuthProvider):
    __userBase__ = EmailParticipant

    def connect(self, email: str):  # type: ignore
        assert self.user_model is not None
        user: EmailParticipant | None = EmailParticipant.query.filter(self.user_model.email == email).first()

        if user is None:
            user = EmailParticipant.create(email=email)

        super()._connect(user)
