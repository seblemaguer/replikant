# coding: utf8
# license : CeCILL-C


from .error import error_handler
from .config import Config
from .scope import Scope
from .core import Campaign, campaign_instance
from .participant_scope import ParticipantScope, Activity
from .admin_scope import AdminScope

from .providers.auth import AuthProvider, User, VirtualAuthProvider

__all__ = [
    "Config",
    "Scope",
    "ParticipantScope",
    "Activity",
    "AdminScope",
    "AuthProvider",
    "User",
    "VirtualAuthProvider",
    "error_handler",
    "Campaign",
    "campaign_instance",
]
