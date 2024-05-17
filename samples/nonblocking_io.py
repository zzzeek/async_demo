import socket
import select

socks = {}
for msg in ["one", "two", "three", "four", "five"]:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(("tcpbin.com", 4242))
    sock.setblocking(False)
    socks[sock] = {"socket": sock,"cmd": "write", "data_recv": "",
        "data_send": f"message number {msg}\n".encode("ascii"),
    }

while True:
    readers, writers, _ = select.select(
        [sock["socket"] for sock in socks.values() if sock["cmd"] == "read"],
        [sock["socket"] for sock in socks.values() if sock["cmd"] == "write"],
        [],
    )
    for writer in writers:
        sent = writer.send(socks[writer]["data_send"])
        socks[writer]["data_send"] = socks[writer]["data_send"][sent:]
        if not socks[writer]["data_send"]:
            socks[writer]["cmd"] = "read"

    for reader in readers:
        data = reader.recv(1024)
        if data:
            socks[reader]["data_recv"] += data.decode("utf-8")

        if not data or len(data) < 1024:
            print(f"Got back echo response: {socks[reader]['data_recv']}")
            socks[reader]["cmd"] = "done"

    if not any(sock["cmd"] != "done" for sock in socks.values()):
        break


