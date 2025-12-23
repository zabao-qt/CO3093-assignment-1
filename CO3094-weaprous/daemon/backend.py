import socket
import threading
import json
import os
from .httpadapter import HttpAdapter

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db")
PEERS_FILE = os.path.join(DB_DIR, "peers.json")
CHANNEL_FILE = os.path.join(DB_DIR, "channels.json")

def load_json(path, default):
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR)
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump(default, f)
        return default
    try:
        with open(path) as f:
            return json.load(f)
    except:
        return default

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f)

def register_peer(ip, port):
    data = load_json(PEERS_FILE, [])
    for p in data:
        if p["ip"] == ip and p["port"] == port:
            return
    data.append({"ip": ip, "port": port})
    save_json(PEERS_FILE, data)

def list_peers():
    peers = load_json(PEERS_FILE, [])
    alive = []

    for p in peers:
        ip = p.get("ip")
        port = p.get("port")
        
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.5)
        try:
            s.connect((ip, port))
            alive.append(p)
        except:
            pass
        finally:
            s.close()

    save_json(PEERS_FILE, alive)
    return alive

def create_channel(name):
    data = load_json(CHANNEL_FILE, {})
    if name not in data:
        data[name] = []
        save_json(CHANNEL_FILE, data)

def list_channels():
    return load_json(CHANNEL_FILE, {})

def post_channel(name, sender, msg):
    data = load_json(CHANNEL_FILE, {})
    if name not in data:
        data[name] = []
    data[name].append({"sender": sender, "msg": msg})
    save_json(CHANNEL_FILE, data)

def read_channel(name):
    data = load_json(CHANNEL_FILE, {})
    return data.get(name, [])

def process_backend_routes(method, path, body):
    if path == "/submit-info" and method == "POST":
        info = json.loads(body)
        register_peer(info["ip"], info["port"])
        return {"status": "ok"}

    if path == "/get-list" and method == "GET":
        return list_peers()

    if path == "/create-channel" and method == "POST":
        info = json.loads(body)
        create_channel(info["name"])
        return {"status": "ok"}

    if path == "/channels" and method == "GET":
        return list_channels()

    if path == "/post-channel" and method == "POST":
        info = json.loads(body)
        post_channel(info["name"], info["sender"], info["msg"])
        return {"status": "ok"}

    if path == "/channel-history" and method == "POST":
        info = json.loads(body)
        return read_channel(info["name"])

    return None

def handle_backend(ip, port, conn, addr):
    try:
        raw = conn.recv(8192).decode(errors="ignore")
    except:
        conn.close()
        return

    if not raw:
        conn.close()
        return

    # parse request line and headers
    try:
        lines = raw.splitlines()
        first = lines[0]
        method, path, _ = first.split()
    except:
        conn.close()
        return

    # extract Origin header if present
    origin = None
    for ln in lines[1:]:
        if ln.lower().startswith("origin:"):
            origin = ln.split(":",1)[1].strip()
            break

    body = ""
    if "\r\n\r\n" in raw:
        body = raw.split("\r\n\r\n", 1)[1]

    if method == "OPTIONS":
        allow_origin = origin if origin else "*"
        resp = (
            "HTTP/1.1 204 No Content\r\n"
            f"Access-Control-Allow-Origin: {allow_origin}\r\n"
            "Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS\r\n"
            "Access-Control-Allow-Headers: Content-Type, Authorization\r\n"
            "Access-Control-Allow-Credentials: true\r\n"
            "Access-Control-Max-Age: 86400\r\n"
            "Content-Length: 0\r\n"
            "Connection: close\r\n\r\n"
        )
        conn.sendall(resp.encode())
        conn.close()
        return

    result = process_backend_routes(method, path, body)
    if result is not None:
        out = json.dumps(result)
        allow_origin = origin if origin else "*"
        resp = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: application/json\r\n"
            f"Content-Length: {len(out.encode('utf-8'))}\r\n"
            f"Access-Control-Allow-Origin: {allow_origin}\r\n"
            "Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS\r\n"
            "Access-Control-Allow-Headers: Content-Type, Authorization\r\n"
            "Access-Control-Allow-Credentials: true\r\n"
            "Connection: close\r\n\r\n" +
            out
        )
        conn.sendall(resp.encode())
        conn.close()
        return

    HttpAdapter(ip, port, conn, addr, {}).handle_client(conn, addr, {})

def run_backend(ip, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((ip, port))
    s.listen(50)
    print("[Backend] Listening on", port)
    while True:
        conn, addr = s.accept()
        threading.Thread(target=handle_backend, args=(ip, port, conn, addr), daemon=True).start()

def create_backend(ip, port, routes={}):
    run_backend(ip, port)
