import json
import logging
import sqlite3
import time as time_module

import trio

logger = logging.getLogger(__name__)


class Event(dict):
    def __init__(self, time=None, id=None, **kw):
        self.update(kw)
        if time is None:
            time = time_module.time()
        self["time"] = time
        self["id"] = id

    @property
    def time(self):
        return self["time"]

    @property
    def id(self):
        return self["id"]

    def serialize(self):
        d = self.copy()
        if d["id"] is None:
            del d["id"]
        return json.dumps(d)


class EventLog:
    """A persistent log of events, ordered by their time."""

    # Someday this class's methods can be made more efficient
    # by shifting all database accesses to a background thread
    # via trio.to_thread.run_sync().
    # For Python <3.11 sqlite3 isn't thread-safe, so we can't do that.
    # Python 3.11's sqlite3 module has thread-safety features.

    INIT_SQL = """
    CREATE TABLE IF NOT EXISTS redpepper_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        time REAL,
        data TEXT
    )
    """

    def __init__(self, filename):
        self.db = sqlite3.connect(filename)
        self.db.execute(self.INIT_SQL)
        self.db.commit()
        self.consumers = {}

    def add_consumer(self):
        send, recv = trio.open_memory_channel(5)
        self.consumers[id(recv)] = send
        return recv

    def remove_consumer(self, consumer):
        del self.consumers[id(consumer)]

    def add_sync(self, event):
        logger.debug("Adding event: %r", event)
        c = self.db.execute(
            "INSERT INTO redpepper_events (time, data) VALUES (?, ?) RETURNING id",
            (event.time, event.serialize()),
        )
        event["id"] = c.fetchone()[0]
        self.db.commit()
        for q in self.consumers.values():
            q: trio.MemorySendChannel
            q.send_nowait(event)

    async def add(self, event):
        self.add_sync(event)

    async def add_event(self, **kw):
        await self.add(Event(**kw))

    def purge_sync(self, max_age):
        self.db.execute(
            "DELETE FROM redpepper_events WHERE time < ?",
            (time_module.time() - max_age,),
        )
        self.db.commit()

    async def purge(self, max_age):
        self.purge_sync(max_age)

    async def __aiter__(self):
        cursor = self.db.execute(
            "SELECT id, data FROM redpepper_events ORDER BY time DESC"
        )
        for row in cursor:
            kw = json.loads(row[1])
            kw["id"] = row[0]
            yield Event(**kw)
            await trio.sleep(0)

    async def since(self, time):
        cursor = self.db.execute(
            "SELECT id, data FROM redpepper_events WHERE time >= ? ORDER BY time DESC",
            (time,),
        )
        for row in cursor:
            kw = json.loads(row[1])
            kw["id"] = row[0]
            yield Event(**kw)
            await trio.sleep(0)

    async def between(self, start_time, end_time):
        cursor = self.db.execute(
            "SELECT id, data FROM redpepper_events WHERE time >= ? AND time <= ? ORDER BY time DESC",
            (start_time, end_time),
        )
        for row in cursor:
            kw = json.loads(row[1])
            kw["id"] = row[0]
            yield Event(**kw)
            await trio.sleep(0)
