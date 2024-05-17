import socket
import threading

messages = []

def sendrecv(msg):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect(("tcpbin.com", 4242))
        sock.sendall(f"message number {msg}\n".encode("ascii"))
        messages.append(sock.recv(1024).decode("utf-8"))

threads = [
    threading.Thread(target=sendrecv, args=(msg,))
    for msg in ["one", "two", "three", "four", "five"]
]
for t in threads:
    t.start()
for t in threads:
    t.join()
for msg in messages:
    print(f"Got back echo response: {msg}")



