import json
import socket
import os

TRACKER_IP = os.environ.get("TRACKER_IP", "127.0.0.1")
TRACKER_PORT = int(os.environ.get("TRACKER_PORT", "9000"))

class ChatRoutes:
    def __init__(self, app, peer):
        self.app = app
        self.peer = peer
        self.register_routes()

    def register_routes(self):
        # @self.app.route('/login', methods=['POST'])
        # def login(headers="guest", body="anonymous"):
        #     try:
        #         data = {}
        #         if body:
        #             try:
        #                 data = json.loads(body)
        #             except:
        #                 # handle form encoded
        #                 for pair in body.split("&"):
        #                     if "=" in pair:
        #                         k,v = pair.split("=",1)
        #                         data[k]=v
        #         username = data.get("username") or ""
        #         password = data.get("password") or ""
        #         if username == "admin" and password == "password":
        #             return {"status":"ok","set-cookie":"auth=true"}
        #         return {"status":"unauthorized"}, 
        #     except Exception as e:
        #         return {"error": str(e)}
            
        @self.app.route("/whoami", methods=["GET"])
        def whoami(headers="guest", body=""):
            return {"id": f"{self.peer.ip}:{self.peer.port}"}

        @self.app.route('/get-list', methods=['GET'])
        def get_list(headers="guest", body=""):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(2)
                s.connect((TRACKER_IP, TRACKER_PORT))
                req = (
                    "GET /get-list HTTP/1.1\r\n"
                    f"Host: {TRACKER_IP}:{TRACKER_PORT}\r\n"
                    "Connection: close\r\n\r\n"
                )
                s.sendall(req.encode())
                raw = b""
                while True:
                    chunk = s.recv(4096)
                    if not chunk:
                        break
                    raw += chunk
                s.close()
                text = raw.decode(errors="ignore")
                if "\r\n\r\n" in text:
                    return text.split("\r\n\r\n",1)[1]
                return json.dumps({"error":"invalid response"})
            except Exception as e:
                return json.dumps({"error":"tracker-offline","detail":str(e)})

        @self.app.route("/connect-peer", methods=["POST"])
        def connect_peer(headers, body):
            info = json.loads(body)
            target_ip = info["ip"]
            target_port = info["port"]
            my_id = f"{self.peer.ip}:{self.peer.port}"
            ok = self.peer.request_connect(target_ip, target_port, my_id)
            return {"status":"sent" if ok else "failed"}

        @self.app.route("/accept-request", methods=["POST"])
        def accept_request(headers, body):
            req = json.loads(body)
            my_id = f"{self.peer.ip}:{self.peer.port}"
            ok = self.peer.accept_request(req, my_id)
            peer_from = req.get("from")
            self.peer.pending_requests = [p for p in self.peer.pending_requests if str(p.get("from")) != str(peer_from)]
            return {"status":"accepted" if ok else "failed"}
        
        @self.app.route("/deny-request", methods=["POST"])
        def deny_request(headers, body):
            req = json.loads(body)
            peer_from = req.get("from")
            self.peer.pending_requests = [p for p in self.peer.pending_requests if str(p.get("from")) != str(peer_from)]
            return {"status":"denied"}
        
        @self.app.route("/disconnect-peer", methods=["POST"])
        def disconnect_peer(headers, body):
            info = json.loads(body)
            peer_id = info.get("id")
            ip = info.get("ip")
            port = info.get("port")
            # remove by id if available
            if peer_id and peer_id in self.peer.connected_peers:
                try:
                    del self.peer.connected_peers[peer_id]
                except KeyError:
                    pass
                return {"status":"disconnected"}
            # fallback: find matching ip/port
            to_remove = []
            for pid, val in list(self.peer.connected_peers.items()):
                # val could be (ip, port) or (ip, port, sock)
                try:
                    v_ip = val[0]
                    v_port = val[1]
                    if str(v_ip) == str(ip) and int(v_port) == int(port):
                        to_remove.append(pid)
                except Exception:
                    continue
            for pid in to_remove:
                self.peer.connected_peers.pop(pid, None)
            return {"status":"disconnected" if to_remove else "not-found"}

        @self.app.route("/send-peer", methods=["POST"])
        def send_peer(headers, body):
            info = json.loads(body)
            target_ip = info["ip"]
            target_port = info["port"]
            msg = info["message"]
            my_id = f"{self.peer.ip}:{self.peer.port}"
            ok = self.peer.send_message(target_ip, target_port, my_id, msg)
            return {"status":"sent" if ok else "failed"}

        @self.app.route("/broadcast-peer", methods=["POST"])
        def broadcast_peer(headers, body):
            info = json.loads(body)
            msg = info["message"]
            my_id = f"{self.peer.ip}:{self.peer.port}"
            self.peer.broadcast(my_id, msg)
            return {"status":"broadcasted"}

        @self.app.route("/get-pending", methods=["GET"])
        def get_pending(headers="guest", body=""):
            return self.peer.pending_requests

        @self.app.route("/get-connected", methods=["GET"])
        def get_connected(headers="guest", body=""):
            """
            Return list of connected peers.
            Make unpacking robust: connected_peers values might be (host, port) or (host, port, something).
            """
            peers = []
            try:
                for peer_id, val in self.peer.connected_peers.items():
                    # val could be a tuple/list (host, port) or (host, port, sock)
                    if not val:
                        continue
                    try:
                        host = val[0]
                        port = val[1]
                    except Exception as e:
                        # malformed entry — skip but log for diagnostics
                        try:
                            # self.logger may exist; otherwise print
                            if hasattr(self, "logger"):
                                self.logger.exception("Malformed connected_peers entry for %s: %r", peer_id, val)
                            else:
                                print(f"[get_connected] malformed entry for {peer_id}: {val!r} -> {e}")
                        except Exception:
                            pass
                        continue
                    peers.append({"id": peer_id, "host": host, "port": port})
            except Exception as e:
                # Top-level safety: return a useful error payload instead of crashing the hook system
                try:
                    if hasattr(self, "logger"):
                        self.logger.exception("Error in /get-connected: %s", e)
                    else:
                        print(f"[get_connected] unexpected error: {e}")
                except Exception:
                    pass
                return {"error": "hook error", "detail": str(e)}
            return {"status": "ok", "peers": peers}

        @self.app.route("/get-messages", methods=["GET"])
        def get_messages(headers="guest", body=""):
            return self.peer.messages