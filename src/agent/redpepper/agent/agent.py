"""RedPepper Agent"""

import base64
import importlib.util
import json
import logging
import os
import ssl
import subprocess
import time
import traceback

import trio

from redpepper.common.connection import Connection
from redpepper.common.messages_pb2 import CommandResult, Message, MessageType
from redpepper.common.operations import Result
from redpepper.common.requests import RequestError
from redpepper.common.slot import Slot
from redpepper.common.tls import load_tls_context

from .config import load_agent_config
from .tasks import Task, topological_sort

logger = logging.getLogger(__name__)


class Agent:
    """RedPepper Agent"""

    def __init__(self, config=None, config_file=None):
        self.config = config or load_agent_config(config_file)
        self.conn: Connection
        self.data_slots: dict[int, Slot] = {}
        self.last_message_id = 100
        self.tls_context: ssl.SSLContext = load_tls_context(
            ssl.Purpose.SERVER_AUTH,
            self.config["tls_cert_file"],
            self.config["tls_key_file"],
            self.config["tls_key_password"],
            verify_mode=self.config["tls_verify_mode"],
            check_hostname=self.config["tls_check_hostname"],
            cafile=self.config["tls_ca_file"],
            capath=self.config["tls_ca_path"],
            cadata=self.config["tls_ca_data"],
        )

    async def connect(self):
        host = self.config["manager_host"]
        port = self.config["manager_port"]
        self.remote_address = (host, port)
        logger.info("Connecting to manager at %s:%s", host, port)
        stream = await trio.open_ssl_over_tcp_stream(
            host, port, ssl_context=self.tls_context
        )
        self.conn = Connection(
            stream, self.config["ping_timeout"], self.config["ping_interval"]
        )
        logger.debug("Performing SSL handshake with manager")
        await self.conn.stream.do_handshake()
        logger.info("Connected to manager at %s:%s", host, port)

    async def handshake(self):
        hello_slot = Slot()
        self.conn.message_handlers[MessageType.SERVERHELLO] = hello_slot.set  # type: ignore
        hello = Message()
        hello.type = MessageType.CLIENTHELLO
        hello.client_hello.clientID = self.config["agent_id"]
        hello.client_hello.auth = self.config["agent_secret"]
        logger.debug("Sending client hello message to manager")
        await self.conn.send_message(hello)
        try:
            server_hello: Message = await hello_slot.get(self.config["hello_timeout"])
        except trio.TooSlowError:
            logger.error("Handshake timed out")
            await self.conn.close()
            return
        finally:
            del self.conn.message_handlers[MessageType.SERVERHELLO]
        logger.debug(
            "Checking server hello message with version %s",
            server_hello.server_hello.version,
        )
        if server_hello.server_hello.version != 1:
            logger.error(
                "Unsupported server version %s", server_hello.server_hello.version
            )
            await self.conn.close()
            return
        self.conn.message_handlers[MessageType.COMMAND] = self.handle_command
        self.conn.message_handlers[MessageType.RESPONSE] = self.handle_response

    async def handle_command(self, message: Message):
        cmdtype = message.command.type
        try:
            kw = json.loads(message.command.data)
        except json.JSONDecodeError:
            logger.error("Failed to decode command data")
            self.send_command_result(
                message.command.commandID,
                CommandResult.Status.FAILED,
                False,
                "Failed to decode command data",
            )
            return
        args = kw.pop("[args]", [])
        await trio.to_thread.run_sync(
            self._run_received_command,
            message.command.commandID,
            cmdtype,
            args,
            kw,
        )

    def _run_received_command(self, commandID: int, cmdtype: str, args: list, kw: dict):
        try:
            if cmdtype == "state":
                if len(args) > 1:
                    raise ValueError("State command takes at most one argument")
                state_name = args[0] if args else ""
                state_data = self.request("stateDefinition", state_name=state_name)
                if not isinstance(state_data, dict):
                    raise ValueError(f"State {state_name} is not a dictionary")
                result = self.run_state(state_name, state_data, commandID=commandID)
            else:
                self.send_command_progress(commandID, 0, 1, f"Running {cmdtype}...")
                result = self.do_operation(cmdtype, args, kw)
                self.send_command_progress(commandID, 1, 1, f"Finished {cmdtype}")
        except Exception:
            logger.error("Failed to execute command", exc_info=True)
            result = Result(cmdtype)
            result.succeeded = False
            result += f"Failed to execute command {cmdtype!r}:"
            result += traceback.format_exc()
        status = (
            CommandResult.Status.SUCCESS
            if result.succeeded
            else CommandResult.Status.FAILED
        )
        self.send_command_result(commandID, status, result.changed, str(result))

    def do_operation(self, cmdtype: str, args: list, kw: dict):
        # In this function we can raise errors because callers will catch them
        logger.debug("Running operation %s", cmdtype)
        # Split the command type into module and class names
        parts = cmdtype.split(".", 1)
        if (
            len(parts) != 2
            or not parts[0].isidentifier()
            or not parts[1].isidentifier()
        ):
            raise ValueError("Invalid operation type")
        module_name, class_name = parts
        # Attempt to import the module
        logger.debug("Looking for operation module %s", module_name)
        try:
            module = importlib.import_module("redpepper.operations." + module_name)
        except ImportError as e:
            # If the module is not found, check the cached-modules directory
            cached_path = os.path.join(
                self.config["operation_modules_cache_dir"], module_name + ".py"
            )
            try:
                mtime = os.path.getmtime(cached_path)
                size = os.path.getsize(cached_path)
            except OSError:
                mtime = None
                size = None
            # Request the operation module status from the manager
            logger.debug("Requesting operation module %s", module_name)
            data = self.request(
                "operationModule",
                name=module_name,
                existing_mtime=mtime,
                existing_size=size,
            )
            if data["changed"]:
                logger.debug("Operation module %s has changed", module_name)
                # Save the module to the cache directory
                content = base64.b64decode(data["content"])
                with open(cached_path, "wb") as f:
                    f.write(content)
                os.utime(cached_path, (data["mtime"], data["mtime"]))
            # Load the module from the cache
            try:
                spec = importlib.util.spec_from_file_location(module_name, cached_path)
                if spec is None or spec.loader is None:
                    raise ImportError(f"Failed to load operation module {module_name}")
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
            except Exception as e:
                logger.error(
                    "Failed to load operation module %s", module_name, exc_info=True
                )
                raise ImportError(
                    f"Failed to load operation module {module_name}"
                ) from e
        # Get the operation class from the module
        logger.debug("Looking for operation class %s", class_name)
        op_class = getattr(module, class_name)
        # Check if the operation is prevented by a condition
        condition = kw.pop("if", None)
        logger.debug("Checking operation condition %r", condition)
        if not self.evaluate_condition(condition):
            logger.debug("Operation condition not met for %s, not running", cmdtype)
            result = Result(cmdtype)
            result.succeeded = True
            result += "Condition not met"
            return result
        # Instantiate the operation class with the given positional and keyword arguments
        logger.debug("Instantiating operation class %s", cmdtype)
        operation = op_class(*args, **kw)
        # Run the operation
        # Here's where all the fun stuff happens
        logger.debug("Running operation %s", cmdtype)
        result = operation.ensure(self)
        # Ensure the result is a Result object
        if not isinstance(result, Result):
            logger.warn("Operation returned a non-Result object: %r", result)
            result = Result(cmdtype)
            result.succeeded = False
            result += "Operation returned a non-Result object: %r" % result
        # Return the result
        logger.debug("Operation result: %s", result)
        return result

    def run_state(
        self, state_name: str, state_data: dict[str, dict], commandID: int | None = None
    ):
        # For now we can raise errors because we don't have any previous output to return.
        # Arrange the state entries into a list of Task objects
        tasks = {}
        for state_task_name, state_definition in state_data.items():
            if isinstance(state_definition, list):
                # Merge requirements from all items
                requirements = set()
                for i, item in enumerate(state_definition, 1):
                    if not isinstance(item, dict):
                        raise TypeError(
                            f"State {state_data} task {state_task_name} item {i} is not a dictionary"
                        )
                    req = item.pop("require", ())
                    if isinstance(req, str):
                        requirements.add(req)
                    else:
                        requirements.update(req)
                tasks[state_task_name] = Task(
                    state_task_name, state_definition, requirements
                )
            elif isinstance(state_definition, dict):
                requirements = state_definition.pop("require", ())
                if isinstance(requirements, str):
                    requirements = {requirements}
                tasks[state_task_name] = Task(
                    state_task_name, state_definition, set(requirements)
                )
            else:
                raise TypeError(
                    f"State {state_data} task {state_task_name} is not a dictionary or list"
                )

        # Sort the list of tasks according to their dependencies
        sorted_tasks = topological_sort(tasks)

        # Flatten task groups
        flattened_tasks = []
        for task in sorted_tasks:
            if isinstance(task.data, list):
                for i, subtaskdata in enumerate(task.data, 1):
                    flattened_tasks.append(Task(f"{task.name} #{i}", subtaskdata, None))
            else:
                flattened_tasks.append(task)

        # Task counter
        i = 0
        # Create a result to store information about the execution
        result = Result(state_name)
        # Send the initial status message
        if commandID is not None:
            self.send_command_progress(
                commandID, 0, len(flattened_tasks), f"Starting {state_name}..."
            )
        # Run the tasks
        for task in flattened_tasks:
            # Update the result with the operation name
            result += f"\nRunning state {task.name}:"
            # Extract the parameters
            kwargs = task.data
            cmdtype = kwargs.pop("type")
            onchange = kwargs.pop("onchange", None)
            # Run the operation
            try:
                cmd_result = self.do_operation(cmdtype, [], kwargs)
            except Exception:
                cmd_result = Result(task.name)
                cmd_result.fail(
                    f"Failed to execute state {task.name}:\n{traceback.format_exc()}"
                )
            # Update the result with output and success/changed status
            result.update(cmd_result)
            # Increment the task counter
            i += 1
            # Stop if the operation failed
            if not result.succeeded:
                break
            # Run the onchange operation if the operation succeeded and an onchange operation is defined
            if onchange and cmd_result.changed:
                onchange_name = task.name + " onchange"
                try:
                    onchange_result = self.run_state(
                        onchange_name, {onchange_name: onchange}
                    )
                except Exception:
                    onchange_result = Result(onchange_name)
                    onchange_result.fail(
                        f"Failed to execute state {onchange_name}:\n{traceback.format_exc()}"
                    )
                # Update the result with the onchange operation output
                result.update(onchange_result, raw_output=True)
                # Stop if the onchange operation failed
                if not result.succeeded:
                    break
            # Send the progress message
            if commandID is not None:
                self.send_command_progress(
                    commandID, i, len(flattened_tasks), f"{task.name} done"
                )
        # Return the result
        return result

    def send_command_progress(
        self, command_id: int, current: int = 1, total: int = 1, msg: str = ""
    ):
        message = Message()
        message.type = MessageType.COMMANDPROGRESS
        message.progress.commandID = command_id
        message.progress.current = current
        message.progress.total = total
        message.progress.message = msg
        self.conn.send_message_threadsafe(message)

    def send_command_result(
        self, command_id: int, status: CommandResult.Status, changed: bool, output: str
    ):
        message = Message()
        message.type = MessageType.COMMANDRESULT
        message.result.commandID = command_id
        message.result.status = status
        message.result.changed = changed
        message.result.output = output
        self.conn.send_message_threadsafe(message)

    def request(self, request_name: str, **kw):
        data = json.dumps(kw)
        message = Message()
        message.type = MessageType.REQUEST
        self.last_message_id += 1
        request_id = int(time.strftime("%Y%m%d%H%M%S")) * 1000 + self.last_message_id
        message.request.requestID = request_id
        message.request.name = request_name
        message.request.data = data
        self.data_slots[message.request.requestID] = slot = Slot()
        self.conn.send_message_threadsafe(message)
        response: Message = slot.get_threadsafe(self.config["data_request_timeout"])
        if not response.response.success:
            raise RequestError(response.response.data)
        result = response.response.data
        result = json.loads(result)
        return result

    async def handle_response(self, message: Message):
        logger.debug("Received response: %r", message.response)
        slot = self.data_slots.get(message.response.requestID, None)
        if not slot:
            logger.error(
                "Data response for unknown request ID %s",
                message.response.requestID,
            )
            return
        await slot.set(message)
        del self.data_slots[message.response.requestID]

    def evaluate_condition(self, condition):
        if condition is None:
            return True
        if isinstance(condition, bool):
            return condition
        if isinstance(condition, str):
            if condition.lower() == "true":
                return True
            elif condition.lower() == "false":
                return False
            raise ValueError("Invalid standalone condition name: {condition!r}")
        if isinstance(condition, dict) and len(condition) > 1:
            raise ValueError("Use a list for multiple conditions")
        if isinstance(condition, list):
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
                logger.error("Failed to run condition command: %s", v, exc_info=True)
                success = False
            return not negate if success else negate
        if ctype == "path":
            verb = "exists"
            if words:
                verb = words.pop(0)
            if words:
                raise ValueError(f"Invalid condition name: {k!r}")
            if verb == "exists":
                logger.debug("Checking if file exists: %s", v)
                return not negate if os.path.exists(v) else negate
            elif verb == "isfile":
                logger.debug("Checking if file is a regular file: %s", v)
                return not negate if os.path.isfile(v) else negate
            elif verb == "isdir":
                logger.debug("Checking if file is a directory: %s", v)
                return not negate if os.path.isdir(v) else negate
            elif verb == "islink":
                logger.debug("Checking if file is a symbolic link: %s", v)
                return not negate if os.path.islink(v) else negate
            else:
                raise ValueError(f"Invalid file condition verb {verb}")
        logger.error("Invalid condition name: %s", k)
        raise ValueError(f"Invalid condition name: {k!r}")

    async def run(self):
        """Run the agent"""
        await self.connect()
        async with trio.open_nursery() as nursery:
            nursery.start_soon(self.conn.run)
            nursery.start_soon(self.handshake)
