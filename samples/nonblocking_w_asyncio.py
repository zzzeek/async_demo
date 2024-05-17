import asyncio


async def sendrecv(msg):
    reader, writer = await asyncio.open_connection("tcpbin.com", 4242)
    writer.write(f"message number {msg}\n".encode("ascii"))
    await writer.drain()
    data = (await reader.read(1024)).decode("utf-8")
    return data


async def main():
    messages = await asyncio.gather(
        *[sendrecv(msg) for msg in ["one", "two", "three", "four", "five"]]
    )
    for msg in messages:
        print(f"Got back echo response: {msg}")


asyncio.run(main())
