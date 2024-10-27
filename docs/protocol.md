# Communucation Protocol

This document describes the protocol used for communication between the Manager and Agents.

> The basic protocol provides much the same functionality as a WebSocket connection.
> It would be fairly simple to implement communication over WebSockets if such a need arises.

Connections are made using TLS over a normal TCP connection initiated by agents.
Messages are passed both directions over the connection.
Messages are encoded in MessagePack encoding prefixed with the message's 32-bit encoded length.
See [messages.py](/src/common/redpepper/common/messages.py) for the message definitions.

Ping messages are used for connection keep-alive.

All request/response flows should have timeouts. Retries of timed-out flows are not handled at the protocol level.

## Communication Flow

On startup (agent):

- Initiate connection to manager
- Send AgentHello
- Read ServerHello with timeout
  - If timeout, close connection
- Validate ServerHello as needed
  - If validation fails, send Bye and close connection
- Start listening for incoming messages and handle them as below

On connection received (manager):

- Read AgentHello with timeout
  - If timeout, close connection
- Authenticate agent based on information in AgentHello
  - If authentication fails, send Bye and close connection
- Send ServerHello
- Start listening for incoming messages and handle them as below

Periodically (both):

- Send Ping message
- Read Ping message with timeout
  - If timeout, close connection

Receive Request (both):

- Execute the request specified in the message
- Send Response with the request ID and the result of the request

Receive Response (both):

- Match the response to the request and return the result to the caller

Receive Notification (both):

- Handle the notification as needed without sending a response

Receive Bye (both):

- Close the connection
