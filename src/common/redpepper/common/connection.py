"""Message sending and receiving functionality for RedPepper Agent and Manager"""

import logging
import random
import uuid
from typing import Any, Awaitable, Callable, Iterable

import msgpack
import trio

from .config import ConnectionConfig
from .errors import ProtocolError
from .messages import (
    Bye,
    Message,
    MessageType,
    Ping,
    Pong,
    Request,
    Response,
    get_type_code,
)
from .rpc import RPC, RPCError
from .slot import Slot

logger = logging.getLogger(__name__)
TRACE = 5


class Connection:
    """Base class for communication between RedPepper Agent and Manager"""

    config: ConnectionConfig
    """Connection configuration"""

    stream: trio.SSLStream[trio.SocketStream]
    """Connection stream"""

    remote_address: tuple[str, int]
    """Remote address of the connection"""

    message_handlers: dict[int, Callable[[MessageType], Awaitable[None]]]
    """Low-level message handlers"""

    rpc: RPC
    """High-level RPC server"""

    def __init__(
        self,
        config: ConnectionConfig,
        stream: trio.SSLStream[trio.SocketStream],
    ):
        self.config = config
        self.stream = stream
        self.remote_address = stream.transport_stream.socket.getpeername()
        self.message_handlers = {
            get_type_code(Ping): self._handle_ping,
            get_type_code(Pong): self._handle_pong,
            get_type_code(Bye): self._handle_bye,
        }

        self._send_lock = trio.Lock()
        self._cancel_scope = trio.CancelScope()
        self._read_buffer = b""
        self._pong_slot: Slot | None = None
        self._response_slots: dict[str, Slot[Response]] = {}
        self.trio_nursery: trio.Nursery

    async def run(self) -> None:
        with self._cancel_scope:
            async with trio.open_nursery() as nursery:
                self.trio_nursery = nursery
                nursery.start_soon(self._receive_messages)
                nursery.start_soon(self._ping_periodically)

    # Message receiving

    async def _receive_messages(self) -> None:
        logger.log(TRACE, "Receiving messages from %s", self.remote_address)
        while True:
            try:
                m = await self.receive_message_direct()
            except trio.BrokenResourceError:
                logger.error("Connection broken from %s", self.remote_address)
                break
            except trio.ClosedResourceError:
                logger.debug("Connection closed by %s", self.remote_address)
                break
            except ProtocolError:
                logger.error("Protocol error from %s", self.remote_address)
                break
            self.trio_nursery.start_soon(self._handle_message, m)
        logger.log(TRACE, "Done reading messages from %s", self.remote_address)
        await self.close()

    async def receive_message_direct(self) -> MessageType:
        while True:
            data = await self.stream.receive_some(1024)
            if not data:
                raise trio.BrokenResourceError("Expected message, got EOF")
            logger.log(TRACE, "Received data from %s: %r", self.remote_address, data)
            self._read_buffer += data
            if len(self._read_buffer) < 4:
                continue
            msg_len = int.from_bytes(self._read_buffer[:4], "big", signed=False)
            if msg_len > self.config.max_message_size:
                logger.error(
                    "Received indicator of message with length %s (too big), closing connection",
                    msg_len,
                )
                # Log a warning if the message starts with "HTTP" to help diagnose
                if self._read_buffer[:4] == b"HTTP":
                    logger.info(
                        "It seems that RedPepper was pointed to an remote server that is currently serving HTTP. "
                        "Please make sure the hostname and port are correct."
                    )
                await self.close()
                raise ProtocolError("Message too big")
            if msg_len > len(self._read_buffer) - 4:
                continue
            try:
                data = msgpack.unpackb(self._read_buffer[4 : msg_len + 4])
            except Exception as e:
                logger.error(
                    "Failed to parse received message with length %s: %s", msg_len, e
                )
                raise ProtocolError("Invalid message: failed to unpack") from e
            finally:
                self._read_buffer = self._read_buffer[msg_len + 4 :]
            try:
                m = Message.validate_python(data)
            except ValueError as e:
                logger.error(
                    "Failed to validate received message with length %s: %s", msg_len, e
                )
                raise ProtocolError("Invalid message: failed to validate") from e
            logger.log(TRACE, "Received message from %s: %r", self.remote_address, m)
            return m

    async def _handle_message(self, message: MessageType) -> None:
        logger.log(TRACE, "Handling message from %s: %r", self.remote_address, message)
        handler = self.message_handlers.get(message.t, None)
        if handler:
            try:
                await handler(message)
            except Exception as e:
                logger.error("Error handling message: %s", e, exc_info=True)
        else:
            logger.warning("No handler for message type %s", message.t)

    # Message sending

    async def send_message(self, message: MessageType) -> None:
        data = msgpack.packb(message.model_dump())
        data_len = len(data).to_bytes(4, "big", signed=False)
        data = data_len + data
        async with self._send_lock:
            logger.log(TRACE, "Sending message to %s: %r", self.remote_address, message)
            await self.stream.send_all(data)
            logger.log(TRACE, "Sent message to %s: %r", self.remote_address, message)

    # Connection keepalive with Ping/Pong messages

    async def ping(self) -> None:
        if self._pong_slot:
            raise ProtocolError("Ping already in progress")
        ping = Ping(data=random.randint(0, 1000000))
        self._pong_slot = Slot()
        logger.debug("Ping %s", ping.data)
        await self.send_message(ping)
        pong = await self._pong_slot.get(timeout=self.config.ping_timeout)
        assert isinstance(pong, Pong)
        if pong.data != ping.data:
            raise ProtocolError("Ping/pong data mismatch")
        self._pong_slot = None

    async def _handle_ping(self, message: MessageType) -> None:
        assert isinstance(message, Ping)
        logger.log(TRACE, "Received ping %s", message.data)
        pong = Pong(data=message.data)
        await self.send_message(pong)

    async def _handle_pong(self, message: MessageType) -> None:
        assert isinstance(message, Pong)
        logger.debug("Pong %s", message.data)
        if self._pong_slot:
            await self._pong_slot.set(message)
        else:
            logger.warning("Received unexpected PONG message")

    async def _ping_periodically(self) -> None:
        interval = self.config.ping_interval
        logger.debug("Pinging %s every %s seconds", self.remote_address, interval)
        while True:
            await trio.sleep(interval)
            try:
                await self.ping()
            except Exception:
                logger.error("Ping failed", exc_info=True)
                await self.close()
                break

    # Connection closing

    async def close(self) -> None:
        logger.info("Closing connection to %s", self.remote_address)
        self._cancel_scope.cancel()
        try:
            await self.stream.aclose()
        except trio.ClosedResourceError:
            pass

    async def _handle_bye(self, message: MessageType) -> None:
        assert isinstance(message, Bye)
        logger.error("Received BYE message: %s", message.reason)
        await self.close()

    async def bye(self, reason: str) -> None:
        logger.error("Sending BYE message: %s", reason)
        bye = Bye(reason=reason)
        try:
            await self.send_message(bye)
        except ConnectionError as e:
            logger.error("Failed to send BYE message: %s", e)
        except trio.ClosedResourceError:
            logger.debug("Connection closed before BYE message could be sent")

    # High-level RPC

    def init_rpc(self, expose_error_info: bool = False):
        self.rpc = RPC(self._rpc_call)
        self.message_handlers[get_type_code(Request)] = self._rpc_handle_request
        self.message_handlers[get_type_code(Response)] = self._rpc_handle_response
        self._expose_error_info = expose_error_info

    def _generate_request_id(self) -> str:
        return uuid.uuid4().hex

    async def _rpc_call(
        self, method: str, args: Iterable[Any], kwargs: dict[str, Any]
    ) -> Any:
        req = Request(
            id=self._generate_request_id(),
            method=method,
            args=list(args),
            kwargs=kwargs,
        )
        slot = self._response_slots[req.id] = Slot()
        await self.send_message(req)
        resp = await slot.get()
        if resp.success:
            return resp.data
        else:
            raise RPCError(resp.data)

    async def _rpc_handle_request(self, request: MessageType) -> None:
        assert isinstance(request, Request)
        try:
            res = await self.rpc.handle(request.method, request.args, request.kwargs)
        except RPCError as e:
            response = Response(id=request.id, success=False, data=str(e))
        except Exception as e:
            logger.error("RPC call failed", exc_info=True)
            response = Response(
                id=request.id,
                success=False,
                data=str(e) if self._expose_error_info else "RPC call failed",
            )
        else:
            response = Response(id=request.id, success=True, data=res)
        await self.send_message(response)

    async def _rpc_handle_response(self, response: MessageType) -> None:
        assert isinstance(response, Response)
        try:
            slot = self._response_slots.pop(response.id)
        except KeyError:
            logger.error("No response slot for request ID %s", response.id)
        else:
            await slot.set(response)
