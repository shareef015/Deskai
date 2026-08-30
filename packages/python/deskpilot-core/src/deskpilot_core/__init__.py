"""Runtime-neutral primitives shared by DeskPilot services."""

from .clock import Clock, SystemClock
from .configuration import ConfigurationError, RuntimeConfiguration, load_configuration
from .identifiers import CorrelationId, new_correlation_id
from .errors import DeskPilotError, ErrorCode, problem_document, unexpected_problem
from .result import Result
from .secrets import (
    EnvironmentSecretProvider,
    FileSecretProvider,
    RotationMetadata,
    SecretReference,
    SecretResolutionError,
    SecretResolver,
    SecretValue,
)
from .structured_logging import (
    JsonLogFormatter,
    LogContext,
    LoggingContractError,
    build_log_event,
    emit,
    redact,
    tenant_log_key,
)

__all__ = [
    "Clock", "ConfigurationError", "CorrelationId", "Result", "RuntimeConfiguration",
    "DeskPilotError", "ErrorCode", "problem_document", "unexpected_problem",
    "EnvironmentSecretProvider", "FileSecretProvider", "RotationMetadata",
    "SecretReference", "SecretResolutionError", "SecretResolver", "SecretValue",
    "JsonLogFormatter", "LogContext", "LoggingContractError", "build_log_event",
    "emit", "redact", "tenant_log_key",
    "SystemClock", "load_configuration", "new_correlation_id",
]
