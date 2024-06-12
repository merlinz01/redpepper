import enum

class MessageType(enum.Enum):
    UNSPECIFIED = 0
    CLIENTHELLO = 10
    SERVERHELLO = 11
    BYE = 12
    PING = 13
    PONG = 14
    COMMAND = 20
    COMMANDCANCEL = 21
    COMMANDPROGRESS = 22
    COMMANDRESULT = 23
    REQUEST = 30
    RESPONSE = 31

class Message:
    type: MessageType
    client_hello: "ClientHello"
    server_hello: "ServerHello"
    bye: "Bye"
    ping: "Ping"
    pong: "Pong"
    command: "Command"
    command_cancel: "CommandCancel"
    progress: "CommandProgress"
    result: "CommandResult"
    request: "Request"
    response: "Response"

    def ParseFromString(self, data: bytes) -> "Message": ...

class Bye:
    reason: str

class ClientHello:
    clientID: str
    auth: str

class ServerHello:
    version: int

class Ping:
    data: int

class Pong:
    data: int

class Command:
    commandID: int
    type: str
    data: str

class CommandCancel:
    commandID: int

class CommandResult:
    class Status(enum.Enum):
        UNSPECIFIED = 0
        SUCCESS = 1
        FAILED = 2
        CANCELLED = 3

    commandID: int
    status: Status
    changed: bool
    output: str

class CommandProgress:
    commandID: int
    current: int
    total: int

class Request:
    requestID: int
    name: str
    data: str

class Response:
    requestID: int
    success: bool
    data: str
