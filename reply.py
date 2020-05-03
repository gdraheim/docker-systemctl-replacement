#! /usr/bin/python3 -u
import os
import sys
import socket
import time
try:
    import socketserver
except:
    import SocketServer
    socketserver = SocketServer

ADDR = '127.0.0.1'
PORT = 5005
BUFS = 32  # defaults to 1024
DATA = "foo"
FILE = "/tmp/{ppid}.sock"

def strips(text):
    if isinstance(text, bytes):
        text = text.decode("utf-8")
    return text.strip()
def utf8(text):
    if not isinstance(text, bytes):
        return text.encode("utf-8")
    return text

def serverINET():
    while True:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((ADDR, PORT))
        s.listen(1)
        #
        conn, addr = s.accept()
        print('Connection address:', addr)
        while True:
            data = conn.recv(BUFS)
            if not data: break
            print("received:", data)
            conn.send(utf8(strips(data).upper()))  # echo
        conn.close()

def serverINET6():
    while True:
        s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        s.bind((ADDR, PORT))
        s.listen(1)
        #
        conn, addr = s.accept()
        print('Connection address:', addr)
        while True:
            data = conn.recv(BUFS)
            if not data: break
            print("received:", data)
            conn.send(utf8(strips(data).upper()))  # echo
        conn.close()

class ServerTCP(socketserver.BaseRequestHandler):
     def handle(self):
          data = self.request.recv(BUFS)
          print("received:", data)
          self.request.sendall(utf8(strips(data).upper()))

def serverTCP():
    server = socketserver.TCPServer((ADDR, PORT), ServerTCP)
    print("server TCP", (ADDR, PORT))
    server.serve_forever()

class StreamServerTCP(socketserver.StreamRequestHandler):
     def handle(self):
          data = self.rfile.readline()
          print("received:", data)
          self.wfile.write(utf8(strips(data).upper()))

def streamTCP():
    server = socketserver.TCPServer((ADDR, PORT), StreamServerTCP)
    print("server TCP", (ADDR, PORT))
    server.serve_forever()

def sendTCP():
    if ADDR and ":" in ADDR:
        sendTCP6()
    else:
        sendTCP4()

def sendTCP4():
    reply=""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((ADDR, PORT))
        sock.sendall(utf8(DATA + "\n"))
        reply = sock.recv(BUFS)
    except Exception as e:
        reply=str(e)
    finally:
        sock.close()
    print("request:", strips(DATA))
    print("replied:", strips(reply))

def sendTCP6():
    reply=""
    sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    try:
        sock.connect((ADDR, PORT))
        sock.sendall(utf8(DATA + "\n"))
        reply = sock.recv(BUFS)
    except Exception as e:
        reply=str(e)
    finally:
        sock.close()
    print("request:", strips(DATA))
    print("replied:", strips(reply))

class ServerUDP(socketserver.BaseRequestHandler):
     def handle(self):
          data = self.request[0]
          sock = self.request[1]
          print("received:", data)
          sock.sendto(utf8(strips(data).upper()), self.client_address)

def serverUDP():
    server = socketserver.UDPServer((ADDR, PORT), ServerUDP)
    print("server UDP", (ADDR, PORT))
    server.serve_forever()

def sendUDP():
    reply=""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.sendto(utf8(DATA + "\n"), (ADDR, PORT))
        reply = sock.recv(BUFS)
    except Exception as e:
        reply=str(e)
    finally:
        # sock.close()
        pass
    print("request:", strips(DATA))
    print("replied:", strips(reply))

class ServerUNIX(socketserver.BaseRequestHandler):
    def handle(self):
          data = self.request.recv(BUFS)
          print("received:", data)
          self.request.sendall(utf8(strips(data).upper()))

def serverUNIX():
    ppid = os.getpid()
    path = FILE.format(**locals())
    dir_path = os.path.dirname(path)
    if not os.path.isdir(dir_path):
        print("mkdir", dir_path)
        os.makedirs(dir_path)
    server = socketserver.UnixStreamServer(path, ServerUNIX)
    try:
        print("server UNIX", path)
        server.serve_forever()
    finally:
        server.shutdown()
        os.remove(path)

class SocketUnixStreamServer(socketserver.UnixStreamServer):
    # https://ahmet2mir.eu/blog/2015/python_ssl_sockets_and_systemd_activation/
    def server_bind(self):
        LISTEN_FDS = int(os.environ.get("LISTEN_FDS", 0))
        LISTEN_PID = os.environ.get("LISTEN_PID", None) or os.getpid()
        print("LISTEN_FDS:", str(LISTEN_FDS))
        print("LISTEN_PID:", str(LISTEN_PID))
        if LISTEN_FDS == 0:
            socketserver.UnixStreamServer.server_bind(self)
        else:
            print("rebind socket")
            print("address_family:", str(self.address_family))
            print("socket_type:", str(self.socket_type))
            self.socket = socket.fromfd(3, self.address_family, self.socket_type)

def socketUNIX():
    ppid = os.getpid()
    path = FILE.format(**locals())
    if not os.path.isdir(dir_path):
        print("mkdir", dir_path)
        os.makedirs(dir_path)
    server = SocketUnixStreamServer(path, ServerUNIX)
    try:
        print("server", path)
        server.serve_forever()
    finally:
        server.shutdown()
        os.remove(path)

def sendUNIX():
    ppid = os.getpid()
    path = FILE.format(**locals())
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        sock.connect(path)
        sock.send(utf8(DATA + "\n"))
        reply = sock.recv(BUFS)
    except Exception as e:
        reply=str(e)
    finally:
        sock.close()
    print("request:", strips(DATA))
    print("replied:", strips(reply))

class SocketTCPServer(socketserver.TCPServer):
    def server_bind(self):
        LISTEN_FDS = int(os.environ.get("LISTEN_FDS", 0))
        LISTEN_PID = os.environ.get("LISTEN_PID", None) or os.getpid()
        print("LISTEN_FDS:", str(LISTEN_FDS))
        print("LISTEN_PID:", str(LISTEN_PID))
        if LISTEN_FDS == 0:
            socketserver.TCPServer.server_bind(self)
        else:
            print("rebind socket")
            print("address_family:", str(self.address_family))
            print("socket_type:", str(self.socket_type))
            self.socket = socket.fromfd(3, self.address_family, self.socket_type)

def socketTCP():
    ppid = os.getpid()
    server = SocketTCPServer((ADDR, PORT), ServerTCP)
    try:
        print("server", path)
        server.serve_forever()
    finally:
        server.shutdown()

class SocketUDPServer(socketserver.UDPServer):
    def server_bind(self):
        LISTEN_FDS = int(os.environ.get("LISTEN_FDS", 0))
        LISTEN_PID = os.environ.get("LISTEN_PID", None) or os.getpid()
        print("LISTEN_FDS:", str(LISTEN_FDS))
        print("LISTEN_PID:", str(LISTEN_PID))
        if LISTEN_FDS == 0:
            socketserver.TCPServer.server_bind(self)
        else:
            print("rebind socket")
            print("address_family:", str(self.address_family))
            print("socket_type:", str(self.socket_type))
            self.socket = socket.fromfd(3, self.address_family, self.socket_type)

def socketUDP():
    ppid = os.getpid()
    server = SocketUDPServer((ADDR, PORT), ServerUDP)
    try:
        print("server", path)
        server.serve_forever()
    finally:
        server.shutdown()

def echo():
    for i in range(100):
        data = sys.stdin.read(BUFS)
        time.sleep(0.2)
        sys.stdout.write(strips(data).upper())
        sys.stdout.write("\n")

def socat():
    ppid = os.getpid()
    path = FILE.format(**locals())
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    try:
        sock.connect(path)
        for i in range(100):
            data = sys.stdin.read(BUFS)
            time.sleep(0.2)
            if not data:
                break
            sock.send(utf8(data))
    finally:
        sock.close()

if __name__ == "__main__":
    from optparse import OptionParser
    o = OptionParser("%prog prog [options]...")
    o.add_option("-p","--port", metavar="PORT", default=PORT,
       help="use different port [%default]")
    o.add_option("-a", "--addr", metavar="ADDR", default=ADDR,
       help="use different addr [%default]")
    o.add_option("-f", "--file", metavar="FILE", default=FILE,
       help="use different sock file [%default]")
    o.add_option("-s", "--send", metavar="DATA", default=DATA,
       help="use different send data [%default]")
    o.add_option("-b", "--bufs", metavar="size", default=BUFS,
       help="use different bufs size [%default]")
    o.add_option("-d", "--debug", action="count", default=0,
       help="increase debug level [%default]")
    o.add_option("-v", "--verbose", action="count", default=0,
       help="increase logging level [%default]")
    opt, args = o.parse_args()
    PORT = int(opt.port)
    ADDR = opt.addr
    FILE = opt.file
    DATA = opt.send
    BUFS = int(opt.bufs)
    for arg in args:
        if arg.startswith("UNIX-CLIENT:"):
            FILE=arg[len("UNIX-CLIENT:"):]
            arg = "socat"
        if arg in globals():
            func = globals()[arg]
            if callable(func):
                func()
