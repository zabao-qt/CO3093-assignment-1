import urllib

class Request:
    __attrs__=["method","url","headers","body","reason","cookies","routes","hook","path","version"]

    def __init__(self):
        self.method=None
        self.url=None
        self.headers={}
        self.path=None
        self.cookies={}
        self.body=""
        self.routes={}
        self.hook=None
        self.version="HTTP/1.1"

    def extract_request_line(self, raw):
        try:
            line=raw.splitlines()[0]
            m,p,v=line.split()
            if p=="/":
                p="/index.html"
            elif p == "/login":
                p = "/login.html"
            return m.upper(),p,v
        except:
            return None,None,None

    def prepare_headers(self,raw):
        lines=raw.split("\r\n")
        h={}
        for ln in lines[1:]:
            if ": " in ln:
                k,v=ln.split(": ",1)
                h[k.lower()]=v
        return h

    def parse_cookies(self, c):
        out={}
        if not c:
            return out
        for p in c.split(";"):
            p=p.strip()
            if "=" in p:
                k,v=p.split("=",1)
                out[k]=v
        return out

    def prepare(self, raw, routes=None):
        m, p, v = self.extract_request_line(raw)
        self.method = m
        self.path = p.strip()
        self.version = v
        self.headers = self.prepare_headers(raw)
        self.body = raw.split("\r\n\r\n",1)[1] if "\r\n\r\n" in raw else ""
        self.cookies = self.parse_cookies(self.headers.get("cookie",""))
        if routes:
            self.routes = routes
            self.hook = routes.get((self.method,self.path))
        return self
