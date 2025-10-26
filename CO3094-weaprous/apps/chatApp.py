# apps/chatApp.py
import json
from daemon.weaprous import WeApRous
from daemon.tracker import Tracker

tracker = Tracker()

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

    return app


