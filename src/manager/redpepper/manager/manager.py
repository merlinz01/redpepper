"""RedPepper Manager"""

import hashlib
import importlib
import ipaddress
import json
import logging
import ssl
import time
import uuid
from enum import IntEnum
from typing import Any, Callable, Coroutine, Iterable

import trio

from redpepper.common.connection import Connection, ProtocolError
from redpepper.common.messages import (
    AgentHello,
    Bye,
    ManagerHello,
    MessageType,
    Notification,
    Request,
    Response,
    get_type_code,
)
from redpepper.common.operations import Result
from redpepper.common.requests import RequestError
from redpepper.common.slot import Slot
from redpepper.version import __version__

from .apiserver import APIServer
from .config import ManagerConfig
from .data import DataManager
from .eventlog import CommandLog, EventBus

logger = logging.getLogger(__name__)
TRACE = 5


class CommandStatus(IntEnum):
    """Command status"""

    SUCCESS = 1
    FAILED = 2
    CANCELLED = 3


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
        self.api_server = APIServer(self, self.config)
        self.running = trio.Event()

        self._tls_context = config.load_tls_context(ssl.Purpose.CLIENT_AUTH)
        self._last_command_id: int = 0
        self._cancel_scope = trio.CancelScope()
        self._command_result_handlers: dict[str, list[Callable]] = {}

    async def run(self) -> None:
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
                    ssl_context=self._tls_context,
                    host=self.config.bind_host,
                )
                nursery.start_soon(self._serve, listeners, nursery)
                self.running.set()

    async def _serve(
        self,
        listeners: list[trio.SSLListener[trio.SocketStream]],
        handler_nursery: trio.Nursery,
    ) -> None:
        await trio.serve_listeners(
            handler=self.handle_connection,
            listeners=listeners,
            handler_nursery=handler_nursery,
        )

    async def handle_connection(
        self, stream: trio.SSLStream[trio.SocketStream]
    ) -> None:
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

    def connected_agents(self) -> list[str]:
        """Return a list of connected agents"""
        return [conn.agent_id for conn in self.connections if conn.agent_id is not None]

    async def send_command(
        self,
        agent: str,
        command: str,
        args: Iterable[Any],
        kw: dict[str, Any],
    ) -> str | None:
        """Run a command on an agent"""
        for conn in self.connections:
            if conn.agent_id == agent:
                return await conn.send_command(command, args, kw)
        logger.error("Agent %s not connected", agent)
        return None

    async def await_command_result(
        self, command_id: str, timeout: float = 10 * 60
    ) -> Result:
        """Wait for a command result"""
        handlers = self._command_result_handlers.setdefault(command_id, [])
        slot = Slot()
        handlers.append(slot.set)
        try:
            return await slot.get(timeout=timeout)
        finally:
            handlers.remove(slot.set)

    async def _purge_command_log(self) -> None:
        """Periodically purge the event log"""
        if not self.config.command_log_purge_interval:
            return
        while True:
            await self.command_log.purge(self.config.command_log_max_age)
            await trio.sleep(self.config.command_log_purge_interval)

    async def shutdown(self) -> None:
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

    async def run(self) -> None:
        await self.handshake()
        await self.conn.run()

    async def handshake(self) -> None:
        logger.debug("Waiting for agent hello")
        message = await self.conn.receive_message_direct()
        if not isinstance(message, AgentHello):
            raise ProtocolError("expected agent hello")
        logger.info("Hello from agent ID: %s", message.id)
        machine_id = message.id

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
        secret_hash = hashlib.sha256(message.credentials.encode()).hexdigest()
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
            bye = Bye(reason="authentication failed")
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

        res = ManagerHello(version=__version__)
        logger.debug("Returning server hello to %s", self.agent_id)
        await self.conn.send_message(res)

        self.conn.message_handlers[get_type_code(Notification)] = (
            self.handle_notification
        )
        self.conn.message_handlers[get_type_code(Request)] = self.handle_request
        self.conn.message_handlers[get_type_code(Response)] = self.handle_response

    async def handle_notification(self, message: MessageType) -> None:
        assert isinstance(message, Notification)
        if message.type == "command_progress":
            await self.handle_command_progress(message)
        else:
            logger.error("Unhandled notification type: %s", message.type)

    async def handle_command_progress(self, message: Notification) -> None:
        logger.debug("Command status from %s", self.agent_id)
        data = message.data
        logger.debug("ID: %s", data["command_id"])
        logger.debug(
            "Progress: %s/%s",
            data["current"],
            data["total"],
        )
        await self.manager.command_log.command_progressed(
            data["command_id"],
            data["current"],
            data["total"],
        )
        await self.manager.event_bus.post(
            type="command_progress",
            agent=self.agent_id,
            # string because JavaScript numbers are not big enough
            id=str(data["command_id"]),
            progress_current=data["current"],
            progress_total=data["total"],
            message=data["message"],
        )

    async def handle_response(self, response: MessageType) -> None:
        assert isinstance(response, Response)
        logger.debug("Command result from %s", self.agent_id)
        logger.debug("ID: %s", response.id)
        if response.success:
            success = response.data["success"]
            changed = response.data["changed"]
            output = response.data["output"]
        else:
            success = False
            changed = False
            output = response.data
        status = CommandStatus.SUCCESS if success else CommandStatus.FAILED
        result = Result("")
        result.succeeded = success
        result.changed = changed
        result.output = output
        logger.debug("Success: %s", success)
        logger.debug("Data: %s", output)
        await self.manager.command_log.command_finished(
            response.id,
            status,
            changed,
            output,
        )
        await self.manager.event_bus.post(
            type="command_result",
            agent=self.agent_id,
            # string because JavaScript numbers are not big enough
            id=str(response.id),
            status=status,
            changed=changed,
            output=output,
        )
        for handler in self.manager._command_result_handlers.pop(response.id, []):
            await handler(result)

    async def handle_request(self, request: MessageType) -> None:
        assert isinstance(request, Request)
        logger.debug("Request from %s", self.agent_id)
        logger.debug("ID: %s", request.id)
        logger.debug("Method: %s", request.method)
        logger.debug("Params: %s", request.params)

        res = Response(id=request.id, success=False, data="")
        dtype: str = request.method

        try:
            if not dtype.isidentifier():
                raise RequestError("invalid request method identifier")
            handler = self._get_request_handler(dtype)
            result = handler(self, **request.params)
            if isinstance(result, Coroutine):
                result = await result
            res.data = result
            res.success = True
        except (RequestError, TypeError) as e:
            logger.error("Request error: %s", e)
            res.success = False
            res.data = str(e)
        except Exception:
            logger.error("Failed to handle data request", exc_info=True)
            res.success = False
            res.data = "internal error"
        logger.debug("Returning data response to %s", self.agent_id)
        await self.conn.send_message(res)

    def _get_request_handler(self, dtype: str) -> Callable:
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

    async def send_command(self, command: str, args: Iterable, kw: dict) -> str:
        assert self.agent_id is not None
        logger.debug("Sending command %s to %s", command, self.agent_id)
        command_id = uuid.uuid4().hex
        res = Request(id=command_id, method=command, params={"[args]": args, **kw})
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
            id=str(command_id),
            command=command,
            args=args,
            kw=kw,
        )
        return command_id
