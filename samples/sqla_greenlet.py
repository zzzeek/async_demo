import asyncio
from sqlalchemy.util  import greenlet_spawn, await_only

def sendrecv_implementation(msg):
    reader, writer = await_only(asyncio.open_connection("tcpbin.com", 4242))
    writer.write(f"message number {msg}\n".encode("ascii"))
    await_only(writer.drain())
    data = (await_only(reader.read(1024))).decode("utf-8")
    return data

async def sendrecv(msg):
    return await greenlet_spawn(sendrecv_implementation, msg)

async def main():
    messages = await asyncio.gather(
        *[
            sendrecv(msg) for msg in
            ["one", "two", "three", "four", "five"]
        ]
    )
    for msg in messages:
        print(f"Got back echo response: {msg}")

asyncio.run(main())



