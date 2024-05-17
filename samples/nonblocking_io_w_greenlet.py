# this doesnt work yet but it will, and it's going to be cool

import socket
import greenlet
import select

thingies = []
thingies_by_sock = {}


class loop(greenlet.greenlet):
    def run(self):
        while True:
            print("LOOP 1")
            for thingy in thingies:
                if thingy.mode == "none" and not thingy.dead:
                    thingy.switch()

            print("LOOP 2")
            readers, writers, _ = select.select(
                [
                    sock
                    for sock, t in thingies_by_sock.items()
                    if t.mode == "reader"
                ],
                [
                    sock
                    for sock, t in thingies_by_sock.items()
                    if t.mode == "writer"
                ],
                [],
            )
            print("LOOP 3")
            for writer in writers:
                thingies_by_sock[writer].switch()

            print("LOOP 4")
            for reader in readers:
                thingies_by_sock[reader].switch()


class thingy(greenlet.greenlet):
    mode = "none"

    def __init__(self, msg):
        self.msg = msg
        self.result = ""
        thingies.append(self)

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(("tcpbin.com", 4242))
        sock.setblocking(False)

        print("step1")
        self.send_writer(sock, f"message number {self.msg}\n".encode("ascii"))
        print("step2")
        self.receive_reader(sock)
        event_loop.switch()

    def send_writer(self, sock, msg):
        self.mode = "writer"
        thingies_by_sock[sock] = self
        event_loop.switch()

        while True:
            sent = sock.send(msg)
            self.msg = self.msg[sent:]
            if not self.msg:
                self.mode = "none"
                del thingies_by_sock[sock]
                break
            else:
                event_loop.switch()

    def receive_reader(self, sock):
        print(f"RECV FOR  {self.msg}")
        self.mode = "reader"
        thingies_by_sock[sock] = self
        event_loop.switch()

        while True:
            data = sock.recv(1024)
            if data:
                self.result += data.decode("utf-8")

            if not data or len(data) < 1024:
                print(f"Got back echo response: {self.result}")
                self.mode = "none"
                del thingies_by_sock[sock]
                break
            else:
                event_loop.switch()


event_loop = loop()

for msg in ["one", "two", "three", "four", "five"]:
    thingy(msg)
event_loop.switch()
