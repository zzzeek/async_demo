import greenlet
import select
import socket

class event_loop(greenlet.greenlet):
    def run(self, socket_comms):
        comms_by_sock = {t.sock: t for t in socket_comms}

        while comms_by_sock:
            t_list = {
                "notstarted": (t_start := []), "reader": (t_reader := []),
                "writer": (t_writer := []), "done": (t_done := [])
            }
            for sock, t in comms_by_sock.items():
                t_list[t.mode].append(sock)

            if t_reader or t_writer:
                t_reader, t_writer, _ = select.select(t_reader, t_writer, [])

            for sock in t_start + t_reader + t_writer:
                comms_by_sock[sock].switch(self)
            for sock in t_done:
                del comms_by_sock[sock]

class socket_comm(greenlet.greenlet):
    def __init__(self, msg):
        self.mode = "notstarted"
        self.msg = msg
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def run(self, loop):
        self.sock.connect(("tcpbin.com", 4242))
        self.sock.setblocking(False)

        self.mode = "writer"
        tosend = f"message number {self.msg}\n".encode("ascii")
        while tosend:
            loop.switch()
            sent = self.sock.send(tosend)
            tosend = tosend[sent:]

        self.mode = "reader"; data = ""; result = ""
        while not result or (data and len(data) >= 1024):
            loop.switch()
            data = self.sock.recv(1024)
            result += data.decode("utf-8")

        print(f"Got back echo response: {result}")
        self.mode = "done"
        loop.switch()

event_loop().switch(
    [socket_comm(msg) for msg in ["one", "two", "three", "four", "five"]]
)
