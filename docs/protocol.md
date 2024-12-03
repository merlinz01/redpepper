# Communucation Protocol

This document describes the protocol used for communication between the Manager and Agents.

## Message Transport

The protocol uses a simple bidirectional message transport.
This is intended to be somewhat generic and could be replaced with a different message transport if needed (e.g. WebSockets, message queues, etc.).

The default message transport is implemented using TLS-encrypted TCP sockets.
Messages are passed back and forth as binary blobs prefixed with the message's 32-bit encoded length.

## Message Encoding

Messages are encoded as MessagePack dicts with a type field which determines both the semantics and the accepted message schema.
See [messages.py](/src/common/redpepper/common/messages.py) for the schema definitions.

## Message Types

AgentHello and ManagerHello messages are used for initial connection setup.

Ping and Pong messages are used for connection keep-alive.

Request and Response messages are used for asynchronous request/response communication.

Notification messages are used for notifications which do not require a response.

Bye messages are used to close the connection gracefully.

## Communication Flow

On startup (agent):

- Initiate connection to manager
- Send AgentHello
- Wait for ManagerHello with timeout
  - If timeout, close connection
- Validate ManagerHello details as needed
  - If validation fails, send Bye and close connection
- Start listening for incoming requests and notifications

On connection received (manager):

- Wait for AgentHello with timeout
  - If timeout, close connection
- Authenticate agent based on information in AgentHello
  - If authentication fails, send Bye and close connection
- Send ManagerHello
- Start listening for incoming messages and notifications

Periodically:

- Send Ping message
- Wait for Ping message with timeout
  - If timeout, close connection

Receive Request:

- Execute the request specified in the message
- Send Response with the request ID and the result of the request

Receive Response:

- Match the response to the request and return the result to the caller

Receive Notification:

- Handle the notification as needed without sending a response

Receive Bye:

- Close the connection
