import socket

HOST = "0.0.0.0"
PORT = 9999

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen(5)
print(f"Peer listening on {HOST}:{PORT}")
while True:
    conn, addr = s.accept()
    data = b""
    while True:
        chunk = conn.recv(4096)
        if not chunk:
            break
        data += chunk
        if b"\n" in data:
            break
    print("FROM", addr, data.decode(errors="ignore").strip())
    conn.close()
