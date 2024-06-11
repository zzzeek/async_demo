"""illustrates how a traditional sync-style SQLAlchemy API can be invoked
from both sync and async contexts"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import select, create_engine, literal
from sqlalchemy.util import greenlet_spawn
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import create_async_engine


def some_ordinary_function(argument):
    """a function that uses standard SQLAlchemy.   "engine" is assumed
    to be a global SQLAlchemy engine object (sync style).

    Standard SQLAlchemy ORM session patterns are used.

    """
    with Session(engine) as sess:
        result = sess.execute(select(literal(argument))).scalar()
    return result


def sync_front_api():
    """invoke the ordinary function directly."""

    result = some_ordinary_function("sync")
    print(f"result from sync: {result}")

async def async_front_api():
    """invoke the ordinary function from an async context, where
    it will be invoked within the event loop against an asyncio database
    driver.."""

    result = await greenlet_spawn(some_ordinary_function, "async")
    print(f"result from async: {result}")


if __name__ == "__main__":

    def run_the_sync_version():
        global engine
        engine = create_engine("sqlite+pysqlite:///file.db")

        sync_front_api()

    def run_the_async_version():
        global engine
        async_engine = create_async_engine("sqlite+aiosqlite:///file.db")
        engine = async_engine.sync_engine

        # event loop is initiated here
        asyncio.run(async_front_api())

    run_the_sync_version()
    run_the_async_version()

