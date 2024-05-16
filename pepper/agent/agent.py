"""Pepper Agent"""

import asyncio
import importlib
import json
import logging
import os
import queue
import subprocess
import threading
import traceback

from pepper.agent.config import load_agent_config
from pepper.agent.states import Task, topological_sort
from pepper.common.connection import Connection
from pepper.common.messages_pb2 import CommandStatus, Message, MessageType

logger = logging.getLogger(__name__)


class Agent:
    """Pepper Agent"""

    def __init__(self, config=None, config_file=None):
        self.config = config or load_agent_config(config_file)
        self.conn = None
        self.hello_timeout = None
        self.data_response_queues = {}
        self.last_message_id = 100
        self.last_message_id_lock = threading.Lock()

    async def connect(self):
        host = self.config["manager_host"]
        port = self.config["manager_port"]
        self.remote_address = (host, port)
        logger.info("Connecting to manager at %s:%s", host, port)
        try:
            reader, writer = await asyncio.open_connection(host, port)
        except ConnectionError:
            logger.error("Failed to connect to server", exc_info=1)
            raise
        self.conn = Connection(
            reader, writer, self.config["ping_timeout"], self.config["ping_interval"]
        )
        self.conn.message_handlers[MessageType.SERVERHELLO] = self.handle_hello
        hello = Message()
        hello.type = MessageType.CLIENTHELLO
        hello.client_hello.clientID = self.config["machine_id"]
        hello.client_hello.auth = "password1234"
        logger.debug("Sending client hello message to manager")
        self.hello_timeout = asyncio.get_running_loop().call_later(
            self.config["hello_timeout"], self.hello_timeout_handler
        )
        await self.conn.send_message(hello)

    def hello_timeout_handler(self):
        logger.error("Server hello timeout")
        self.conn.close()

    async def handle_hello(self, message):
        logger.debug("Received server hello message")
        if self.hello_timeout:
            self.hello_timeout.cancel()
            self.hello_timeout = None
        if message.server_hello.version != 1:
            logger.error("Unsupported server version %s", message.server_hello.version)
            self.conn.close()
            return
        try:
            del self.conn.message_handlers[MessageType.SERVERHELLO]
        except KeyError:
            logger.warn("Server hello message received more than once")
        else:
            self.conn.message_handlers[MessageType.COMMAND] = self.handle_command
            self.conn.message_handlers[MessageType.DATARESPONSE] = (
                self.handle_data_response
            )

    async def handle_command(self, message):
        cmdtype = message.command.type
        try:
            kw = json.loads(message.command.data)
        except json.JSONDecodeError:
            logger.error("Failed to decode command data")
            self.send_command_status(
                message.command.commandID,
                CommandStatus.Status.FAILURE,
                "Failed to decode command data",
            )
            return
        args = kw.pop("[args]", [])
        threading.Thread(
            target=self._run_command,
            args=(message.command.commandID, cmdtype, args, kw),
        ).start()

    def _run_command(self, commandID, cmdtype, args, kw):
        if cmdtype == "state":
            self.run_state(commandID, *args, _send_status=True, **kw)
            return
        try:
            self.send_command_status(
                commandID, CommandStatus.Status.PENDING, "", current=0, total=1
            )
            output, changed = self.run_command(cmdtype, args, kw)
            status = CommandStatus.Status.SUCCESS
            self.send_command_status(commandID, status, output, current=1, total=1)
        except Exception as e:
            output = "Failed to execute command:\n" + traceback.format_exc()
            changed = False
            status = CommandStatus.Status.FAILURE
            self.send_command_status(commandID, status, output)

    def run_command(self, cmdtype, args, kw):
        logger.debug("Preparing to run command %s", cmdtype)
        parts = cmdtype.split(".", 1)
        if (
            len(parts) != 2
            or not parts[0].isidentifier()
            or not parts[1].isidentifier()
        ):
            raise ValueError("Invalid command type")
        module_name, class_name = parts
        logger.debug("Looking for command module %s", module_name)
        try:
            module = importlib.import_module("pepper.commands." + module_name)
        except ImportError:
            logger.error("Command module not found %s", module_name)
            raise ValueError(f"Command module {module_name} not found")
        logger.debug("Looking for command class %s", class_name)
        try:
            command_class = getattr(module, class_name)
        except AttributeError:
            logger.error("Command class not found %s", class_name)
            raise ValueError(
                f"Command class {class_name} not found in module {module_name}"
            )
        cond = kw.pop("if", None)
        logger.debug("Checking command condition %r", cond)
        try:
            if not self.evaluate_condition(cond):
                logger.debug("Command condition not met for %s", cmdtype)
                return "Command condition not met", False
        except Exception as e:
            logger.error("Failed to evaluate condition %s", e, exc_info=1)
            raise
        logger.debug("Instantiating command %s", cmdtype)
        try:
            command = command_class(*args, **kw)
        except Exception as e:
            logger.error("Failed to instantiate command %s", e, exc_info=1)
            raise
        logger.debug("Running command %s", cmdtype)
        try:
            output, changed = command.ensure(self)
        except Exception as e:
            logger.error("Command failed %s", e, exc_info=1)
            raise
        logger.debug("Command %s", "changed" if changed else "did not change")
        logger.debug("Command output: %s", output)
        return output, changed

    def run_state(self, commandID, name="", _send_status=False):
        def error(msg):
            logger.error(msg)
            if _send_status:
                self.send_command_status(commandID, CommandStatus.Status.FAILED, msg)
            else:
                raise ValueError(msg)

        ok, data = self.request_data("state", name)
        if not ok:
            return error(f"Failed to retrieve state {name}: {data}")
        state = json.loads(data)
        if not isinstance(state, dict):
            return error(f"State {name} is not a dictionary")
        tasks = {}
        for key, st in state.items():
            if not isinstance(st, dict):
                return error(f"State {name} task {key} is not a dictionary")
            tasks[key] = Task(key, st, st.pop("require", None))
        try:
            sorted_tasks = topological_sort(tasks)
        except ValueError as e:
            return error(f"Failed to sort tasks: {e}")
        if _send_status:
            self.send_command_status(
                commandID,
                CommandStatus.Status.PENDING,
                "",
                current=0,
                total=len(sorted_tasks),
            )
        i = 0
        changed = False
        output = f"Running state {name}:\n"
        for task in sorted_tasks:
            data = task.data
            failed = False
            try:
                cmd_output, cmd_changed = self.run_command(data.pop("type"), [], data)
            except Exception as e:
                if not _send_status:
                    raise
                else:
                    failed = True
                    cmd_output = (
                        f"Failed to run task {task.name}:\n{traceback.format_exc()}"
                    )
                    cmd_changed = False
            if cmd_changed:
                changed = True
            output += f"\nRunning task {task.name}:\n{cmd_output}\n"
            i += 1
            if _send_status:
                self.send_command_status(
                    commandID,
                    (
                        CommandStatus.Status.FAILED
                        if failed
                        else CommandStatus.Status.PENDING
                    ),
                    cmd_output,
                    current=i,
                    total=len(sorted_tasks),
                )
            if failed:
                break
        else:
            if _send_status:
                self.send_command_status(
                    commandID, CommandStatus.Status.SUCCESS, output, current=i, total=i
                )
        return output, changed

    def send_command_status(self, command_id, status, output, current=1, total=1):
        message = Message()
        message.type = MessageType.COMMANDSTATUS
        message.status.commandID = command_id
        message.status.status = status
        message.status.data = output
        message.status.progress.current = current
        message.status.progress.total = total
        self.conn.queue_message(message)

    def request_data(self, dtype, data):
        message = Message()
        message.type = MessageType.DATAREQUEST
        with self.last_message_id_lock:
            message.data_request.requestID = self.last_message_id
            self.last_message_id += 1
        message.data_request.type = dtype
        message.data_request.data = data
        self.data_response_queues[message.data_request.requestID] = q = queue.Queue(1)
        self.conn.queue_message(message)
        try:
            response = q.get(True, self.config["data_request_timeout"])
        except queue.Empty:
            raise TimeoutError("Data request timed out")
        return response.data_response.ok, response.data_response.data

    async def handle_data_response(self, message):
        q = self.data_response_queues.get(message.data_response.requestID)
        if q is None:
            logger.error(
                "Data response for unknown request ID %s",
                message.data_response.requestID,
            )
            return
        q.put(message)

    def evaluate_condition(self, condition):
        if not condition:
            return True
        if isinstance(condition, dict) and len(condition) > 1:
            raise ValueError("Use a list for multiple conditions")
        if isinstance(condition, list):
            logger.debug("Evaluating all conditions in list: %r", condition)
            return all(self.evaluate_condition(c) for c in condition)
        if not isinstance(condition, dict):
            raise ValueError("Condition must be a single key-value pair")
        k = next(iter(condition))
        v = condition[k]
        logger.debug("Evaluating condition %r: %r", k, v)
        if k == "not":
            return not self.evaluate_condition(v)
        negate = False
        words = k.split()
        if words[0] == "not":
            negate = True
            words.pop(0)
        ctype = words.pop(0)
        logger.debug("Condition type: %s", ctype)
        if ctype == "true":
            if words:
                raise ValueError("Invalid condition name: {k!r}")
            if v is not None:
                raise ValueError("Condition true does not take a value")
            return not negate
        if ctype == "false":
            if words:
                raise ValueError("Invalid condition name: {k!r}")
            if v is not None:
                raise ValueError("Condition false does not take a value")
            return negate
        if ctype == "all":
            if words:
                raise ValueError("Invalid condition name: {k!r}")
            if not isinstance(v, list):
                raise ValueError("Value for all condition must be a list")
            return not negate if all(self.evaluate_condition(c) for c in v) else negate
        if ctype == "any":
            if words:
                raise ValueError("Invalid condition name: {k!r}")
            if not isinstance(v, list):
                raise ValueError("Value for any condition must be a list")
            return not negate if any(self.evaluate_condition(c) for c in v) else negate
        if ctype == "py":
            if words:
                raise ValueError("Invalid condition name: {k!r}")
            return not negate if eval(v) else negate
        if ctype == "cmd":
            retcodes = [0]
            if words:
                retcodes = [int(w) for w in words.pop(0).split(",")]
            if words:
                raise ValueError(f"Invalid condition name: {k!r}")
            if not isinstance(v, str):
                raise ValueError(
                    f"Invalid command condition value type: {type(v).__name__}"
                )
            success = False
            logger.debug("Running condition command: %s", v)
            try:
                rc = subprocess.call(v, shell=True)
                success = rc in retcodes
            except Exception as e:
                success = False
            return not negate if success else negate
        if ctype == "file":
            verb = "exists"
            if words:
                verb = words.pop(0)
            if words:
                raise ValueError(f"Invalid condition name: {k!r}")
            if verb == "exists":
                logger.debug("Checking if file exists: %s", v)
                return not negate if os.path.exists(v) else negate
            else:
                raise ValueError(f"Invalid file condition verb {verb}")
        logger.error("Invalid condition name: %s", k)
        raise ValueError(f"Invalid condition name: {k!r}")

    async def run(self):
        """Run the agent"""
        await self.connect()
        try:
            await self.conn.run()
        except asyncio.CancelledError:
            logger.info("Agent cancelled")
            pass
