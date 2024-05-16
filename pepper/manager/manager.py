"""Pepper Manager"""

import asyncio
import json
import logging
import os
import ssl

from pepper.common.connection import Connection
from pepper.common.messages_pb2 import Message, MessageType
from pepper.manager.config import load_manager_config
from pepper.manager.data import NODATA, DataManager

logger = logging.getLogger(__name__)
TRACE = 5


class Manager:
    """Pepper Manager"""

    def __init__(self, config=None, config_file=None):
        self.config = config or load_manager_config(config_file)
        self.connections = []
        self.datamanager = DataManager(self.config["data_base_dir"])
        self.tls_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        self.tls_context.load_cert_chain(
            self.config["tls_cert_file"],
            self.config["tls_key_file"],
            password=self.config["tls_key_password"],
        )
        if os.stat(self.config["tls_cert_file"]).st_mode & 0o77 != 0:
            raise ValueError(
                "TLS certificate file %s is insecure, please set permissions to 600"
                % self.config["tls_cert_file"],
            )
        if os.stat(self.config["tls_key_file"]).st_mode & 0o77 != 0:
            raise ValueError(
                "TLS key file %s is insecure, please set permissions to 600"
                % self.config["tls_key_file"],
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
        self.config = config
        self.datamanager = datamanager
        self.conn = Connection(
            reader, writer, config["ping_timeout"], config["ping_frequency"]
        )
        self.machine_id = None
        self.conn.message_handlers[MessageType.CLIENTHELLO] = self.handle_hello
        self.last_command_id = 1000
        self.last_command_id_lock = asyncio.Lock()

    async def handle_hello(self, message):
        logger.info("Hello from client ID: %s", message.client_hello.clientID)
        logger.info("Hello auth: %s", message.client_hello.auth)
        self.machine_id = message.client_hello.clientID

        res = Message()
        res.type = MessageType.SERVERHELLO
        res.server_hello.version = 1
        logger.debug("Returning server hello to %s", self.machine_id)
        await self.conn.send_message(res)

        try:
            del self.conn.message_handlers[MessageType.CLIENTHELLO]
        except KeyError:
            logger.error("Client hello message received more than once")
            self.conn.close()
        else:
            self.conn.message_handlers[MessageType.COMMANDSTATUS] = (
                self.handle_command_status
            )
            self.conn.message_handlers[MessageType.DATAREQUEST] = (
                self.handle_data_request
            )

        self._command_task = asyncio.create_task(self.send_test_commands())

    async def handle_command_status(self, message):
        logger.info("Command status from %s", self.machine_id)
        logger.info("ID: %s", message.status.commandID)
        logger.info("Status: %s", message.status.status)
        logger.info(
            "Progress: %s/%s",
            message.status.progress.current,
            message.status.progress.total,
        )
        logger.info("Output: %r", message.status.data)
        # TODO: handle command status

    async def handle_data_request(self, message):
        logger.info("Data request from %s", self.machine_id)
        logger.info("ID: %s", message.data_request.requestID)
        logger.info("Type: %s", message.data_request.type)
        logger.info("Data: %s", message.data_request.data)

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
                res.data_response.data = "no data available"
            else:
                try:
                    json_data = json.dumps(data)
                except Exception as e:
                    logger.error(
                        "Failed to serialize requested data: %s", e, exc_info=1
                    )
                    res.data_response.ok = False
                    res.data_response.data = "failed to serialize data"
                else:
                    res.data_response.ok = True
                    res.data_response.data = json_data
        elif dtype == "state":
            state = self.datamanager.get_state(self.machine_id)
            try:
                json_state = json.dumps(state)
            except Exception as e:
                logger.error("Failed to serialize state: %s", e, exc_info=1)
                res.data_response.ok = False
                res.data_response.data = "failed to serialize state"
            else:
                res.data_response.ok = True
                res.data_response.data = json_state
        else:
            logger.error("Unknown data request type: %s", dtype)
            res.data_response.ok = False
            res.data_response.data = "unknown data request type"
        logger.debug("Returning data response to %s", self.machine_id)
        await self.conn.send_message(res)

    async def send_command(self, command, args, kw):
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
        while True:
            await asyncio.sleep(2)
            await self.send_command("state", [], {})
            break
