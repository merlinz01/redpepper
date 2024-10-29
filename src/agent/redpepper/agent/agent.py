"""RedPepper Agent"""

import base64
import importlib.util
import logging
import os
import ssl
import subprocess
import traceback
import uuid
from typing import Any

import trio

from redpepper.common.connection import Connection
from redpepper.common.errors import AuthenticationError, ProtocolError
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

from .config import AgentConfig

logger = logging.getLogger(__name__)
TRACE = 5


class OperationSpec:
    def __init__(self, name: str, data: dict[str, Any]):
        self.name = name
        self.data = data


class Agent:
    """RedPepper Agent"""

    config: AgentConfig
    """Agent configuration"""

    conn: Connection
    """Connection to the manager"""

    connected: trio.Event
    """Event that is set when the agent is connected"""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.data_slots: dict[str, Slot] = {}
        self.last_message_id = 100
        self.tls_context = config.load_tls_context(ssl.Purpose.SERVER_AUTH)
        self.connected = trio.Event()

    async def run(self) -> None:
        """Run the agent"""
        host = self.config.manager_host
        port = self.config.manager_port
        logger.info("Connecting to manager at %s:%s", host, port)
        stream = await trio.open_ssl_over_tcp_stream(
            host, port, ssl_context=self.tls_context
        )
        logger.debug("Performing SSL handshake with manager")
        await stream.do_handshake()
        logger.info("Connected to manager at %s:%s", host, port)
        self.conn = Connection(self.config, stream)
        await self.handshake()
        self.conn.message_handlers[get_type_code(Request)] = self.handle_request
        self.conn.message_handlers[get_type_code(Response)] = self.handle_response
        self.connected.set()
        await self.conn.run()

    async def shutdown(self) -> None:
        await self.conn.bye("shutting down")
        await self.conn.close()

    async def handshake(self) -> None:
        hello = AgentHello(
            id=self.config.agent_id,
            version=__version__,
            credentials=self.config.agent_secret.get_secret_value(),
        )
        logger.debug("Sending agent hello message to manager")
        await self.conn.send_message(hello)
        try:
            with trio.fail_after(self.config.hello_timeout):
                server_hello = await self.conn.receive_message_direct()
        except trio.TooSlowError as e:
            logger.error("Handshake timed out")
            await self.conn.close()
            raise AuthenticationError("Handshake timed out") from e
        if isinstance(server_hello, Bye):
            await self.conn.close()
            raise AuthenticationError(server_hello.reason)
        if not isinstance(server_hello, ManagerHello):
            await self.conn.close()
            raise ProtocolError(
                "Expected manager hello message, got %s" % server_hello.t
            )
        logger.debug(
            "Checking manager hello message with version %s",
            server_hello.version,
        )
        if server_hello.version != __version__:
            server_major = server_hello.version.split(".", 1)[0]
            agent_major = __version__.split(".", 1)[0]
            if server_major != agent_major:
                await self.conn.close()
                raise AuthenticationError("Incompatible server version")
            logger.warning(
                "Manager version %s does not match agent version %s; use at your own risk",
                server_hello.version,
                __version__,
            )

    async def handle_request(self, request: MessageType) -> None:
        assert isinstance(request, Request)
        cmdtype = request.method
        kw = request.params
        args = kw.pop("[args]", [])
        await trio.to_thread.run_sync(
            self._run_received_command,
            request.id,
            cmdtype,
            args,
            kw,
        )
        # TODO: to_thread.run_sync returns the return value of the function.
        # We should send the result back here instead of in the function.

    def _run_received_command(
        self, commandID: str, cmdtype: str, args: list, kw: dict
    ) -> None:
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
        self.send_command_result(commandID, result)

    def do_operation(self, cmdtype: str, args: list, kw: dict) -> Result:
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
        except ImportError:
            # If the module is not found, check the cached-modules directory
            cached_path = self.config.operation_modules_cache_dir / (
                module_name + ".py"
            )

            try:
                mtime = cached_path.stat().st_mtime
                size = cached_path.stat().st_size
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
        self,
        state_name: str,
        state_data: dict[str, dict | list | None],
        commandID: str | None = None,
    ) -> Result:
        # For now we can raise errors because we don't have any previous output to return.
        # Arrange the state entries into a list of OperationSpec objects
        tasks: list[OperationSpec] = []
        for state_task_name, state_definition in state_data.items():
            if isinstance(state_definition, list):
                for i, item in enumerate(state_definition, 1):
                    if not isinstance(item, dict):
                        raise TypeError(
                            f"State {state_data} task {state_task_name} item {i} is not a dictionary"
                        )
                    tasks.append(OperationSpec(f"{state_task_name} #{i}", item))
            elif isinstance(state_definition, dict):
                tasks.append(OperationSpec(state_task_name, state_definition))
            else:
                raise TypeError(
                    f"State {state_data} task {state_task_name} is not a dictionary or list"
                )

        # Task counter
        i = 0
        # Create a result to store information about the execution
        result = Result(state_name)
        # Send the initial status message
        if commandID is not None:
            self.send_command_progress(
                commandID, 0, len(tasks), f"Starting {state_name}..."
            )
        # Run the tasks
        for task in tasks:
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
                    commandID, i, len(tasks), f"{task.name} done"
                )
        # Return the result
        return result

    def send_command_progress(
        self, command_id: str, current: int = 1, total: int = 1, msg: str = ""
    ) -> None:
        message = Notification(
            type="command_progress",
            data={
                "command_id": command_id,
                "current": current,
                "total": total,
                "message": msg,
            },
        )
        self.conn.send_message_fromthread(message)

    def send_command_result(self, command_id: str, result: Result) -> None:
        # Success means that we have a result to return rather than a Python exception,
        # not necessarily that the operation itself was successful
        response = Response(
            id=command_id,
            success=True,
            data={
                "success": result.succeeded,
                "changed": result.changed,
                "output": str(result),
            },
        )
        self.conn.send_message_fromthread(response)

    def request(self, request_name: str, **kw) -> Any:
        self.last_message_id += 1
        request_id = uuid.uuid4().hex
        message = Request(id=request_id, method=request_name, params=kw)
        self.data_slots[message.id] = slot = Slot()
        self.conn.send_message_fromthread(message)
        response: MessageType = trio.from_thread.run(
            slot.get, self.config.data_request_timeout
        )
        assert isinstance(response, Response)
        if not response.success:
            raise RequestError(response.data)
        result = response.data
        return result

    async def handle_response(self, response: MessageType) -> None:
        assert isinstance(response, Response)
        logger.log(TRACE, "Received response for request %s", response.id)
        slot = self.data_slots.pop(response.id, None)
        if not slot:
            logger.error(
                "Data response for unknown request ID %s",
                response.id,
            )
            return
        await slot.set(response)

    def evaluate_condition(self, condition: Any) -> bool:
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
            except Exception:
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
