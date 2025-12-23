import argparse
import threading
import json
import socket
import time

from daemon.weaprous import WeApRous
from apps.peer import PeerNode
from apps.routes import ChatRoutes
from daemon.backend import run_backend
from apps.chat_backend import run_chat_backend

TRACKER_IP = "127.0.0.1"
TRACKER_PORT = 9000       # backend server


def start_peer_node(peer):
    peer.run()


def start_webapp(app):
    run_backend(my_ip, ui_port, app.routes)


def register_to_tracker(my_ip, my_port):
    """
    Register this client to the central backend server.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((TRACKER_IP, TRACKER_PORT))

        req = (
            "POST /submit-info HTTP/1.1\r\n"
            f"Host: {TRACKER_IP}:{TRACKER_PORT}\r\n"
            "Content-Type: application/json\r\n"
            f"Content-Length: {len(json.dumps({'ip': my_ip, 'port': my_port}))}\r\n"
            "\r\n"
            + json.dumps({"ip": my_ip, "port": my_port})
        )

        s.sendall(req.encode())
        s.close()
        print("[ChatApp] Registered to tracker")
    except:
        print("[ChatApp] Could NOT register to tracker (server offline)")


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--ui-port", type=int, default=8001)
    parser.add_argument("--peer-port", type=int, default=7001)
    parser.add_argument("--my-ip", default="127.0.0.1")
    args = parser.parse_args()

    my_ip = args.my_ip
    ui_port = args.ui_port
    peer_port = args.peer_port

    peer = PeerNode(my_ip, peer_port)

    app = WeApRous()
    routes = ChatRoutes(app, peer)

    app.prepare_address(my_ip, ui_port)

    # Register to backend tracker
    threading.Thread(target=register_to_tracker, args=(my_ip, peer_port), daemon=True).start()

    # Start peer node (listening for P2P messages)
    threading.Thread(target=start_peer_node, args=(peer,), daemon=True).start()

    # Start UI webapp
    run_chat_backend(my_ip, ui_port, app.routes)
