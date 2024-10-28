from typing import Annotated, Any, Literal, TypeAlias, Union

from pydantic import BaseModel, Field, TypeAdapter


class AgentHello(BaseModel):
    """Message sent by the Agent to the Manager immediately after connecting"""

    t: Literal[10] = 10

    id: str
    """Agent ID"""
    version: str
    """Version of the Agent"""
    credentials: str
    """Authentication credentials"""


class ManagerHello(BaseModel):
    """Message sent by the Manager to the Agent immediately after connecting"""

    t: Literal[11] = 11

    version: str
    """Version of the Manager"""


class Ping(BaseModel):
    """Ping message for connection keep-alive"""

    t: Literal[12] = 12

    data: int
    """Data to be echoed back"""


class Pong(BaseModel):
    """Pong message for connection keep-alive"""

    t: Literal[13] = 13

    data: int
    """Data echoed back"""


class Bye(BaseModel):
    """Message sent by either side to indicate disconnection"""

    t: Literal[14] = 14

    reason: str
    """Reason for disconnection"""


class Request(BaseModel):
    """Request message"""

    t: Literal[20] = 20

    id: str
    """Request ID"""
    method: str
    """Method name"""
    params: dict[str, Any]
    """Method parameters"""


class Response(BaseModel):
    """Response message"""

    t: Literal[21] = 21

    id: str
    """Request ID"""
    success: bool
    """Whether the request was successful"""
    data: Any
    """Returned data if successful, exception string if not"""


class Notification(BaseModel):
    """Notification message"""

    t: Literal[22] = 22

    type: str
    """Notification type"""
    data: Any
    """Notification data"""


MessageType: TypeAlias = Union[
    Ping,
    Pong,
    Request,
    Response,
    Notification,
    AgentHello,
    ManagerHello,
    Bye,
]
Message = TypeAdapter(
    Annotated[
        MessageType,
        Field(discriminator="t"),
    ]
)


def get_type_code(type: Any) -> int:
    """
    Get the type code of a message type, since Pydantic eats the class attribute
    """
    return type.model_fields["t"].default
