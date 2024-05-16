
Purpose: executing commands on remote machines
Connect using TLS with server name verification.
All messages have predefined behavior depending on the state of the connection.
UI decides whether or not to retry any command.

connect (client):
    send Hello with credentials
    set Hello timeout

receive Ping:
    send Pong.

receive Pong:
    cancel any ping timeout.

receive Hello (server):
    update connection state with remote ID.
    send Hello.

receive Hello (client):
    cancel Hello timeout

receive Bye:
    close connection.

receive Command (client) with commandID:
    send CommandStatus with commandID and progress 0.
    start command worker in separate thread.
        send DataNeeded if data needed
            wait for corresponding CommandData received.
        send multiple CommandStatus with relevant progress and commandID.
        send CommandDone with commandID when done

receive CommandStatus with commandID:
    log status in progress for commandID.
    notify UI.

receive CommandDone with commandID:
    log status done for commandID.
    remove commandID from pending commands.
    notify UI.

receive CancelCommand (client) with commandID:
    notify worker thread of cancellation.
    worker thread send CommandDone with commandID and cancelled.

receive DataNeeded:
    send CommandData with relevant data.

start command (UI):
    send Command with parameters and commandID set to auto-incremented value
    log status started for commandID
    add commandID to pending commands with generous timeout

cancel command (UI):
    send CancelCommand with commandID.

continually (server):
    if any pending command is past timeout:
        log status timeout for commandID.
        remove commandID from pending commands.
        notify UI.
    if pong timeout exists and is past:
        send Bye.
        close connection.
    if no pong timeout and last ping was X secs ago:
        send Ping.
        set reasonable pong timeout.
        record now as last ping.

continually (client):
    if pong timeout exists and is past:
        send Bye.
        close connection.
        reopen connection.
    if no pong timeout and last ping was X secs ago:
        send Ping.
        set reasonable pong timeout.
        record now as last ping.
    if hello timeout exists and is past:
        close connection.
        reopen connection.

on connection errors or invalid data received (server):
    close the connection.

on connection errors or invalid data received (client):
    close the connection.
    reconnect.
