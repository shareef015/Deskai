"""OIDC authentication and immutable request identity."""

from .claims import AuthenticatedPrincipal
from .dependencies import require_principal

__all__ = ["AuthenticatedPrincipal", "require_principal"]
