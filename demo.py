import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import select



async def coro1(conn, value):
    result = await conn.execute(select(value))
    print(f"RESULT: {result.scalar()}")

async def coro2(conn, value):
    result = await conn.execute(select(value))
    print(f"RESULT: {result.scalar()}")


async def go_async():
    e = create_async_engine("sqlite+aiosqlite:///file.db", echo='debug')

    conn1 = await e.execution_options(logging_token="coroutine 1").connect()
    conn2 = await e.execution_options(logging_token="coroutine 2").connect()

    await asyncio.gather(coro1(conn1, 1), coro2(conn2, 2))


from sqlalchemy_asyncio_demo import Demo

Demo("coro1", "coro2").show_methods(
    ("sqlalchemy/util/.*concurrency", {"await_only", "greenlet_spawn"}),
    ("sqlalchemy/ext/asyncio/engine", {"execute"}),
    ("sqlalchemy/engine/base.py", {"execute", "_exec_single_context"}),
    ("sqlalchemy/engine/default.py", {"do_execute"}),
    ("sqlalchemy/dialects/sqlite/aiosqlite.py", {"execute"}),
    ("aiosqlite/", {"cursor", "execute"}),
    ("demo.py", None)
).start()

asyncio.run(go_async())
