import os
from urllib.parse import unquote
from .request import Request
from .response import Response
import json

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
    "Access-Control-Max-Age": "86400"
}

class HttpAdapter:
    __attrs__ = ["ip","port","conn","connaddr","routes","request","response"]

    def __init__(self, ip, port, conn, connaddr, routes):
        self.ip = ip
        self.port = port
        self.conn = conn
        self.connaddr = connaddr
        self.routes = routes
        self.request = Request()
        self.response = Response()

    def parse_form(self, body):
        params = {}
        if not body:
            return params
        for pair in body.split("&"):
            if "=" in pair:
                k,v = pair.split("=",1)
                params[k] = unquote(v)
        return params

    def _write(self, txt):
        try:
            self.conn.sendall(txt.encode())
        finally:
            try:
                self.conn.close()
            except:
                pass

    def send_json(self, obj, extra_headers=None, status=200, status_text="OK"):
        txt = json.dumps(obj)
        lines = [f"HTTP/1.1 {status} {status_text}"]
        lines.append("Content-Type: application/json")
        lines.append(f"Content-Length: {len(txt.encode('utf-8'))}")
        for k,v in CORS_HEADERS.items():
            lines.append(f"{k}: {v}")
        if extra_headers:
            for k,v in extra_headers.items():
                lines.append(f"{k}: {v}")
        lines.append("Connection: close")
        lines.append("")
        lines.append(txt)
        self._write("\r\n".join(lines))

    def send_text(self, body, content_type="text/plain", extra_headers=None, status=200, status_text="OK"):
        b = body if isinstance(body, str) else str(body)
        lines = [f"HTTP/1.1 {status} {status_text}"]
        lines.append(f"Content-Type: {content_type}")
        lines.append(f"Content-Length: {len(b.encode('utf-8'))}")
        for k,v in CORS_HEADERS.items():
            lines.append(f"{k}: {v}")
        if extra_headers:
            for k,v in extra_headers.items():
                lines.append(f"{k}: {v}")
        lines.append("Connection: close")
        lines.append("")
        lines.append(b)
        self._write("\r\n".join(lines))

    def handle_client(self, conn, addr, routes):
        try:
            raw = conn.recv(8192).decode(errors="ignore")
        except:
            conn.close()
            return
        if not raw:
            conn.close()
            return

        req = self.request
        resp = self.response
        req.prepare(raw, routes)

        # compute dynamic CORS origin
        origin = req.headers.get("origin") or None
        allow_origin = origin if origin else "*"
        cors_extra = {
            "Access-Control-Allow-Origin": allow_origin,
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Max-Age": "86400"
        }

        if req.method == "OPTIONS":
            self.send_text("", content_type="text/plain", extra_headers=cors_extra, status=204, status_text="No Content")
            return

        if req.hook:
            try:
                out = req.hook(headers=req.headers, body=req.body)
            except Exception as e:
                out = {"error":"hook error", "detail": str(e)}
            if isinstance(out, (dict,list)):
                self.send_json(out, extra_headers=cors_extra)
                return
            if isinstance(out, str):
                try:
                    parsed = json.loads(out)
                    self.send_json(parsed, extra_headers=cors_extra)
                    return
                except:
                    self.send_text(out, content_type="text/plain", extra_headers=cors_extra)
                    return
            self.send_text(str(out), content_type="text/plain", extra_headers=cors_extra)
            return

        if req.method=="POST" and req.path in ("/login", "/login.html"):
            body = raw.split("\r\n\r\n",1)[1] if "\r\n\r\n" in raw else ""
            form = self.parse_form(body)
            u = form.get("username")
            p = form.get("password")
            if u=="admin" and p=="password":
                extra = {
                    "Set-Cookie": "auth=true; Path=/",
                    "Location": "/"
                }
                extra.update(cors_extra)

                self.send_text("", content_type="text/plain", extra_headers=extra, status=302, status_text="Found")
                return
            else:
                self.send_text("Unauthorized", content_type="text/plain", extra_headers=cors_extra, status=401, status_text="Unauthorized")
                return

        if req.path=="/index.html":
            if not (req.cookies and req.cookies.get("auth")=="true"):
                base = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/www/"
                path = os.path.join(base, "401.html")
                try:
                    with open(path, "rb") as f:
                        html = f.read()

                    extra = {}
                    extra.update(cors_extra)
                    header = (
                        "HTTP/1.1 401 Unauthorized\r\n"
                        "Content-Type: text/html\r\n"
                        f"Content-Length: {len(html)}\r\n"
                    )
                    for k,v in extra.items():
                        header += f"{k}: {v}\r\n"
                    header += "Connection: close\r\n\r\n"

                    self.conn.sendall(header.encode() + html)
                    self.conn.close()
                    return
                except:
                    self.send_text("401 Unauthorized", status=401, status_text="Unauthorized", extra_headers=cors_extra)
                    return

        if req.path.endswith(".html") or req.path.startswith("/static") or req.path.startswith("/css") or req.path.startswith("/js") or req.path.startswith("/images"):
            out = resp.build_response(req)
            try:
                self.conn.sendall(out)
            finally:
                try: self.conn.close()
                except: pass
            return

        self.send_json({"error":"unknown route"}, extra_headers=cors_extra, status=404, status_text="Not Found")
