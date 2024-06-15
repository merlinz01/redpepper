import json
import logging
import sqlite3
import time as time_module
from collections import deque

import trio

logger = logging.getLogger(__name__)


class EventBus:
    """A simple event bus that allows consumers to subscribe to events."""

    def __init__(self):
        self.consumers: dict[int, trio.MemorySendChannel] = {}
        self.most_recent = deque(maxlen=10)

    def add_consumer(self):
        send, recv = trio.open_memory_channel(10)
        self.consumers[id(recv)] = send
        for event in self.most_recent:
            try:
                send.send_nowait(event)
            except (trio.WouldBlock, trio.ClosedResourceError) as e:
                logger.warn("Event bus consumer queue full or closed: %s", e)
        return recv

    def remove_consumer(self, consumer):
        self.consumers.pop(id(consumer)).close()

    async def post(self, **kw):
        kw["time"] = time_module.time()
        self.most_recent.append(kw)
        for q in self.consumers.values():
            q.send_nowait(kw)


class CommandLog:
    """A persistent log of commands, ordered by their time."""

    # Someday this class's methods can be made more efficient
    # by shifting all database accesses to a background thread
    # via trio.to_thread.run_sync().
    # For Python <3.11 sqlite3 isn't thread-safe, so we can't do that.
    # Python 3.11's sqlite3 module has thread-safety features.

    INIT_SQL = """
    CREATE TABLE IF NOT EXISTS redpepper_commands (
        id INTEGER PRIMARY KEY NOT NULL,
        time REAL,
        agent TEXT,
        command TEXT,
        status INTEGER,
        changed BOOLEAN,
        progress_current INTEGER,
        progress_total INTEGER,
        output TEXT
    );
    """

    def __init__(self, filename):
        self.db = sqlite3.connect(filename)
        self.db.executescript(self.INIT_SQL)
        self.db.commit()

    async def command_started(self, ID, time, agent, command):
        self.db.execute(
            "INSERT INTO redpepper_commands (id, time, agent, command, status, changed, progress_current, progress_total, output) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (ID, time, agent, command, 0, False, 0, 0, ""),
        )
        self.db.commit()

    async def command_progressed(self, ID, progress_current, progress_total):
        self.db.execute(
            "UPDATE redpepper_commands SET progress_current = ?, progress_total = ? WHERE id = ?",
            (progress_current, progress_total, ID),
        )
        self.db.commit()

    async def command_finished(self, ID, status, changed, output):
        self.db.execute(
            "UPDATE redpepper_commands SET status = ?, changed = ?, output = ? WHERE id = ?",
            (status, changed, output, ID),
        )
        self.db.commit()

    async def purge(self, max_age):
        self.db.execute(
            "DELETE FROM redpepper_commands WHERE time < ?",
            (time_module.time() - max_age,),
        )
        self.db.commit()

    async def last(self, max):
        cursor = self.db.execute(
            "SELECT id, time, agent, command, status, changed, progress_current, progress_total, output"
            " FROM redpepper_commands ORDER BY time DESC LIMIT ?",
            (max,),
        )
        for row in cursor:
            yield {
                "id": row[0],
                "time": row[1],
                "agent": row[2],
                "command": json.loads(row[3]),
                "status": row[4],
                "changed": row[5],
                "progress_current": row[6],
                "progress_total": row[7],
                "output": row[8],
            }
            await trio.sleep(0)
