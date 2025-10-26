# daemon/tracker.py 

class Tracker:
    def __init__(self):
        self.peers = []
        self.shared_info = {}

    def add_peer(self, peer_info):
        if not any(p["ip"] == peer_info["ip"] and p["port"] == peer_info["port"] for p in self.peers):
            self.peers.append(peer_info)
            print(f"[Tracker] Added peer: {peer_info}")
            return True
        return False

    def remove_peer(self, peer_info):
        before = len(self.peers)
        self.peers = [p for p in self.peers if not (p["ip"] == peer_info["ip"] and p["port"] == peer_info["port"])]
        after = len(self.peers)
        print(f"[Tracker] Removed peer: {peer_info}") if after < before else None
        return before != after

    def get_peers(self):
        return self.peers

    def submit_info(self, key, info):
        self.shared_info[key] = info
        print(f"[Tracker] Submitted info for {key}")
        return True

    def get_info(self, key):
        return self.shared_info.get(key, {})

    def get_all_info(self):
        return self.shared_info
