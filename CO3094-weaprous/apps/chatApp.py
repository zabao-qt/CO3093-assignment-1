# apps/chatApp.py
import json
import socket
from daemon.weaprous import WeApRous
from daemon.tracker import Tracker

tracker = Tracker()

def _send_tcp_message(ip, port, data, timeout=2):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((ip, int(port)))
        if isinstance(data, dict):
            payload = json.dumps(data).encode("utf-8")
        elif isinstance(data, str):
            payload = data.encode("utf-8")
        else:
            payload = str(data).encode("utf-8")
        s.sendall(payload + b"\n")
        s.close()
        return True, "sent"
    except Exception as e:
        return False, str(e)

def create_chatapp():
    app = WeApRous()

    @app.route("/submit-info", methods=["POST"])
    def submit_info(body):
        try:
            info = json.loads(body)
            name = info.get("name", "unknown")
            tracker.submit_info(name, info)
            return {"status": "ok", "message": f"Info submitted for {name}"}
        except json.JSONDecodeError:
            return {"status": "error", "message": "Invalid JSON body"}

    @app.route("/add-list", methods=["POST"])
    def add_peer(body):
        try:
            peer = json.loads(body)
            added = tracker.add_peer(peer)
            return {"status": "ok" if added else "exists", "peers": tracker.get_peers()}
        except json.JSONDecodeError:
            return {"status": "error", "message": "Invalid JSON body"}

    @app.route("/get-list", methods=["GET"])
    def get_peers(_):
        return {"peers": tracker.get_peers()}

    @app.route("/connect-peer", methods=["POST"])
    def connect_peer(body):
        """
        Connect to a peer (establish simple TCP handshake).
        Body: {"ip":"x.x.x.x", "port": 9001}
        """
        try:
            data = json.loads(body)
            ip = data.get("ip")
            port = data.get("port")
            if not ip or not port:
                return {"status": "error", "message": "ip and port required"}
            ok, msg = _send_tcp_message(ip, port, {"cmd": "handshake", "from": "tracker"})
            return {"status": "ok" if ok else "error", "message": msg}
        except json.JSONDecodeError:
            return {"status": "error", "message": "Invalid JSON body"}

    @app.route("/send-peer", methods=["POST"])
    def send_peer(body):
        """
        Send a message to a single peer.
        Body: {"ip":"x.x.x.x", "port":9001, "message":"hello"}
        """
        try:
            data = json.loads(body)
            ip = data.get("ip")
            port = data.get("port")
            message = data.get("message", "")
            if not ip or not port:
                return {"status": "error", "message": "ip and port required"}
            ok, msg = _send_tcp_message(ip, port, {"cmd": "message", "body": message})
            return {"status": "ok" if ok else "error", "message": msg}
        except json.JSONDecodeError:
            return {"status": "error", "message": "Invalid JSON body"}

    @app.route("/broadcast-peer", methods=["POST"])
    def broadcast_peer(body):
        """
        Broadcast message to all known peers in tracker.
        Body: {"message":"..."}
        """
        try:
            data = json.loads(body)
            message = data.get("message", "")
            peers = tracker.get_peers()
            results = []
            for p in peers:
                ip = p.get("ip")
                port = p.get("port")
                ok, msg = _send_tcp_message(ip, port, {"cmd": "broadcast", "body": message})
                results.append({"peer": p, "ok": ok, "msg": msg})
            return {"status": "ok", "results": results}
        except json.JSONDecodeError:
            return {"status": "error", "message": "Invalid JSON body"}
    
    return app


