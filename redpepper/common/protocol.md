# Protocol description

Connections are made using TLS over a normal TCP socket.
All messages have predefined behavior depending on the state of the connection.
The user decides whether or not to retry any command.
All request/response flows (should) have reasonable timeouts.

Connect (agent):
- send Hello with credentials
- set Hello timeout

Receive Ping:
- send Pong

Receive Pong:
- cancel any ping timeout

Receive Hello (manager):
- check authentication
    - if fails, send Bye
- update connection state with remote ID
- send server Hello

Receive Hello (agent):
- cancel Hello timeout

Receive Command (agent) with commandID:
- start command worker in separate thread.
    - send DataNeeded if data needed
        - wait for corresponding CommandData received.
    - send any relevant CommandStatus with progress and commandID.
    - send CommandStatus with commandID when done

Receive CommandStatus with commandID:
- log status for commandID
- notify user

Receive CancelCommand (agent) with commandID:
- notify worker thread of cancellation
- worker thread send CommandDone with commandID and cancelled

Receive DataNeeded (manager):
- send CommandData with relevant data

Start command (user):
- send Command with parameters and commandID set to auto-incremented value

Cancel command (UI):
- send CancelCommand with commandID

On connection errors or invalid data received (server) or Bye received:
- close the connection

On connection errors or invalid data received (agent) or Bye received:
- close the connection
- wait a bit
- reconnect
