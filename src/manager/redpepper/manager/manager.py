"""RedPepper Manager"""

import hashlib
import importlib
import ipaddress
import json
import logging
import ssl
import time
import typing

import trio

from redpepper.common.connection import Connection, ProtocolError
from redpepper.common.messages_pb2 import (
    BYE,
    CLIENTHELLO,
    COMMAND,
    COMMANDPROGRESS,
    COMMANDRESULT,
    REQUEST,
    RESPONSE,
    SERVERHELLO,
    Message,
)
from redpepper.common.requests import RequestError

from .apiserver import APIServer
from .config import ManagerConfig
from .data import DataManager
from .eventlog import CommandLog, EventBus

logger = logging.getLogger(__name__)
TRACE = 5


class Manager:
    """RedPepper Manager"""

    config: ManagerConfig
    """Manager configuration"""

    running: trio.Event
    """Event that is set when the manager is running"""

    def __init__(self, config: ManagerConfig):
        self.config = config
        self.connections: list[AgentConnection] = []
        self.data_manager = DataManager(self.config.data_base_dir)
        self.event_bus = EventBus()
        self.command_log = CommandLog(self.config.command_log_file)
        self.tls_context = config.load_tls_context(ssl.Purpose.CLIENT_AUTH)
        self.api_server = APIServer(self, self.config)
        self.last_command_id: int = 0
        self._cancel_scope = trio.CancelScope()
        self.running = trio.Event()

    async def run(self):
        """Run the manager"""
        with self._cancel_scope:
            async with trio.open_nursery() as nursery:
                nursery.start_soon(self.api_server.run)
                nursery.start_soon(self._purge_command_log)
                logger.info(
                    "Starting server on %s:%s",
                    self.config.bind_host,
                    self.config.bind_port,
                )
                listeners = await trio.open_ssl_over_tcp_listeners(
                    port=self.config.bind_port,
                    ssl_context=self.tls_context,
                    host=self.config.bind_host,
                )
                nursery.start_soon(self._serve, listeners, nursery)
                self.running.set()

    async def _serve(
        self,
        listeners: list[trio.SSLListener[trio.SocketStream]],
        handler_nursery: trio.Nursery,
    ):
        await trio.serve_listeners(
            handler=self.handle_connection,
            listeners=listeners,
            handler_nursery=handler_nursery,
        )

    async def handle_connection(self, stream):
        """Handle a connection"""
        try:
            conn = AgentConnection(stream, self)
            logger.info("Received connection from %s", conn.conn.remote_address)
            await self.event_bus.post(type="connected", ip=conn.conn.remote_address[0])
            logger.debug("Performing TLS handshake")
            await conn.conn.stream.do_handshake()
            self.connections.append(conn)
            logger.debug("Starting connection")
            try:
                await conn.run()
                logger.debug("Stopping connection")
            finally:
                self.connections.remove(conn)
                await self.event_bus.post(
                    type="disconnected",
                    agent=conn.agent_id,
                    ip=conn.conn.remote_address[0],
                )
        except Exception:
            logger.error("Connection error", exc_info=True)

    def connected_agents(self):
        """Return a list of connected agents"""
        return [conn.agent_id for conn in self.connections if conn.agent_id is not None]

    async def send_command(self, agent, command, args, kw):
        """Run a command on an agent"""
        for conn in self.connections:
            if conn.agent_id == agent:
                await conn.send_command(command, args, kw)
                return True
        logger.error("Agent %s not connected", agent)
        return False

    async def _purge_command_log(self):
        """Periodically purge the event log"""
        if not self.config.command_log_purge_interval:
            return
        while True:
            await self.command_log.purge(self.config.command_log_max_age)
            await trio.sleep(self.config.command_log_purge_interval)

    async def shutdown(self):
        """Shutdown the manager"""
        logger.info("Shutting down")
        await self.api_server.shutdown()
        for conn in self.connections:
            await conn.conn.bye("server shutting down")
            await conn.conn.close()
        self._cancel_scope.cancel()


class AgentConnection:
    """Connection to an agent"""

    config: ManagerConfig
    """Manager configuration"""

    manager: Manager
    """Manager instance"""

    conn: Connection
    """Connection instance"""

    agent_id: str | None
    """Agent ID"""

    def __init__(self, stream: trio.SSLStream, manager: Manager):
        self.config = manager.config
        self.manager = manager
        self.conn = Connection(self.config, stream)
        self.agent_id = None

    async def run(self):
        await self.handshake()
        await self.conn.run()

    async def handshake(self):
        logger.debug("Waiting for client hello")
        message = await self.conn.receive_message_direct()
        if message.type != CLIENTHELLO:
            raise ProtocolError("expected client hello")
        logger.info("Hello from client ID: %s", message.client_hello.clientID)
        machine_id = message.client_hello.clientID

        success = False
        entry = self.manager.data_manager.get_agent_entry(machine_id)
        ip_allowed = False
        ipaddr = ipaddress.ip_address(self.conn.remote_address[0])
        allowed_ips = entry.get("allowed_ips", [])
        if isinstance(allowed_ips, str):
            allowed_ips = [allowed_ips]
        for iprange in allowed_ips:
            try:
                iprange = ipaddress.ip_network(iprange)
            except ValueError:
                logger.error("Invalid IP range: %s", iprange)
                continue
            if ipaddr in iprange:
                ip_allowed = True
                break
        else:
            logger.warning(
                "IP %s not allowed for %s", self.conn.remote_address[0], machine_id
            )
        secret_hash = hashlib.sha256(message.client_hello.auth.encode()).hexdigest()
        logger.debug("Secret hash for %s: %s", machine_id, secret_hash)
        if ip_allowed and secret_hash == entry.get("secret_hash", None):
            success = True

        if not success:
            await self.manager.event_bus.post(
                type="auth_failure",
                agent=machine_id,
                ip=self.conn.remote_address[0],
                secret_hash=secret_hash,
            )
            bye = Message()
            bye.type = BYE
            bye.bye.reason = "authentication failed"
            await self.conn.send_message(bye)
            logger.error(
                "Auth from %s failed for %s",
                self.conn.remote_address[0],
                machine_id,
            )
            await self.conn.close()
            return
        await self.manager.event_bus.post(
            type="auth_success",
            agent=machine_id,
            ip=self.conn.remote_address[0],
        )
        logger.info(
            "Auth from %s succeeded for %s",
            self.conn.remote_address[0],
            machine_id,
        )
        self.agent_id = machine_id

        res = Message()
        res.type = SERVERHELLO
        res.server_hello.version = 1
        logger.debug("Returning server hello to %s", self.agent_id)
        await self.conn.send_message(res)

        self.conn.message_handlers[COMMANDPROGRESS] = self.handle_command_progress
        self.conn.message_handlers[COMMANDRESULT] = self.handle_command_result
        self.conn.message_handlers[REQUEST] = self.handle_request

    async def handle_command_progress(self, message: Message):
        logger.debug("Command status from %s", self.agent_id)
        logger.debug("ID: %s", message.progress.commandID)
        logger.debug(
            "Progress: %s/%s",
            message.progress.current,
            message.progress.total,
        )
        await self.manager.command_log.command_progressed(
            message.progress.commandID,
            message.progress.current,
            message.progress.total,
        )
        await self.manager.event_bus.post(
            type="command_progress",
            agent=self.agent_id,
            # string because JavaScript numbers are not big enough
            id=str(message.progress.commandID),
            progress_current=message.progress.current,
            progress_total=message.progress.total,
            message=message.progress.message,
        )

    async def handle_command_result(self, message: Message):
        logger.debug("Command result from %s", self.agent_id)
        logger.debug("ID: %s", message.result.commandID)
        logger.debug("Status: %s", message.result.status)
        logger.debug("Changed: %s", message.result.changed)
        logger.debug("Output: %s", message.result.output)
        await self.manager.command_log.command_finished(
            message.result.commandID,
            message.result.status,
            message.result.changed,
            message.result.output,
        )
        await self.manager.event_bus.post(
            type="command_result",
            agent=self.agent_id,
            # string because JavaScript numbers are not big enough
            id=str(message.result.commandID),
            status=message.result.status,
            changed=message.result.changed,
            output=message.result.output,
        )

    async def handle_request(self, message: Message):
        logger.debug("Request from %s", self.agent_id)
        logger.debug("ID: %s", message.request.requestID)
        logger.debug("Name: %s", message.request.name)
        logger.debug("Data: %s", message.request.data)

        res = Message()
        res.type = RESPONSE
        res.response.requestID = message.request.requestID
        dtype: str = message.request.name

        try:
            if not dtype.isidentifier():
                raise RequestError("invalid request type identifier")
            kwargs = json.loads(message.request.data)
            if not isinstance(kwargs, dict):
                raise RequestError("request payload is not a JSON mapping")
            handler = self.get_request_handler(dtype)
            result = handler(self, **kwargs)
            if isinstance(result, typing.Coroutine):
                result = await result
            res.response.data = json.dumps(result)
            res.response.success = True
        except (RequestError, TypeError) as e:
            logger.error("Request error: %s", e)
            res.response.success = False
            res.response.data = str(e)
        except Exception:
            logger.error("Failed to handle data request", exc_info=True)
            res.response.success = False
            res.response.data = "internal error"
        logger.debug("Returning data response to %s", self.agent_id)
        await self.conn.send_message(res)

    def get_request_handler(self, dtype: str):
        try:
            module = importlib.import_module(f"redpepper.requests.{dtype}")
        except ImportError:
            try:
                assert self.agent_id is not None
                module = self.manager.data_manager.get_request_module(
                    self.agent_id, dtype
                )
            except ImportError as e:
                raise RequestError(f"request module not found: {dtype}") from e
        try:
            return module.call
        except AttributeError as e:
            raise RequestError(f"request module missing call function: {dtype}") from e

    async def send_command(self, command: str, args: list, kw: dict):
        logger.debug("Sending command %s to %s", command, self.agent_id)
        res = Message()
        res.type = COMMAND
        self.manager.last_command_id += 1
        command_id = (
            int(time.strftime("%Y%m%d%H%M%S")) * 1000 + self.manager.last_command_id
        )
        res.command.commandID = command_id
        res.command.type = command
        res.command.data = json.dumps({"[args]": args, **kw})
        await self.conn.send_message(res)
        await self.manager.command_log.command_started(
            command_id,
            time.time(),
            self.agent_id,
            json.dumps({"command": command, "args": args, "kw": kw}),
        )
        await self.manager.event_bus.post(
            type="command",
            agent=self.agent_id,
            # string because JavaScript numbers are not big enough
            id=str(res.command.commandID),
            command=command,
            args=args,
            kw=kw,
        )
