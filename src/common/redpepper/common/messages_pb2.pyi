from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

BYE: MessageType
CLIENTHELLO: MessageType
COMMAND: MessageType
COMMANDCANCEL: MessageType
COMMANDPROGRESS: MessageType
COMMANDRESULT: MessageType
DESCRIPTOR: _descriptor.FileDescriptor
PING: MessageType
PONG: MessageType
REQUEST: MessageType
RESPONSE: MessageType
SERVERHELLO: MessageType
UNSPECIFIED: MessageType

class Bye(_message.Message):
    __slots__ = ["reason"]
    REASON_FIELD_NUMBER: _ClassVar[int]
    reason: str
    def __init__(self, reason: _Optional[str] = ...) -> None: ...

class ClientHello(_message.Message):
    __slots__ = ["auth", "clientID"]
    AUTH_FIELD_NUMBER: _ClassVar[int]
    CLIENTID_FIELD_NUMBER: _ClassVar[int]
    auth: str
    clientID: str
    def __init__(self, clientID: _Optional[str] = ..., auth: _Optional[str] = ...) -> None: ...

class Command(_message.Message):
    __slots__ = ["commandID", "data", "type"]
    COMMANDID_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    commandID: int
    data: str
    type: str
    def __init__(self, commandID: _Optional[int] = ..., type: _Optional[str] = ..., data: _Optional[str] = ...) -> None: ...

class CommandCancel(_message.Message):
    __slots__ = ["commandID"]
    COMMANDID_FIELD_NUMBER: _ClassVar[int]
    commandID: int
    def __init__(self, commandID: _Optional[int] = ...) -> None: ...

class CommandProgress(_message.Message):
    __slots__ = ["commandID", "current", "message", "total"]
    COMMANDID_FIELD_NUMBER: _ClassVar[int]
    CURRENT_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    TOTAL_FIELD_NUMBER: _ClassVar[int]
    commandID: int
    current: int
    message: str
    total: int
    def __init__(self, commandID: _Optional[int] = ..., current: _Optional[int] = ..., total: _Optional[int] = ..., message: _Optional[str] = ...) -> None: ...

class CommandResult(_message.Message):
    __slots__ = ["changed", "commandID", "output", "status"]
    class Status(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    CANCELLED: CommandResult.Status
    CHANGED_FIELD_NUMBER: _ClassVar[int]
    COMMANDID_FIELD_NUMBER: _ClassVar[int]
    FAILED: CommandResult.Status
    OUTPUT_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    SUCCESS: CommandResult.Status
    UNSPECIFIED: CommandResult.Status
    changed: bool
    commandID: int
    output: str
    status: CommandResult.Status
    def __init__(self, commandID: _Optional[int] = ..., status: _Optional[_Union[CommandResult.Status, str]] = ..., changed: bool = ..., output: _Optional[str] = ...) -> None: ...

class Message(_message.Message):
    __slots__ = ["bye", "cancel", "client_hello", "command", "ping", "pong", "progress", "request", "response", "result", "server_hello", "type"]
    BYE_FIELD_NUMBER: _ClassVar[int]
    CANCEL_FIELD_NUMBER: _ClassVar[int]
    CLIENT_HELLO_FIELD_NUMBER: _ClassVar[int]
    COMMAND_FIELD_NUMBER: _ClassVar[int]
    PING_FIELD_NUMBER: _ClassVar[int]
    PONG_FIELD_NUMBER: _ClassVar[int]
    PROGRESS_FIELD_NUMBER: _ClassVar[int]
    REQUEST_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_FIELD_NUMBER: _ClassVar[int]
    RESULT_FIELD_NUMBER: _ClassVar[int]
    SERVER_HELLO_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    bye: Bye
    cancel: CommandCancel
    client_hello: ClientHello
    command: Command
    ping: Ping
    pong: Pong
    progress: CommandProgress
    request: Request
    response: Response
    result: CommandResult
    server_hello: ServerHello
    type: MessageType
    def __init__(self, type: _Optional[_Union[MessageType, str]] = ..., client_hello: _Optional[_Union[ClientHello, _Mapping]] = ..., server_hello: _Optional[_Union[ServerHello, _Mapping]] = ..., bye: _Optional[_Union[Bye, _Mapping]] = ..., ping: _Optional[_Union[Ping, _Mapping]] = ..., pong: _Optional[_Union[Pong, _Mapping]] = ..., command: _Optional[_Union[Command, _Mapping]] = ..., cancel: _Optional[_Union[CommandCancel, _Mapping]] = ..., progress: _Optional[_Union[CommandProgress, _Mapping]] = ..., result: _Optional[_Union[CommandResult, _Mapping]] = ..., request: _Optional[_Union[Request, _Mapping]] = ..., response: _Optional[_Union[Response, _Mapping]] = ...) -> None: ...

class Ping(_message.Message):
    __slots__ = ["data"]
    DATA_FIELD_NUMBER: _ClassVar[int]
    data: int
    def __init__(self, data: _Optional[int] = ...) -> None: ...

class Pong(_message.Message):
    __slots__ = ["data"]
    DATA_FIELD_NUMBER: _ClassVar[int]
    data: int
    def __init__(self, data: _Optional[int] = ...) -> None: ...

class Request(_message.Message):
    __slots__ = ["data", "name", "requestID"]
    DATA_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    REQUESTID_FIELD_NUMBER: _ClassVar[int]
    data: str
    name: str
    requestID: int
    def __init__(self, requestID: _Optional[int] = ..., name: _Optional[str] = ..., data: _Optional[str] = ...) -> None: ...

class Response(_message.Message):
    __slots__ = ["data", "requestID", "success"]
    DATA_FIELD_NUMBER: _ClassVar[int]
    REQUESTID_FIELD_NUMBER: _ClassVar[int]
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    data: str
    requestID: int
    success: bool
    def __init__(self, requestID: _Optional[int] = ..., success: bool = ..., data: _Optional[str] = ...) -> None: ...

class ServerHello(_message.Message):
    __slots__ = ["version"]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    version: int
    def __init__(self, version: _Optional[int] = ...) -> None: ...

class MessageType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
