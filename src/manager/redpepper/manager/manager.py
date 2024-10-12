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

from redpepper.common.connection import Connection
from redpepper.common.messages_pb2 import Message, MessageType
from redpepper.common.requests import RequestError
from redpepper.common.tls import load_tls_context

from .apiserver import APIServer
from .config import load_manager_config
from .data import DataManager
from .eventlog import CommandLog, EventBus

logger = logging.getLogger(__name__)
TRACE = 5


class Manager:
    """RedPepper Manager"""

    def __init__(self, config=None, config_file=None):
        self.config: dict = config or load_manager_config(config_file)
        self.connections: list[AgentConnection] = []
        self.data_manager: DataManager = DataManager(self.config["data_base_dir"])
        self.event_bus: EventBus = EventBus()
        self.command_log: CommandLog = CommandLog(self.config["command_log_file"])
        self.tls_context: ssl.SSLContext = load_tls_context(
            ssl.Purpose.CLIENT_AUTH,
            self.config["tls_cert_file"],
            self.config["tls_key_file"],
            self.config["tls_key_password"],
            verify_mode=self.config["tls_verify_mode"],
            check_hostname=self.config["tls_check_hostname"],
            cafile=self.config["tls_ca_file"],
            capath=self.config["tls_ca_path"],
            cadata=self.config["tls_ca_data"],
        )
        self.api_server: APIServer = APIServer(self, self.config)
        self.last_command_id: int = 0

    async def run(self):
        """Run the manager"""
        host = self.config["bind_host"]
        port = self.config["bind_port"]
        logger.info("Starting server on %s:%s", host, port)
        async with trio.open_nursery() as nursery:
            nursery.start_soon(self.api_server.run)
            nursery.start_soon(self.purge_command_log_periodically)
            await trio.serve_ssl_over_tcp(
                self.handle_connection,
                host=host,
                port=port,
                ssl_context=self.tls_context,
                handler_nursery=nursery,
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
                await conn.conn.run()
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

    async def purge_command_log_periodically(self):
        """Periodically purge the event log"""
        if not self.config["command_log_purge_interval"]:
            return
        while True:
            await self.command_log.purge(self.config["command_log_max_age"])
            await trio.sleep(self.config["command_log_purge_interval"])


class AgentConnection:
    def __init__(self, stream: trio.SSLStream, manager: Manager):
        self.config: dict = manager.config
        self.manager: Manager = manager
        self.conn = Connection(
            stream, self.config["ping_timeout"], self.config["ping_frequency"]
        )
        self.agent_id: str = ""
        self.conn.message_handlers[MessageType.CLIENTHELLO] = self.handle_hello

    async def handle_hello(self, message: Message):
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
            logger.warn(
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
            await self.conn.bye("auth failed")
            logger.error(
                "Auth from %s failed for %s",
                self.conn.remote_address[0],
                self.agent_id,
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
        res.type = MessageType.SERVERHELLO
        res.server_hello.version = 1
        logger.debug("Returning server hello to %s", self.agent_id)
        await self.conn.send_message(res)

        del self.conn.message_handlers[MessageType.CLIENTHELLO]
        self.conn.message_handlers[MessageType.COMMANDPROGRESS] = (
            self.handle_command_progress
        )
        self.conn.message_handlers[MessageType.COMMANDRESULT] = (
            self.handle_command_result
        )
        self.conn.message_handlers[MessageType.REQUEST] = self.handle_request

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
        res.type = MessageType.RESPONSE
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
        res.type = MessageType.COMMAND
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
