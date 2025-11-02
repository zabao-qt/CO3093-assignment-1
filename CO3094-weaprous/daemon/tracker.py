import threading

class Tracker:
    def __init__(self):
        self.peers = []
        self.shared_info = {}
        self.lock = threading.Lock()

    def add_peer(self, peer_info):
        with self.lock:
            if not any(p["ip"] == peer_info["ip"] and p["port"] == peer_info["port"] for p in self.peers):
                self.peers.append(peer_info)
                print(f"[Tracker] Added peer: {peer_info}")
                return True
            return False

    def remove_peer(self, peer_info):
        with self.lock:
            before = len(self.peers)
            self.peers = [p for p in self.peers if not (p["ip"] == peer_info["ip"] and p["port"] == peer_info["port"])]
            after = len(self.peers)
            if after < before:
                print(f"[Tracker] Removed peer: {peer_info}")
            return before != after

    def get_peers(self):
        with self.lock:
            return list(self.peers)

    def submit_info(self, key, info):
        with self.lock:
            self.shared_info[key] = info
            print(f"[Tracker] Submitted info for {key}")
            return True

    def get_info(self, key):
        with self.lock:
            return self.shared_info.get(key, {})

    def get_all_info(self):
        with self.lock:
            return dict(self.shared_info)
