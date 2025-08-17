# coding: utf8
# license : CeCILL-C

from replikant.core.providers.auth import AuthProvider
from .model import InvitedParticipant


class UserAuthError(Exception):
    pass


class BadCredential(UserAuthError):
    pass


class UserAuth(AuthProvider):
    __userBase__ = InvitedParticipant

    def connect(self, token):
        assert self.user_model is not None
        assert isinstance(self.user_model, InvitedParticipant)
        user: InvitedParticipant | None = InvitedParticipant.query.filter(self.user_model.token == token).first()

        if user is None:
            raise BadCredential()
        else:
            super()._connect(user)
