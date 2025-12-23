#
# Copyright (C) 2025 pdnguyen of HCMC University of Technology VNU-HCM.
# All rights reserved.
# This file is part of the CO3093/CO3094 course.
#
# WeApRous release
#
# The authors hereby grant to Licensee personal permission to use
# and modify the Licensed Source Code for the sole purpose of studying
# while attending the course
#

"""
daemon.proxy
~~~~~~~~~~~~~~~~~

This module implements a simple proxy server using Python's socket and threading libraries.
It routes incoming HTTP requests to backend services based on hostname mappings and returns
the corresponding responses to clients.
"""

import socket
import threading
from .response import *
from .httpadapter import HttpAdapter
from .dictionary import CaseInsensitiveDict


# Fallback mapping (not used when proxy.conf is parsed)
PROXY_PASS = {
    "192.168.56.103:8080": ('192.168.56.103', 9000),
    "app1.local": ('192.168.56.103', 9001),
    "app2.local": ('192.168.56.103', 9002),
}


def forward_request(host, port, request):
    """
    Forward raw HTTP request bytes to backend server.
    """
    backend = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        backend.connect((host, port))
        backend.sendall(request.encode())

        response = b""
        while True:
            chunk = backend.recv(4096)
            if not chunk:
                break
            response += chunk

        return response

    except socket.error as e:
        print("[Proxy] Socket error:", e)
        return (
            "HTTP/1.1 404 Not Found\r\n"
            "Content-Type: text/plain\r\n"
            "Content-Length: 13\r\n"
            "Connection: close\r\n"
            "\r\n"
            "404 Not Found"
        ).encode('utf-8')


def resolve_routing_policy(hostname, routes):
    """
    Determine correct backend according to parsed proxy.conf rules.
    """

    # Default fallback (never allow crash)
    proxy_map, policy = routes.get(hostname, ("127.0.0.1:9000", "round-robin"))

    print("[Proxy] Routing host:", hostname)
    print("[Proxy] Proxy map:", proxy_map)
    print("[Proxy] Policy:", policy)

    # Multiple proxy_pass
    if isinstance(proxy_map, list):
        if len(proxy_map) == 0:
            print("[Proxy] No routes configured. Using fallback 127.0.0.1:9000")
            return "127.0.0.1", "9000"

        elif len(proxy_map) == 1:
            # Single backend
            host, port = proxy_map[0].split(":")
            return host, port

        else:
            # Multi-backend (round-robin default)
            # simple: always pick first — you can extend later
            host, port = proxy_map[0].split(":")
            return host, port

    # Single string proxy_pass
    else:
        host, port = proxy_map.split(":")
        return host, port


def handle_client(ip, port, conn, addr, routes):
    """
    Handle a single incoming client to the proxy.
    """

    try:
        request = conn.recv(1024).decode()
    except:
        conn.close()
        return

    hostname = None

    # Parse Host header
    for line in request.splitlines():
        if line.lower().startswith("host:"):
            hostname = line.split(":", 1)[1].strip()

    print("[Proxy] {} Host={}".format(addr, hostname))

    if not hostname:
        response = (
            "HTTP/1.1 400 Bad Request\r\n"
            "Content-Type: text/plain\r\n"
            "Content-Length: 11\r\n"
            "\r\n"
            "Bad Request"
        ).encode()
        conn.sendall(response)
        conn.close()
        return

    # Resolve backend
    resolved_host, resolved_port = resolve_routing_policy(hostname, routes)

    # Convert port safely
    try:
        resolved_port = int(resolved_port)
    except:
        resolved_port = 9000

    print("[Proxy] Forwarding → {}:{}".format(resolved_host, resolved_port))

    # Forward to backend
    response = forward_request(resolved_host, resolved_port, request)
    conn.sendall(response)
    conn.close()


def run_proxy(ip, port, routes):
    """
    Main proxy loop: accepts clients and spawns threads
    """
    proxy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        proxy.bind((ip, port))
        proxy.listen(50)
        print("[Proxy] Listening on {}:{}".format(ip, port))

        while True:
            conn, addr = proxy.accept()
            thread = threading.Thread(
                target=handle_client,
                args=(ip, port, conn, addr, routes)
            )
            thread.daemon = True
            thread.start()

    except socket.error as e:
        print("[Proxy] Socket error:", e)


def create_proxy(ip, port, routes):
    run_proxy(ip, port, routes)
