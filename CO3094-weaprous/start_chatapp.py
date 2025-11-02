import argparse
from apps.chatApp import create_chatapp

PORT = 8000

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='ChatApp', description='Start chat webapp')
    parser.add_argument('--server-ip', default='0.0.0.0')
    parser.add_argument('--server-port', type=int, default=PORT)
    args = parser.parse_args()
    ip = args.server_ip
    port = args.server_port

    app = create_chatapp()
    app.prepare_address(ip, port)
    app.run()