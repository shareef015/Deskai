from typing import NewType
from uuid import uuid4


CorrelationId = NewType("CorrelationId", str)


def new_correlation_id() -> CorrelationId:
    return CorrelationId(str(uuid4()))
