import socket
import threading
import json

class PeerNode:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port

        self.connected_peers = {}        # peer_id → (ip, port, socket)
        self.pending_requests = []       # list of (ip,port)
        self.messages = []               # store messages for UI

    def run(self):
        print(f"[PeerNode] Listening on {self.ip}:{self.port}")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self.ip, self.port))
        s.listen(10)

        while True:
            conn, addr = s.accept()
            threading.Thread(target=self.handle_conn, args=(conn, addr)).start()

    def handle_conn(self, conn, addr):
        raw = conn.recv(4096).decode()
        if not raw:
            return

        try:
            data = json.loads(raw)
        except:
            return

        action = data.get("action")

        if action == "connect-request":
            self.pending_requests.append(data)
            print("[PeerNode] Incoming connect request from", data["from"])

        elif action == "connect-accept":
            peer_id = data["from"]
            host = data["host"]
            port = data["port"]
            self.connected_peers[peer_id] = (host, port, None)
            print("[PeerNode] Connection accepted by", peer_id)

        elif action == "message":
            msg = data["message"]
            self.messages.append((data["from"], msg))
            print("[PeerNode] New P2P message:", msg)

        elif action == "broadcast":
            msg = data["message"]
            sender = data.get("from", "unknown")
            self.messages.append(("BROADCAST", sender, msg))
            print("[PeerNode] Broadcast received from", sender, ":", msg)

    def request_connect(self, target_ip, target_port, my_id):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((target_ip, target_port))
            pkt = {
                "action": "connect-request",
                "from": my_id,
                "host": self.ip,
                "port": self.port
            }
            s.sendall(json.dumps(pkt).encode())
            s.close()
        except:
            pass

    def accept_request(self, req, my_id):
        host = req["host"]
        port = req["port"]

        peer_id = req["from"]  # correct unique id

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((host, port))
            pkt = {
                "action": "connect-accept",
                "from": my_id,
                "host": self.ip,
                "port": self.port
            }
            s.sendall(json.dumps(pkt).encode())
            s.close()
            self.connected_peers[peer_id] = (host, port, None)
            return True
        except:
            return False

    def send_message(self, target_ip, target_port, my_id, msg):
        try:
            self.messages.append((my_id, msg))
        except Exception:
            pass

        pkt = {
            "action": "message",
            "message": msg,
            "from": my_id
        }
        return self._send(target_ip, target_port, pkt)

    def broadcast(self, my_id, msg):
        try:
            self.messages.append(("BROADCAST", my_id, msg))
        except Exception:
            pass

        # connected_peers items() -> (peer_id, (ip,port,...))
        for peer_id, val in self.connected_peers.items():
            try:
                ip = val[0]
                port = val[1]
            except Exception:
                continue
            pkt = {
                "action": "broadcast",
                "message": msg,
                "from": my_id
            }
            self._send(ip, port, pkt)

    def _send(self, ip, port, pkt):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((ip, port))
            s.sendall(json.dumps(pkt).encode())
            s.close()
            return True
        except:
            print("[PeerNode] Send failed")
            return False
