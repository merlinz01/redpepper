from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class MessageType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    UNSPECIFIED: _ClassVar[MessageType]
    CLIENTHELLO: _ClassVar[MessageType]
    SERVERHELLO: _ClassVar[MessageType]
    BYE: _ClassVar[MessageType]
    PING: _ClassVar[MessageType]
    PONG: _ClassVar[MessageType]
    COMMAND: _ClassVar[MessageType]
    COMMANDCANCEL: _ClassVar[MessageType]
    COMMANDPROGRESS: _ClassVar[MessageType]
    COMMANDRESULT: _ClassVar[MessageType]
    REQUEST: _ClassVar[MessageType]
    RESPONSE: _ClassVar[MessageType]
UNSPECIFIED: MessageType
CLIENTHELLO: MessageType
SERVERHELLO: MessageType
BYE: MessageType
PING: MessageType
PONG: MessageType
COMMAND: MessageType
COMMANDCANCEL: MessageType
COMMANDPROGRESS: MessageType
COMMANDRESULT: MessageType
REQUEST: MessageType
RESPONSE: MessageType

class Message(_message.Message):
    __slots__ = ("type", "client_hello", "server_hello", "bye", "ping", "pong", "command", "cancel", "progress", "result", "request", "response")
    TYPE_FIELD_NUMBER: _ClassVar[int]
    CLIENT_HELLO_FIELD_NUMBER: _ClassVar[int]
    SERVER_HELLO_FIELD_NUMBER: _ClassVar[int]
    BYE_FIELD_NUMBER: _ClassVar[int]
    PING_FIELD_NUMBER: _ClassVar[int]
    PONG_FIELD_NUMBER: _ClassVar[int]
    COMMAND_FIELD_NUMBER: _ClassVar[int]
    CANCEL_FIELD_NUMBER: _ClassVar[int]
    PROGRESS_FIELD_NUMBER: _ClassVar[int]
    RESULT_FIELD_NUMBER: _ClassVar[int]
    REQUEST_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_FIELD_NUMBER: _ClassVar[int]
    type: MessageType
    client_hello: ClientHello
    server_hello: ServerHello
    bye: Bye
    ping: Ping
    pong: Pong
    command: Command
    cancel: CommandCancel
    progress: CommandProgress
    result: CommandResult
    request: Request
    response: Response
    def __init__(self, type: _Optional[_Union[MessageType, str]] = ..., client_hello: _Optional[_Union[ClientHello, _Mapping]] = ..., server_hello: _Optional[_Union[ServerHello, _Mapping]] = ..., bye: _Optional[_Union[Bye, _Mapping]] = ..., ping: _Optional[_Union[Ping, _Mapping]] = ..., pong: _Optional[_Union[Pong, _Mapping]] = ..., command: _Optional[_Union[Command, _Mapping]] = ..., cancel: _Optional[_Union[CommandCancel, _Mapping]] = ..., progress: _Optional[_Union[CommandProgress, _Mapping]] = ..., result: _Optional[_Union[CommandResult, _Mapping]] = ..., request: _Optional[_Union[Request, _Mapping]] = ..., response: _Optional[_Union[Response, _Mapping]] = ...) -> None: ...

class Bye(_message.Message):
    __slots__ = ("reason",)
    REASON_FIELD_NUMBER: _ClassVar[int]
    reason: str
    def __init__(self, reason: _Optional[str] = ...) -> None: ...

class ClientHello(_message.Message):
    __slots__ = ("clientID", "auth")
    CLIENTID_FIELD_NUMBER: _ClassVar[int]
    AUTH_FIELD_NUMBER: _ClassVar[int]
    clientID: str
    auth: str
    def __init__(self, clientID: _Optional[str] = ..., auth: _Optional[str] = ...) -> None: ...

class ServerHello(_message.Message):
    __slots__ = ("version",)
    VERSION_FIELD_NUMBER: _ClassVar[int]
    version: int
    def __init__(self, version: _Optional[int] = ...) -> None: ...

class Ping(_message.Message):
    __slots__ = ("data",)
    DATA_FIELD_NUMBER: _ClassVar[int]
    data: int
    def __init__(self, data: _Optional[int] = ...) -> None: ...

class Pong(_message.Message):
    __slots__ = ("data",)
    DATA_FIELD_NUMBER: _ClassVar[int]
    data: int
    def __init__(self, data: _Optional[int] = ...) -> None: ...

class Command(_message.Message):
    __slots__ = ("commandID", "type", "data")
    COMMANDID_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    commandID: int
    type: str
    data: str
    def __init__(self, commandID: _Optional[int] = ..., type: _Optional[str] = ..., data: _Optional[str] = ...) -> None: ...

class CommandCancel(_message.Message):
    __slots__ = ("commandID",)
    COMMANDID_FIELD_NUMBER: _ClassVar[int]
    commandID: int
    def __init__(self, commandID: _Optional[int] = ...) -> None: ...

class CommandResult(_message.Message):
    __slots__ = ("commandID", "status", "changed", "output")
    class Status(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        UNSPECIFIED: _ClassVar[CommandResult.Status]
        SUCCESS: _ClassVar[CommandResult.Status]
        FAILED: _ClassVar[CommandResult.Status]
        CANCELLED: _ClassVar[CommandResult.Status]
    UNSPECIFIED: CommandResult.Status
    SUCCESS: CommandResult.Status
    FAILED: CommandResult.Status
    CANCELLED: CommandResult.Status
    COMMANDID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    CHANGED_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_FIELD_NUMBER: _ClassVar[int]
    commandID: int
    status: CommandResult.Status
    changed: bool
    output: str
    def __init__(self, commandID: _Optional[int] = ..., status: _Optional[_Union[CommandResult.Status, str]] = ..., changed: bool = ..., output: _Optional[str] = ...) -> None: ...

class CommandProgress(_message.Message):
    __slots__ = ("commandID", "current", "total", "message")
    COMMANDID_FIELD_NUMBER: _ClassVar[int]
    CURRENT_FIELD_NUMBER: _ClassVar[int]
    TOTAL_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    commandID: int
    current: int
    total: int
    message: str
    def __init__(self, commandID: _Optional[int] = ..., current: _Optional[int] = ..., total: _Optional[int] = ..., message: _Optional[str] = ...) -> None: ...

class Request(_message.Message):
    __slots__ = ("requestID", "name", "data")
    REQUESTID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    requestID: int
    name: str
    data: str
    def __init__(self, requestID: _Optional[int] = ..., name: _Optional[str] = ..., data: _Optional[str] = ...) -> None: ...

class Response(_message.Message):
    __slots__ = ("requestID", "success", "data")
    REQUESTID_FIELD_NUMBER: _ClassVar[int]
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    requestID: int
    success: bool
    data: str
    def __init__(self, requestID: _Optional[int] = ..., success: bool = ..., data: _Optional[str] = ...) -> None: ...
