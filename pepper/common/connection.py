"""Message sending and receiving functionality for Pepper Agent and Manager"""

import asyncio
import logging
import queue
import random

from google.protobuf.message import DecodeError, EncodeError

from pepper.common.messages_pb2 import Message, MessageType

logger = logging.getLogger(__name__)
TRACE = 5


class Connection:
    def __init__(self, reader, writer, ping_timeout=5, ping_frequency=10):
        self.reader = reader
        self.writer = writer
        self.remote_address = writer.get_extra_info("peername")
        self.write_lock = asyncio.Lock()
        self.message_handlers = {
            MessageType.PING: self.handle_ping,
            MessageType.PONG: self.handle_pong,
            MessageType.BYE: self.handle_bye,
        }
        self.ping_timeout = ping_timeout
        self.ping_timeout_task = None
        self.write_queue = queue.Queue(10)
        self.receive_task = asyncio.create_task(self.receive_messages())
        self.ping_task = asyncio.create_task(self.ping_periodically(ping_frequency))

    async def receive_messages(self):
        logger.log(TRACE, "Receiving messages from %s", self.remote_address)
        thedata = b""
        while True:
            try:
                data = await self.reader.read(1024)
            except ConnectionError as err:
                logger.error("Error reading from %s: %s", self.remote_address, err)
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
            try:
                await self.handle_message(m)
            except Exception as err:
                logger.error("Failed to handle message: %s", err, exc_info=1)
        logger.log(TRACE, "Done reading messages from %s", self.remote_address)
        self.close()

    async def handle_message(self, message):
        handler = self.message_handlers.get(message.type)
        if handler:
            await handler(message)
        else:
            logger.error("No handler for message type %s", message.type)
            await self.bye("protocol error: unknown message type")
            self.close()

    def send_message_threadsafe(self, message, asyncio_loop):
        logger.log(TRACE, "Queueing message to %s: %r", self.remote_address, message)
        return asyncio.run_coroutine_threadsafe(
            self.send_message(message), asyncio_loop
        ).result()

    async def send_message(self, message):
        logger.log(TRACE, "Sending message to %s: %r", self.remote_address, message)
        try:
            data = message.SerializeToString()
        except EncodeError:
            logger.error("Failed to serialize message", exc_info=1)
            raise
        data_len = len(data).to_bytes(4, "big", signed=False)
        async with self.write_lock:
            self.writer.write(data_len + data)
            try:
                await self.writer.drain()
            except ConnectionError as err:
                logger.error("Error writing to %s: %s", self.remote_address, err)
                self.close()
                raise
        logger.log(TRACE, "Sent message to %s: %r", self.remote_address, message)

    async def ping(self):
        logger.log(TRACE, "Ping %s", self.remote_address)
        ping = Message()
        ping.type = MessageType.PING
        ping.ping.data = random.randint(0, 1000000)
        await self.send_message(ping)
        self.ping_timeout_task = asyncio.get_running_loop().call_later(
            self.ping_timeout, self.ping_timeout_handler
        )

    async def handle_ping(self, message):
        logger.log(TRACE, "Received ping %s", message.ping.data)
        pong = Message()
        pong.type = MessageType.PONG
        pong.pong.data = message.ping.data
        await self.send_message(pong)

    def ping_timeout_handler(self):
        logger.error("Ping timeout")
        self.close()

    async def handle_pong(self, message):
        logger.log(TRACE, "Received pong %s", message.pong.data)
        if self.ping_timeout_task:
            self.ping_timeout_task.cancel()
            self.ping_timeout_task = None

    async def handle_bye(self, message):
        logger.error("Received BYE message: %s", message.bye.reason)
        self.close()

    async def ping_periodically(self, interval):
        logger.log(TRACE, "Pinging %s every %s seconds", self.remote_address, interval)
        while True:
            await asyncio.sleep(interval)
            await self.ping()

    def close(self):
        logger.info("Closing connection to %s", self.remote_address)
        self.ping_task.cancel()
        if self.ping_timeout_task:
            self.ping_timeout_task.cancel()
        self.receive_task.cancel()
        self.writer.close()

    async def bye(self, reason):
        logger.error("Sending BYE message: %s", reason)
        bye = Message()
        bye.type = MessageType.BYE
        bye.bye.reason = reason
        try:
            await self.send_message(bye)
        except ConnectionError as e:
            logger.error("Failed to send BYE message: %s", e)

    async def run(self):
        await asyncio.gather(self.receive_task, self.ping_task)
