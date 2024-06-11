# Communucation Protocol

This document describes the protocol used for communication between the Manager and Agents.

> The foundation of this protocol has much in common with WebSockets;
> I believe it would be fairly simple to implement communication
> over WebSockets if need be.

## General

Connections are made using TLS over a normal TCP connection initiated by agents.

Messages are passed both directions over the connection.

Messages are encoded in Protobuf encoding prefixed with the message's 32-bit encoded length.
See `redpepper/common/messages.proto` for the message definitions.

Ideally, all messages should have predefined behavior depending on the state of the connection.

Some messages represent a request/response flow. Others are one-way notifications.

All request/response flows (should) have reasonable timeouts.

Ping and Pong messages are used for connection keep-alive.

The user decides whether or not to retry any command.

## Event handling

On startup (agent):

- send ClientHello with credentials
- set ServerHello timeout

Receive ClientHello (manager):

- check authentication
  - if fails, send Bye
- update connection state with agent ID
- send ServerHello

Receive ServerHello (agent):

- cancel ServerHello timeout
- prepare to receive Command messages

Periodically:

- send Ping
- set ping timeout

Receive Ping:

- send Pong

Receive Pong:

- cancel any ping timeout

Receive Command (agent):

- start command worker in separate thread.
  - send DataRequest if data is needed
    - wait for corresponding DataResponse received.
  - send any relevant CommandProgress with progress and command ID.
  - send CommandResult with command ID and results when done

Receive CommandProgress (manager):

- log event

Receive CommandResult (manager):

- log event

Receive CommandCancel (agent):

- notify worker thread of cancellation
- worker thread send CommandDone with command ID and results so far

Receive DataRequest (manager):

- send DataResponse with relevant data

Start command (user):

- send Command with specified parameters and command ID set to auto-incremented value

Cancel command (user):

- send CommandCancel with commandID

On connection errors or invalid data received or Bye received (server):

- close the connection

On connection errors or invalid data received or Bye received (agent):

- close the connection
- wait a bit
- reconnect
