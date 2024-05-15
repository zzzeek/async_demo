import socket
import threading

socks = {}
for msg in ["one", "two", "three", "four", "five"]:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(("tcpbin.com", 4242))
    socks[sock] = {
        "socket": sock,
        "data_send": f"message number {msg}\n".encode("ascii"),
        "data_recv": "",
    }

def sendrecv(rec):
    rec["socket"].sendall(rec["data_send"])
    rec["data_recv"] = rec["socket"].recv(1024).decode("utf-8")

threads = [
    threading.Thread(target=sendrecv, args=(rec,)) for rec in socks.values()
]
for t in threads:
    t.start()
for t in threads:
    t.join()
for rec in socks.values():
    print(f"Got back echo response: {rec['data_recv']}")
