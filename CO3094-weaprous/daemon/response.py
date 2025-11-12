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

BASE_DIR = ""

def handle_text_other(sub_type):
    """Handle unsupported text subtypes gracefully."""
    print(f"[Response] Unsupported text subtype: {sub_type}, fallback to text/plain")

class Response():   
    """The :class:`Response <Response>` object, which contains a
    server's response to an HTTP request.

    Instances are generated from a :class:`Request <Request>` object, and
    should not be instantiated manually; doing so may produce undesirable
    effects.

    :class:`Response <Response>` object encapsulates headers, content, 
    status code, cookies, and metadata related to the request-response cycle.
    It is used to construct and serve HTTP responses in a custom web server.

    :attrs status_code (int): HTTP status code (e.g., 200, 404).
    :attrs headers (dict): dictionary of response headers.
    :attrs url (str): url of the response.
    :attrsencoding (str): encoding used for decoding response content.
    :attrs history (list): list of previous Response objects (for redirects).
    :attrs reason (str): textual reason for the status code (e.g., "OK", "Not Found").
    :attrs cookies (CaseInsensitiveDict): response cookies.
    :attrs elapsed (datetime.timedelta): time taken to complete the request.
    :attrs request (PreparedRequest): the original request object.

    Usage::

      >>> import Response
      >>> resp = Response()
      >>> resp.build_response(req)
      >>> resp
      <Response>
    """

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
        "reason",
    ]


    def __init__(self, request=None):
        """
        Initializes a new :class:`Response <Response>` object.

        : params request : The originating request object.
        """

        self._content = False
        self._content_consumed = False
        self._next = None

        #: Integer Code of responded HTTP Status, e.g. 404 or 200.
        self.status_code = None

        #: Case-insensitive Dictionary of Response Headers.
        #: For example, ``headers['content-type']`` will return the
        #: value of a ``'Content-Type'`` response header.
        self.headers = {}

        #: URL location of Response.
        self.url = None

        #: Encoding to decode with when accessing response text.
        self.encoding = None

        #: A list of :class:`Response <Response>` objects from
        #: the history of the Request.
        self.history = []

        #: Textual reason of responded HTTP Status, e.g. "Not Found" or "OK".
        self.reason = None

        #: A of Cookies the response headers.
        self.cookies = CaseInsensitiveDict()

        #: The amount of time elapsed between sending the request
        self.elapsed = datetime.timedelta(0)

        #: The :class:`PreparedRequest <PreparedRequest>` object to which this
        #: is a response.
        self.request = None


    def get_mime_type(self, path):
        """
        Determines the MIME type of a file based on its path.

        "params path (str): Path to the file.

        :rtype str: MIME type string (e.g., 'text/html', 'image/png').
        """

        try:
            mime_type, _ = mimetypes.guess_type(path)
        except Exception:
            return 'application/octet-stream'
        return mime_type or 'application/octet-stream'


    def prepare_content_type(self, mime_type='text/html'):
        """
        Prepares the Content-Type header and determines the base directory
        for serving the file based on its MIME type.

        :params mime_type (str): MIME type of the requested resource.

        :rtype str: Base directory path for locating the resource.

        :raises ValueError: If the MIME type is unsupported.
        """
        
        base_dir = ""

        main_type, sub_type = mime_type.split('/', 1)
        print("[Response] processing MIME main_type={} sub_type={}".format(main_type,sub_type))
        if main_type == 'text':
            self.headers['Content-Type']='text/{}'.format(sub_type)
            if sub_type == 'plain' or sub_type == 'css':
                base_dir = BASE_DIR+"static/"
            elif sub_type == 'html':
                base_dir = BASE_DIR+"www/"
            else:
                handle_text_other(sub_type)
        elif main_type == 'image':
            base_dir = BASE_DIR+"static/"
            self.headers['Content-Type']='image/{}'.format(sub_type)
        elif main_type == 'application':
            if sub_type in ('javascript', 'x-javascript'):
                base_dir = BASE_DIR + "static/"
                self.headers['Content-Type'] = 'application/javascript'
            else:
                base_dir = BASE_DIR + "apps/"
                self.headers['Content-Type'] = 'application/{}'.format(sub_type)
        #
        #  TODO: process other mime_type
        #        application/xml       
        #        application/zip
        #        ...
        #        text/csv
        #        text/xml
        #        ...
        #        video/mp4 
        #        video/mpeg
        #        ...
        #
        else:
            raise ValueError("Invalid MEME type: main_type={} sub_type={}".format(main_type,sub_type))

        return base_dir


    def build_content(self, path, base_dir):
        """
        Loads the objects file from storage space.

        :params path (str): relative path to the file.
        :params base_dir (str): base directory where the file is located.

        :rtype tuple: (int, bytes) representing content length and content data.
        """

        filepath = os.path.join(base_dir, path.lstrip('/'))

        print("[Response] serving the object at location {}".format(filepath))
        try:
            with open(filepath, "rb") as f:
                content = f.read()
            return len(content), content
        except FileNotFoundError:
            try_fallbacks = [
                os.path.join(base_dir, "images", "ico", os.path.basename(path)),
                os.path.join(base_dir, "images", os.path.basename(path)),
                os.path.join(base_dir, os.path.basename(path))
            ]
            for fb in try_fallbacks:
                try:
                    print("[Response] trying fallback location", fb)
                    with open(fb, "rb") as f:
                        content = f.read()
                    return len(content), content
                except FileNotFoundError:
                    continue
            print("[Response] File not found:", filepath)
            return len(b"404 Not Found"), b"404 Not Found"
        except Exception as e:
            print("[Response] Error reading file:", e)
            return len(b"500 Internal Server Error"), b"500 Internal Server Error"


    def build_response_header(self, request):
        """
        Constructs the HTTP response headers based on the class:`Request <Request>
        and internal attributes.

        :params request (class:`Request <Request>`): incoming request object.

        :rtypes bytes: encoded HTTP response header.
        """
        reqhdr = request.headers
        rsphdr = self.headers

        #Build dynamic headers
        headers = {
                "Accept": "{}".format(reqhdr.get("Accept", "application/json")),
                "Accept-Language": "{}".format(reqhdr.get("Accept-Language", "en-US,en;q=0.9")),
                "Authorization": "{}".format(reqhdr.get("Authorization", "Basic <credentials>")),
                "Cache-Control": "no-cache",
                "Content-Type": "{}".format(self.headers['Content-Type']),
                "Content-Length": "{}".format(len(self._content)),
        #
        # TODO prepare the request authentication
        #
	# self.auth = ...
                "Date": "{}".format(datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")),
                "Max-Forward": "10",
                "Pragma": "no-cache",
                "Proxy-Authorization": "Basic dXNlcjpwYXNz",  # example base64
                "Warning": "199 Miscellaneous warning",
                "User-Agent": "{}".format(reqhdr.get("User-Agent", "Chrome/123.0.0.0")),
            }

        fmt_header = f"HTTP/1.1 200 OK\r\n"
        for key, val in headers.items():
            fmt_header += f"{key}: {val}\r\n"
        
        fmt_header += "\r\n"        
        print("[Response] Header built:\n", fmt_header)
        return str(fmt_header).encode('utf-8')


    def build_notfound(self):
        """
        Constructs a standard 404 Not Found HTTP response.

        :rtype bytes: Encoded 404 response.
        """

        return (
                "HTTP/1.1 404 Not Found\r\n"
                "Accept-Ranges: bytes\r\n"
                "Content-Type: text/html\r\n"
                "Content-Length: 13\r\n"
                "Cache-Control: max-age=86000\r\n"
                "Connection: close\r\n"
                "\r\n"
                "404 Not Found"
            ).encode('utf-8')

    def build_unauthorized(self):
        """
        Constructs a standard 401 Unauthorized HTTP response.
        """
        body = b"401 Unauthorized"
        return (
            b"HTTP/1.1 401 Unauthorized\r\n"
            b"Content-Type: text/html\r\n"
            + f"Content-Length: {len(body)}\r\n".encode()
            + b"Connection: close\r\n"
            + b"\r\n"
            + body
        )
    def build_response(self, request):
        """
        Builds a full HTTP response including headers and content based on the request.

        :params request (class:`Request <Request>`): incoming request object.

        :rtype bytes: complete HTTP response using prepared headers and content.
        """

        path = request.path
        mime_type = self.get_mime_type(path)
        print("[Response] {} path {} mime_type {}".format(request.method, request.path, mime_type))

        body_text = request.body.decode() if isinstance(request.body, bytes) else (request.body or "")
        if request.method == "POST" and request.path == "/login":
            print("[Response] Login attempt body:", body_text)
            params = {}
            try:
                for pair in body_text.split("&"):
                    if "=" in pair:
                        k, v = pair.split("=", 1)
                        params[k] = v
            except Exception:
                params = {}

            if params.get("username") == "admin" and params.get("password") == "password":
                # Auth success -> serve index.html and set cookie
                mime_type = self.get_mime_type("index.html")
                base_dir = self.prepare_content_type(mime_type)
                c_len, self._content = self.build_content("index.html", base_dir)

                header = (
                    f"HTTP/1.1 200 OK\r\n"
                    f"Content-Type: text/html\r\n"
                    f"Content-Length: {c_len}\r\n"
                    f"Set-Cookie: auth=true; Path=/; HttpOnly\r\n"
                    f"Connection: close\r\n"
                    "\r\n"
                ).encode("utf-8")
                return header + self._content
            else:
                return self.build_unauthorized()
            
        if request.method == "GET" and request.path == "/login":
            mime_type = self.get_mime_type("login.html")
            base_dir = self.prepare_content_type(mime_type)
            c_len, self._content = self.build_content("login.html", base_dir)
            self._header = (
                f"HTTP/1.1 200 OK\r\n"
                f"Content-Type: text/html\r\n"
                f"Content-Length: {c_len}\r\n"
                f"Connection: close\r\n"
                "\r\n"
            ).encode("utf-8")
            return self._header + self._content
        
        if request.method == "GET" and request.path == "/":
            cookie_header = request.headers.get("cookie", "")
            if "auth=true" in cookie_header or request.cookies.get("auth") == "true":
                mime_type = self.get_mime_type("index.html")
                base_dir = self.prepare_content_type(mime_type)
                c_len, self._content = self.build_content("index.html", base_dir)
                self._header = self.build_response_header(request)
                return self._header + self._content
            else:
                return self.build_unauthorized()
            
        if request.method == "GET" and request.path == "/chat.html":
            cookie_header = request.headers.get("cookie", "")
            if "auth=true" in cookie_header:
                mime_type = self.get_mime_type("chat.html")
                base_dir = self.prepare_content_type(mime_type)
                c_len, self._content = self.build_content("chat.html", base_dir)
                header = (
                    f"HTTP/1.1 200 OK\r\n"
                    f"Content-Type: text/html\r\n"
                    f"Content-Length: {c_len}\r\n"
                    f"Connection: close\r\n\r\n"
                ).encode()
                return header + self._content
            else:
                return self.build_unauthorized()

        base_dir = ""
        if path.endswith('.html') or mime_type == 'text/html':
            base_dir = self.prepare_content_type(mime_type='text/html')
        elif mime_type == 'text/css':
            base_dir = self.prepare_content_type(mime_type='text/css')
        elif mime_type in ['application/javascript', 'text/javascript']:
            base_dir = self.prepare_content_type(mime_type='application/javascript')
        elif mime_type in ['image/png', 'image/jpeg', 'image/jpg', 'image/x-icon']:
            base_dir = self.prepare_content_type(mime_type=mime_type)
        elif mime_type in ['text/plain', 'application/json']:
            base_dir = self.prepare_content_type(mime_type=mime_type)
        else:
            return self.build_notfound()

        c_len, self._content = self.build_content(path, base_dir)
        if self._content == b"404 Not Found":
            return self.build_notfound()
        self._header = self.build_response_header(request)
        return self._header + self._content
                
