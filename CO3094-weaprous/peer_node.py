import argparse
import json
import socket
import threading
import time
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# Config
POLL_INTERVAL = 3
RECONNECT_INTERVAL = 2

class PeerNode:
    def __init__(self, listen_host, listen_port, tracker_url):
        self.host = listen_host
        self.port = int(listen_port)
        self.tracker_url = tracker_url.rstrip("/")
        self.peers = {}
        self.lock = threading.Lock()
        self.out_sockets = {}
        self.in_sockets = []
        self.running = True

    def http_post_json(self, url, data):
        req = Request(url, data=json.dumps(data).encode("utf-8"), headers={"Content-Type":"application/json"})
        try:
            with urlopen(req, timeout=3) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            return {"error": str(e)}

    def http_get_json(self, url):
        req = Request(url)
        try:
            with urlopen(req, timeout=3) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            return {"error": str(e)}

    def register(self):
        url = f"{self.tracker_url}/add-list"
        payload = {"ip": self.host, "port": int(self.port)}
        # print("[PeerNode] Registering at tracker:", url, "payload:", payload)
        res = self.http_post_json(url, payload)
        # print("[PeerNode] register response:", res)

    def fetch_peers(self):
        url = f"{self.tracker_url}/get-list"
        res = self.http_get_json(url)
        if isinstance(res, dict) and "peers" in res:
            with self.lock:
                newmap = {}
                for p in res["peers"]:
                    try:
                        ip = p.get("ip")
                        port = int(p.get("port"))
                        if ip == self.host and port == self.port:
                            continue
                        newmap[(ip, port)] = (ip, port)
                    except Exception:
                        continue
                self.peers = newmap
        else:
            pass

    def connect_to_peer(self, ip, port):
        key = (ip, port)
        if key in self.out_sockets:
            s = self.out_sockets[key]
            try:
                s.sendall(b"")
                return True
            except Exception:
                try:
                    s.close()
                except:
                    pass
                del self.out_sockets[key]

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)
            s.connect((ip, port))
            s.settimeout(None)
            try:
                hs = json.dumps({"cmd": "handshake", "host": self.host, "port": self.port}).encode("utf-8") + b"\n"
                s.sendall(hs)
            except Exception:
                pass
            self.out_sockets[key] = s
            t = threading.Thread(target=self.handle_inbound_like_socket, args=(s, (ip, port)), daemon=True)
            t.start()
            print(f"🔗 Connected outbound to {ip}:{port}")
            return True
        except Exception as e:
            # print(f"[PeerNode] connect_to_peer {ip}:{port} failed: {e}")
            return False

    # Accept incoming connections
    def start_listener(self):
        def listener():
            srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            srv.bind((self.host, self.port))
            srv.listen(50)
            print(f"\n🟢 Listening for peers on {self.host}:{self.port}")
            while self.running:
                try:
                    conn, addr = srv.accept()
                    conn.settimeout(None)
                    print("🔔 Incoming connection from", addr)
                    with self.lock:
                        self.in_sockets.append(conn)
                    t = threading.Thread(target=self.handle_inbound_socket, args=(conn, addr), daemon=True)
                    t.start()
                except Exception as e:
                    time.sleep(0.1)
            try:
                srv.close()
            except:
                pass
        t = threading.Thread(target=listener, daemon=True)
        t.start()

    def handle_inbound_socket(self, conn, addr):
        peer_host = f"{addr[0]}:{addr[1]}"
        try:
            while self.running:
                data = b""
                while True:
                    chunk = conn.recv(4096)
                    if not chunk:
                        break
                    data += chunk
                    if b"\n" in data:
                        break
                if not data:
                    break

                try:
                    text = data.decode(errors="ignore").strip()
                    msg = json.loads(text)
                    body = msg.get("body", text)
                    print(f"[{peer_host}] {body}")
                except json.JSONDecodeError:
                    print(f"[{peer_host}] {text}")

        except Exception:
            pass
        finally:
            try:
                conn.close()
            except:
                pass
            with self.lock:
                if conn in self.in_sockets:
                    self.in_sockets.remove(conn)
            print(f"[{peer_host}] disconnected")

    def handle_inbound_like_socket(self, sock, peeraddr):
        peer_repr = f"{peeraddr[0]}:{peeraddr[1]}"
        try:
            while self.running:
                data = b""
                while True:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    data += chunk
                    if b"\n" in data:
                        break
                if not data:
                    break
                try:
                    text = data.decode(errors="ignore").strip()
                except Exception:
                    text = "<binary>"
                if text:
                    print(f"⬅️ {peer_repr}: {text}")
        except Exception:
            pass
        finally:
            with self.lock:
                if peeraddr in self.out_sockets:
                    try:
                        self.out_sockets[peeraddr].close()
                    except:
                        pass
                    del self.out_sockets[peeraddr]
            print(f"🔌 Outbound disconnected {peer_repr}")

    def maintain_connections_loop(self):
        def loop():
            while self.running:
                try:
                    self.fetch_peers()
                    with self.lock:
                        targets = list(self.peers.keys())
                    for (ip, port) in targets:
                        if (ip, port) not in self.out_sockets:
                            ok = self.connect_to_peer(ip, port)
                            if not ok:
                                time.sleep(RECONNECT_INTERVAL)
                    time.sleep(POLL_INTERVAL)
                except Exception as e:
                    time.sleep(1)
        t = threading.Thread(target=loop, daemon=True)
        t.start()

    def broadcast(self, message):
        payload = json.dumps({"cmd":"message","body": message}).encode("utf-8") + b"\n"
        sent = 0
        with self.lock:
            keys = list(self.out_sockets.keys())
        for k in keys:
            s = None
            with self.lock:
                s = self.out_sockets.get(k)
            if not s:
                continue
            try:
                s.sendall(payload)
                sent += 1
            except Exception:
                with self.lock:
                    try:
                        s.close()
                    except:
                        pass
                    if k in self.out_sockets:
                        del self.out_sockets[k]
                print(f"⚠️ Disconnected {k}")
        if sent:
            print(f"➡️ Sent to {sent} peer(s)")
        else:
            print("⚠️ No peers available to send")

    def stop(self):
        self.running = False
        with self.lock:
            for s in list(self.out_sockets.values()):
                try:
                    s.close()
                except:
                    pass
            for s in list(self.in_sockets):
                try:
                    s.close()
                except:
                    pass

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0", help="bind host")
    parser.add_argument("--port", type=int, default=9999, help="listen port")
    parser.add_argument("--tracker", default="http://127.0.0.1:8000", help="tracker webapp root (e.g. http://127.0.0.1:8000)")
    args = parser.parse_args()

    node = PeerNode(args.host, args.port, args.tracker)
    node.register()
    node.start_listener()
    node.maintain_connections_loop()

    print("💬 Ready. Type a message and press Enter to broadcast to connected peers. Ctrl-C to stop.")
    try:
        while True:
            line = input("> ").strip()
            if not line:
                continue
            if line.lower() in ("/q", "/quit", "/exit"):
                print("Exiting...")
                break
            if line.lower() in ("/h", "/help"):
                print("Commands:")
                print("  /peers         – list discovered peers")
                print("  /status        – show connection counts")
                print("  /send <msg>    – send message to all peers (or just type message)")
                print("  /quit          – exit")
                continue
            if line.lower() == "/peers":
                with node.lock:
                    print("Known peers:", list(node.peers.keys()))
                    print("Outbound sockets:", list(node.out_sockets.keys()))
                continue
            if line.lower() == "/status":
                with node.lock:
                    print(f"Known peers: {len(node.peers)}  Outbound: {len(node.out_sockets)}  Inbound connections: {len(node.in_sockets)}")
                continue
            if line.startswith("/send "):
                msg = line[len("/send "):].strip()
                if msg:
                    node.broadcast(msg)
                continue
            node.broadcast(line)
    except KeyboardInterrupt:
        print("\nInterrupted, shutting down...")
    finally:
        node.stop()

if __name__ == "__main__":
    main()
