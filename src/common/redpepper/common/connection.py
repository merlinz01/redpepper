"""Message sending and receiving functionality for RedPepper Agent and Manager"""

import logging
import random
import typing

import trio
from google.protobuf.message import DecodeError

from .config import ConnectionConfig
from .messages_pb2 import BYE, PING, PONG, Message

logger = logging.getLogger(__name__)
TRACE = 5


class ReceivedBye(Exception):
    """Exception raised when a BYE message is received"""


class ProtocolError(Exception):
    """Exception raised when a protocol error is detected"""


class Connection:
    """Base class for communication between RedPepper Agent and Manager"""

    config: ConnectionConfig
    """Connection configuration"""

    stream: trio.SSLStream[trio.SocketStream]
    """Connection stream"""

    remote_address: tuple[str, int]
    """Remote address of the connection"""

    message_handlers: dict[int, typing.Callable[[Message], typing.Awaitable[None]]]
    """Handlers for incoming messages"""

    def __init__(
        self,
        config: ConnectionConfig,
        stream: trio.SSLStream[trio.SocketStream],
    ):
        self.config = config
        self.stream = stream
        self.remote_address = stream.transport_stream.socket.getpeername()
        self.message_handlers = {
            PING: self.handle_ping,
            PONG: self.handle_pong,
            BYE: self.handle_bye,
        }

        self._send_lock = trio.Lock()
        self._cancel_scope = trio.CancelScope()
        self._read_buffer = b""

    async def run(self):
        with self._cancel_scope:
            async with trio.open_nursery() as nursery:
                nursery.start_soon(self._receive_messages, nursery)
                nursery.start_soon(self._ping_periodically, self.config.ping_interval)

    async def _receive_messages(self, nursery: trio.Nursery):
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
            nursery.start_soon(self._handle_message, m)
        logger.log(TRACE, "Done reading messages from %s", self.remote_address)
        await self.close()

    async def receive_message_direct(self) -> Message:
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
                    logger.error(
                        "It seems that RedPepper was pointed to an remote server that is currently serving HTTP. "
                        "Please make sure the hostname and port are correct."
                    )
                raise ProtocolError("Message too big")
            if msg_len > len(self._read_buffer) - 4:
                continue
            m = Message()
            try:
                m.ParseFromString(self._read_buffer[4 : msg_len + 4])
            except DecodeError:
                logger.error("Failed to parse received message with length %s", msg_len)
                raise ProtocolError("Invalid message")
            self._read_buffer = self._read_buffer[msg_len + 4 :]
            logger.log(TRACE, "Received message from %s: %r", self.remote_address, m)
            return m

    async def _handle_message(self, message):
        logger.log(TRACE, "Handling message from %s: %r", self.remote_address, message)
        handler = self.message_handlers.get(message.type, None)
        if handler:
            try:
                await handler(message)
            except ReceivedBye:
                raise
            except Exception as e:
                logger.error("Error handling message: %s", e, exc_info=True)
        else:
            logger.warn("No handler for message type %s", message.type)

    async def send_message(self, message: Message):
        async with self._send_lock:
            logger.log(TRACE, "Sending message to %s: %r", self.remote_address, message)
            data = message.SerializeToString()
            data_len = len(data).to_bytes(4, "big", signed=False)
            await self.stream.send_all(data_len + data)
            logger.log(TRACE, "Sent message to %s: %r", self.remote_address, message)

    def send_message_threadsafe(self, message):
        logger.log(TRACE, "Queueing message to %s: %r", self.remote_address, message)
        return trio.from_thread.run(self.send_message, message)

    async def ping(self):
        ping = Message()
        ping.type = PING
        ping.ping.data = random.randint(0, 1000000)
        self._pong_event = trio.Event()
        logger.debug("Ping %s", ping.ping.data)
        await self.send_message(ping)
        with trio.fail_after(self.config.ping_timeout):
            await self._pong_event.wait()

    async def handle_ping(self, message):
        logger.log(TRACE, "Received ping %s", message.ping.data)
        pong = Message()
        pong.type = PONG
        pong.pong.data = message.ping.data
        await self.send_message(pong)

    async def handle_pong(self, message):
        logger.debug("Pong %s", message.pong.data)
        if self._pong_event:
            self._pong_event.set()
        else:
            logger.warn("Received unexpected PONG message")

    async def handle_bye(self, message):
        logger.error("Received BYE message: %s", message.bye.reason)
        await self.close()
        raise ReceivedBye(message.bye.reason)

    async def _ping_periodically(self, interval):
        logger.log(TRACE, "Pinging %s every %s seconds", self.remote_address, interval)
        while True:
            await trio.sleep(interval)
            try:
                await self.ping()
            except (trio.TooSlowError, trio.ClosedResourceError):
                logger.error("Ping failed")
                await self.close()
                break

    async def close(self):
        logger.info("Closing connection to %s", self.remote_address)
        self._cancel_scope.cancel()
        try:
            await self.stream.aclose()
        except trio.ClosedResourceError:
            pass

    async def bye(self, reason):
        logger.error("Sending BYE message: %s", reason)
        bye = Message()
        bye.type = BYE
        bye.bye.reason = reason
        try:
            await self.send_message(bye)
        except ConnectionError as e:
            logger.error("Failed to send BYE message: %s", e)
        except trio.ClosedResourceError:
            logger.debug("Connection closed before BYE message could be sent")
