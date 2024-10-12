"""Message sending and receiving functionality for RedPepper Agent and Manager"""

import logging
import random

import trio
from google.protobuf.message import DecodeError, EncodeError

from .messages_pb2 import Message, MessageType

logger = logging.getLogger(__name__)
TRACE = 5


class Connection:
    def __init__(
        self,
        stream: trio.SSLStream,
        ping_timeout: float = 5,
        ping_interval: int = 10,
    ):
        self.stream: trio.SSLStream = stream
        self.ping_interval: float = ping_interval
        self.ping_timeout: float = ping_timeout
        self.pong_event: trio.Event | None = None
        self.remote_address: tuple[str, int] = (
            stream.transport_stream.socket.getpeername()
        )
        self.writeq_send, self.writeq_recv = trio.open_memory_channel(10)
        self.message_handlers = {
            MessageType.PING: self.handle_ping,
            MessageType.PONG: self.handle_pong,
            MessageType.BYE: self.handle_bye,
        }
        self._closed = False

    async def run(self):
        async with trio.open_nursery() as nursery:
            nursery.start_soon(self._receive_messages, nursery)
            nursery.start_soon(self._send_messages)
            nursery.start_soon(self._ping_periodically, self.ping_interval)

    async def _receive_messages(self, nursery: trio.Nursery):
        logger.log(TRACE, "Receiving messages from %s", self.remote_address)
        thedata = b""
        while True:
            try:
                data = await self.stream.receive_some(1024)
            except trio.BrokenResourceError:
                logger.error("Connection broken from %s", self.remote_address)
                break
            except trio.ClosedResourceError:
                logger.debug("Connection closed by %s", self.remote_address)
                break
            if not data:
                logger.info("Connection closed by %s", self.remote_address)
                break
            logger.log(TRACE, "Received data from %s: %r", self.remote_address, data)
            thedata += data

            if len(thedata) < 4:
                continue
            msg_len = int.from_bytes(thedata[:4], "big", signed=False)
            if msg_len > 65536:
                logger.error(
                    "Received indicator of message with length %s (too big), closing connection",
                    msg_len,
                )
                if thedata[:4] == b"HTTP":
                    logger.error(
                        "RedPepper was connected to an remote server that is currently serving HTTP. "
                        "Please make sure the address is correct and restart the Agent."
                    )
                else:
                    await self.bye("protocol error: message too big")
                break
            if msg_len > len(thedata) - 4:
                continue
            m = Message()
            try:
                m.ParseFromString(thedata[4 : msg_len + 4])
            except DecodeError:
                logger.error("Failed to parse received message with length %s", msg_len)
                await self.bye("protocol error: invalid message")
                break
            thedata = thedata[msg_len + 4 :]
            logger.log(TRACE, "Received message from %s: %r", self.remote_address, m)
            nursery.start_soon(self._handle_message, m)
        logger.log(TRACE, "Done reading messages from %s", self.remote_address)
        await self.close()

    async def _handle_message(self, message):
        logger.log(TRACE, "Handling message from %s: %r", self.remote_address, message)
        handler = self.message_handlers.get(message.type, None)
        if handler:
            try:
                await handler(message)
            except Exception as e:
                logger.error("Error handling message: %s", e, exc_info=True)
        else:
            logger.warn("No handler for message type %s", message.type)

    async def _send_messages(self):
        logger.log(TRACE, "Sending messages to %s", self.remote_address)
        try:
            while True:
                if self._closed:
                    break
                try:
                    message = self.writeq_recv.receive_nowait()
                except trio.WouldBlock:
                    await trio.sleep(0.01)
                    continue
                logger.log(
                    TRACE, "Sending message to %s: %r", self.remote_address, message
                )
                try:
                    data = message.SerializeToString()
                except EncodeError:
                    logger.error("Failed to serialize message", exc_info=True)
                    continue
                data_len = len(data).to_bytes(4, "big", signed=False)
                await self.stream.send_all(data_len + data)
                logger.log(
                    TRACE, "Sent message to %s: %r", self.remote_address, message
                )
        except trio.ClosedResourceError:
            logger.info("Connection closed by %s", self.remote_address)
        logger.log(TRACE, "Done sending messages to %s", self.remote_address)

    def send_message_threadsafe(self, message):
        logger.log(TRACE, "Queueing message to %s: %r", self.remote_address, message)
        return trio.from_thread.run(self.send_message, message)

    async def send_message(self, message):
        await self.writeq_send.send(message)

    async def ping(self):
        ping = Message()
        ping.type = MessageType.PING
        ping.ping.data = random.randint(0, 1000000)
        self.pong_event = trio.Event()
        logger.debug("Ping %s", ping.ping.data)
        await self.send_message(ping)
        with trio.fail_after(self.ping_timeout) as scope:
            await self.pong_event.wait()

    async def handle_ping(self, message):
        logger.log(TRACE, "Received ping %s", message.ping.data)
        pong = Message()
        pong.type = MessageType.PONG
        pong.pong.data = message.ping.data
        await self.send_message(pong)

    async def handle_pong(self, message):
        logger.debug("Pong %s", message.pong.data)
        if self.pong_event:
            self.pong_event.set()
        else:
            logger.warn("Received unexpected PONG message")

    async def handle_bye(self, message):
        logger.error("Received BYE message: %s", message.bye.reason)
        await self.close()

    async def _ping_periodically(self, interval):
        logger.log(TRACE, "Pinging %s every %s seconds", self.remote_address, interval)
        self._ping_cancel_scope = trio.CancelScope()
        with self._ping_cancel_scope:
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
        self._ping_cancel_scope.cancel()
        await self.writeq_send.aclose()
        await self.writeq_recv.aclose()
        try:
            await self.stream.aclose()
        except trio.ClosedResourceError:
            pass
        self._closed = True

    async def bye(self, reason):
        logger.error("Sending BYE message: %s", reason)
        bye = Message()
        bye.type = MessageType.BYE
        bye.bye.reason = reason
        try:
            await self.send_message(bye)
        except ConnectionError as e:
            logger.error("Failed to send BYE message: %s", e)
