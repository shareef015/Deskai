from collections.abc import Awaitable, Callable
from uuid import UUID, uuid4

from fastapi import Request, Response


async def request_context(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    supplied = request.headers.get("x-correlation-id")
    try:
        correlation_id = str(UUID(supplied)) if supplied else str(uuid4())
    except ValueError:
        correlation_id = str(uuid4())
    request.state.correlation_id = correlation_id
    response = await call_next(request)
    response.headers["x-correlation-id"] = correlation_id
    return response
