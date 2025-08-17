from replikant.core.providers.auth import AuthProvider
from replikant.core.admin_scope import Administrator


class AdminAuthProvider(AuthProvider):
    def connect(self):
        super()._connect(Administrator())
