import socket
import threading
from daemon.httpadapter import HttpAdapter

def run_chat_backend(ip, port, routes):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((ip, port))
    s.listen(50)
    print("[ChatBackend] Listening on", port)
    print(f"\033[96mChatApp running, click on \033[92mhttp://{ip}:{port}/login\033[0m")
    while True:
        conn, addr = s.accept()
        threading.Thread(
            target=lambda conn=conn,addr=addr: HttpAdapter(ip, port, conn, addr, routes).handle_client(conn, addr, routes),
            daemon=True
        ).start()
