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
daemon.response
~~~~~~~~~~~~~~~~~

This module provides a :class: `Response <Response>` object to manage and persist 
response settings (cookies, auth, proxies), and to construct HTTP responses
based on incoming requests. 

The current version supports MIME type detection, content loading and header formatting
"""
import datetime
import os
import mimetypes
from .dictionary import CaseInsensitiveDict

# Base directory: parent folder of this file → project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/"

class Response:
    __attrs__ = [
        "_content",
        "_header",
        "status_code",
        "method",
        "headers",
        "url",
        "history",
        "encoding",
        "reason",
        "cookies",
        "elapsed",
        "request",
        "body",
    ]

    def __init__(self, request=None):
        self._content = b""
        self._content_consumed = False
        self._next = None

        self.status_code = 200
        self.headers = {}
        self.url = None
        self.encoding = "utf-8"
        self.history = []
        self.reason = "OK"

        self.cookies = CaseInsensitiveDict()
        self.elapsed = datetime.timedelta(0)
        self.request = request

    def get_mime_type(self, path):
        try:
            mime_type, _ = mimetypes.guess_type(path)
        except Exception:
            return 'application/octet-stream'
        return mime_type or 'application/octet-stream'

    def prepare_content_type(self, mime_type='text/html'):
        main_type, sub_type = mime_type.split('/', 1)
        print(f"[Response] MIME main={main_type} sub={sub_type}")

        # HTML
        if main_type == "text" and sub_type == "html":
            self.headers["Content-Type"] = "text/html"
            return BASE_DIR + "www/"

        # CSS / text files
        if main_type == "text":
            self.headers["Content-Type"] = f"text/{sub_type}"
            return BASE_DIR + "static/"

        # Images
        if main_type == "image":
            self.headers["Content-Type"] = f"image/{sub_type}"
            return BASE_DIR + "static/"

        # Application (JSON, JS, etc.)
        if main_type == "application":
            self.headers["Content-Type"] = f"application/{sub_type}"
            return BASE_DIR + "apps/"

        # If unsupported
        raise ValueError(f"Invalid MIME type {mime_type}")

    def build_content(self, path, base_dir):
        filepath = os.path.join(base_dir, path)

        print(f"[Response] serving file {filepath}")

        if not os.path.exists(filepath):
            print("[Response] FILE NOT FOUND:", filepath)
            return 0, b""

        try:
            with open(filepath, "rb") as f:
                content = f.read()
                return len(content), content
        except IOError:
            return 0, b""

    def build_response_header(self, request):
        lines = []

        # Status Line
        status_line = f"HTTP/1.1 {self.status_code} {self.reason}"
        lines.append(status_line)

        # Required headers
        self.headers.setdefault("Content-Length", str(len(self._content)))
        self.headers.setdefault("Date", datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT"))
        self.headers.setdefault("Server", "WeaprousHTTP/1.0")

        # Convert header dict → HTTP string
        for key, value in self.headers.items():
            lines.append(f"{key}: {value}")

        # End of headers
        lines.append("")  
        lines.append("")  

        header_bytes = "\r\n".join(lines).encode("utf-8")
        return header_bytes

    def build_notfound(self):
        html = (
            "HTTP/1.1 404 Not Found\r\n"
            "Content-Type: text/html\r\n"
            "Content-Length: 13\r\n"
            "Connection: close\r\n"
            "\r\n"
            "404 Not Found"
        )
        return html.encode("utf-8")

    def _resolve_path_and_mime(self, path):
        """
        Return (base_dir, normalized_path, mime_type)
        base_dir: filesystem base directory where file is located
        normalized_path: path relative to base_dir (leading '/' stripped)
        mime_type: Content-Type to send
        """
        p = path
        if p == "/":
            p = "/index.html"
        mime_type = self.get_mime_type(p)
        base = BASE_DIR

        if p.startswith("/css/"):
            base_dir = base + "static/css/"
            normalized = p[len("/css/"):]
            mime_type = "text/css"
        elif p.startswith("/js/"):
            base_dir = base + "static/js/"
            normalized = p[len("/js/"):]
            # Some user agents ask for .js as application/javascript
            mime_type = "application/javascript"
        elif p.startswith("/images/"):
            base_dir = base + "static/images/"
            normalized = p[len("/images/"):]
        elif p.startswith("/apps/"):
            base_dir = base + "apps/"
            normalized = p[len("/apps/"):]
        elif p.endswith(".html") or mime_type == "text/html":
            base_dir = base + "www/"
            normalized = p.lstrip("/")
            mime_type = "text/html"
        else:
            base_dir = base + "static/"
            normalized = p.lstrip("/")

        return base_dir, normalized, mime_type

    def build_response(self, request):
        path = request.path
        # Resolve where the file lives and mime -type
        base_dir, rel_path, mime_type = self._resolve_path_and_mime(path)

        print(f"[Response] {request.method} {path} -> base={base_dir} rel={rel_path} MIME={mime_type}")

        # Load file
        size, content = self.build_content(rel_path, base_dir)
        if size == 0:
            return self.build_notfound()

        self._content = content
        # Ensure content-length and content-type are set
        self.headers["Content-Length"] = str(size)
        self.headers["Content-Type"] = mime_type

        # Final header + content
        header = self.build_response_header(request)
        return header + content