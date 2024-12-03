from typing import Any, Awaitable, Callable, Iterable

type HandlerFunc = Callable[..., Awaitable[Any]]
type CallerFunc = Callable[[str, Iterable[Any], dict[str, Any]], Awaitable[Any]]


class RPCError(Exception):
    """Base class for public RPC errors"""


class RPC:
    """High-level RPC client/server"""

    handlers: dict[str, HandlerFunc]
    caller: CallerFunc

    def __init__(self, caller: CallerFunc):
        self.handlers = {}
        self.caller = caller

    def set_handler(self, method: str, handler: HandlerFunc):
        self.handlers[method] = handler

    async def handle(
        self,
        method: str,
        args: Iterable[Any],
        kwargs: dict[str, Any],
    ) -> Any:
        try:
            hf = self.handlers[method]
        except KeyError:
            raise RPCError(f"Method {method} not found")
        return await hf(*args, **kwargs)

    async def call(self, method: str, *args: Any, **kwargs: Any) -> Any:
        return await self.caller(method, args, kwargs)
