"""DeskPilot backend/API trust-boundary hardening primitives."""

from .authorization import ObjectAuthorizer, ObjectAccessDecision
from .rate_limit import TokenBucketLimiter, RateLimitDecision
from .ssrf import SsrfPolicy, SsrfViolation
from .tenant import TenantContext, TenantGuard

__all__ = [
    "ObjectAuthorizer",
    "ObjectAccessDecision",
    "TokenBucketLimiter",
    "RateLimitDecision",
    "SsrfPolicy",
    "SsrfViolation",
    "TenantContext",
    "TenantGuard",
]
