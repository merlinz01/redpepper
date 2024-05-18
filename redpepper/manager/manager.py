"""RedPepper Manager"""

import asyncio
import hashlib
import ipaddress
import json
import logging
import os
import ssl

from redpepper.common.connection import Connection
from redpepper.common.messages_pb2 import Message, MessageType
from redpepper.manager.config import load_manager_config
from redpepper.manager.data import NODATA, DataManager

logger = logging.getLogger(__name__)
TRACE = 5


class Manager:
    """RedPepper Manager"""

    def __init__(self, config=None, config_file=None):
        self.config: dict = config or load_manager_config(config_file)
        self.connections: list[AgentConnection] = []
        self.datamanager: DataManager = DataManager(self.config["data_base_dir"])

        # Set up TLS context
        self.tls_context: ssl.SSLContext = ssl.create_default_context(
            ssl.Purpose.CLIENT_AUTH,
            cafile=self.config["tls_ca_file"],
            capath=self.config["tls_ca_path"],
            cadata=self.config["tls_ca_data"],
        )
        if os.stat(self.config["tls_key_file"]).st_mode & 0o77 != 0:
            raise ValueError(
                "TLS key file %s is insecure, please set permissions to 600"
                % self.config["tls_key_file"],
            )
        self.tls_context.load_cert_chain(
            self.config["tls_cert_file"],
            self.config["tls_key_file"],
            password=self.config["tls_key_password"],
        )
        if not isinstance(self.config["tls_check_hostname"], bool):
            raise ValueError("tls_check_hostname must be a boolean")
        self.tls_context.check_hostname = self.config["tls_check_hostname"]
        tvm = self.config["tls_verify_mode"]
        if tvm == "none":
            self.tls_context.verify_mode = ssl.CERT_NONE
        elif tvm == "optional":
            self.tls_context.verify_mode = ssl.CERT_OPTIONAL
        elif tvm == "required":
            self.tls_context.verify_mode = ssl.CERT_REQUIRED
        else:
            raise ValueError("Unknown TLS verify mode: %s" % tvm)

    async def run(self):
        """Run the manager"""
        addr = self.config["bind_address"]
        port = self.config["bind_port"]
        logger.debug("Starting server on %s:%s", addr, port)
        server = await asyncio.start_server(
            self.handle_connection, addr, port, ssl=self.tls_context
        )
        logger.info("Serving on %s:%s", addr, port)
        async with server:
            await server.serve_forever()

    async def handle_connection(self, reader, writer):
        """Handle a connection"""
        conn = AgentConnection(reader, writer, self.config, self.datamanager)
        logger.info("Received connection from %s", conn.conn.remote_address)
        self.connections.append(conn)


class AgentConnection:
    def __init__(self, reader, writer, config, datamanager):
        self.config: dict = config
        self.datamanager: DataManager = datamanager
        self.conn = Connection(
            reader, writer, config["ping_timeout"], config["ping_frequency"]
        )
        self.machine_id: str = None
        self.conn.message_handlers[MessageType.CLIENTHELLO] = self.handle_hello
        self.last_command_id: int = 1000
        self.last_command_id_lock = asyncio.Lock()

    async def handle_hello(self, message):
        logger.info("Hello from client ID: %s", message.client_hello.clientID)
        logger.info("Hello auth: %s", message.client_hello.auth)
        self.machine_id = message.client_hello.clientID

        success = False
        auth = self.datamanager.get_auth(self.machine_id)
        ip_allowed = False
        ipaddr = ipaddress.ip_address(self.conn.remote_address[0])
        for iprange in auth["allowed_ips"]:
            if ipaddr in iprange:
                ip_allowed = True
                break
        else:
            logger.warn(
                "IP %s not allowed for %s", self.conn.remote_address[0], self.machine_id
            )
        agentcert = self.conn.writer.get_extra_info("ssl_object").getpeercert(True)
        if agentcert is None:
            cert_hash = None
        else:
            cert_hash = hashlib.sha256(agentcert).hexdigest()
        logger.info(
            "Remote certificate hash for %s: %s",
            self.conn.remote_address[0],
            cert_hash,
        )
        secret_hash = hashlib.sha256(message.client_hello.auth.encode()).hexdigest()
        logger.info("Secret hash for %s: %s", self.machine_id, secret_hash)
        if (
            ip_allowed
            and cert_hash == auth["cert_hash"]
            and secret_hash == auth["secret_hash"]
        ):
            success = True

        if not success:
            await self.conn.bye("auth failed")
            logger.error(
                "Auth from %s failed for %s",
                self.conn.remote_address[0],
                self.machine_id,
            )
            self.conn.close()
            return
        logger.info(
            "Auth from %s succeeded for %s",
            self.conn.remote_address[0],
            self.machine_id,
        )

        res = Message()
        res.type = MessageType.SERVERHELLO
        res.server_hello.version = 1
        logger.debug("Returning server hello to %s", self.machine_id)
        await self.conn.send_message(res)

        del self.conn.message_handlers[MessageType.CLIENTHELLO]
        self.conn.message_handlers[MessageType.COMMANDSTATUS] = (
            self.handle_command_status
        )
        self.conn.message_handlers[MessageType.DATAREQUEST] = self.handle_data_request
        self._command_task = asyncio.create_task(self.send_test_commands())

    async def handle_command_status(self, message):
        logger.info("Command status from %s", self.machine_id)
        logger.debug("ID: %s", message.status.commandID)
        logger.info("Status: %s", message.status.status)
        logger.debug(
            "Progress: %s/%s",
            message.status.progress.current,
            message.status.progress.total,
        )
        logger.debug("Output: %r", message.status.data)
        # TODO: handle command status

    async def handle_data_request(self, message):
        logger.info("Data request from %s", self.machine_id)
        logger.debug("ID: %s", message.data_request.requestID)
        logger.debug("Type: %s", message.data_request.type)
        logger.debug("Data: %s", message.data_request.data)

        res = Message()
        res.type = MessageType.DATARESPONSE
        res.data_response.requestID = message.data_request.requestID
        dtype = message.data_request.type
        if dtype == "echo":
            res.data_response.data = message.data_request.data
        elif dtype == "data":
            data = self.datamanager.get_data(self.machine_id, message.data_request.data)
            if data is NODATA:
                res.data_response.ok = False
                res.data_response.string = "no data available"
            else:
                try:
                    json_data = json.dumps(data)
                except Exception as e:
                    logger.error(
                        "Failed to serialize requested data: %s", e, exc_info=1
                    )
                    res.data_response.ok = False
                    res.data_response.string = "failed to serialize data"
                else:
                    res.data_response.ok = True
                    res.data_response.string = json_data
        elif dtype == "state":
            state = self.datamanager.get_state(self.machine_id)
            try:
                json_state = json.dumps(state)
            except Exception as e:
                logger.error("Failed to serialize state: %s", e, exc_info=1)
                res.data_response.ok = False
                res.data_response.string = "failed to serialize state"
            else:
                res.data_response.ok = True
                res.data_response.string = json_state
        elif dtype == "file_mtime":
            path = self.datamanager.get_file_path(
                self.machine_id, message.data_request.data
            )
            if not path:
                res.data_response.ok = False
                res.data_response.string = "file not found"
            else:
                res.data_response.ok = True
                res.data_response.string = str(os.path.getmtime(path))
        elif dtype == "file_hash":
            path = self.datamanager.get_file_path(
                self.machine_id, message.data_request.data
            )
            if not path:
                res.data_response.ok = False
                res.data_response.string = "file not found"
            else:
                hash = hashlib.sha256()
                with open(path, "rb") as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        hash.update(chunk)
                res.data_response.ok = True
                res.data_response.bytes = hash.digest()
        elif dtype == "file_content":
            try:
                parameters = json.loads(message.data_request.data)
                if not isinstance(parameters, dict):
                    raise ValueError("parameters must be a dict")
                if "filename" not in parameters:
                    raise ValueError("filename parameter missing")
                if not isinstance(parameters.setdefault("offset", 0), int):
                    raise ValueError("offset must be an int")
                if "length" not in parameters:
                    raise ValueError("length parameter missing")
                if not isinstance(parameters["length"], int):
                    raise ValueError("length must be an int")
                if parameters["length"] < 0 or parameters["offset"] < 0:
                    raise ValueError("length and offset must be non-negative")
                if parameters["length"] > 65536 - 1000:
                    raise ValueError("length must be at most 64536")
            except Exception as e:
                logger.error("Failed to parse file content request: %s", e)
                res.data_response.ok = False
                res.data_response.string = "failed to parse request"
            else:
                path = self.datamanager.get_file_path(
                    self.machine_id, parameters["filename"]
                )
                if not path:
                    res.data_response.ok = False
                    res.data_response.string = "file not found"
                else:
                    try:
                        with open(path, "rb") as f:
                            f.seek(parameters["offset"])
                            data = f.read(parameters["length"])
                    except Exception as e:
                        logger.error("Failed to read file: %s", e, exc_info=1)
                        res.data_response.ok = False
                        res.data_response.string = "failed to read file"
                    else:
                        res.data_response.ok = True
                        res.data_response.bytes = data
        else:
            logger.error("Unknown data request type: %s", dtype)
            res.data_response.ok = False
            res.data_response.string = "unknown data request type"
        logger.debug("Returning data response to %s", self.machine_id)
        await self.conn.send_message(res)

    async def send_command(self, command, args, kw):
        logger.debug("Sending command %s to %s", command, self.machine_id)
        res = Message()
        res.type = MessageType.COMMAND
        async with self.last_command_id_lock:
            self.last_command_id += 1
            res.command.commandID = self.last_command_id
        res.command.type = command
        res.command.data = json.dumps({"[args]": args, **kw})
        await self.conn.send_message(res)

    async def send_test_commands(self):
        resp = Message()
        resp.type = MessageType.COMMAND
        await asyncio.sleep(2)
        await self.send_command(
            "file.Installed",
            [],
            {
                "path": "testfile.txt",
                "source": "testfile.txt",
                "user": "root",
                "group": "root",
                "mode": 0o644,
            },
        )
