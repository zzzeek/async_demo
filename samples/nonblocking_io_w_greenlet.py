import socket
import greenlet
import select

writer_thingies = {}
reader_thingies = {}

class loop(greenlet.greenlet):
    def run(self):
        while True:
            print(f"LOOP, WRITERS {len(writer_thingies)} REDAERS {len(reader_thingies)}")
            readers, writers, _ = select.select(
                list(reader_thingies),
                list(writer_thingies),
                [],
            )
            for writer in writers:
                writer_thingies[writer].switch()
            for reader in readers:
                reader_thingies[reader].switch()
            go_greenlet.switch()


class thingy(greenlet.greenlet):
    def __init__(self, msg):
        self.msg = msg
        self.result = ""

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(("tcpbin.com", 4242))
        sock.setblocking(False)

        self.send_writer(sock, f"message number {self.msg}\n".encode("ascii"))
        self.receive_reader(sock)

    def send_writer(self,sock, msg):
        print(f"SEND {msg}")
        writer_thingies[sock] = self
        event_loop.switch()
        sent = sock.send(msg)
        self.msg = self.msg[sent:]
        if not self.msg:
            del writer_thingies[sock]
        else:
            event_loop.switch()

    def receive_reader(self,sock):
        print(f"RECV FOR  {self.msg}")
        reader_thingies[sock] = self
        event_loop.switch()
        data = sock.recv(1024)
        if data:
            self.result += data.decode("utf-8")

        if not data or len(data) < 1024:
            print(f"Got back echo response: {self.result}")
            del reader_thingies[sock]
        else:
            event_loop.switch()


event_loop = loop()

def go():
    thingies = [
        thingy(msg)
        for msg in ["one", "two", "three", "four", "five"]
    ]
    for thingy in thingies:
        thingy.switch()

go_greenlet = greenlet.greenlet(go)
go_greenlet.switch()

