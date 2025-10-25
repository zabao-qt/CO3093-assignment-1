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
daemon.request
~~~~~~~~~~~~~~~~~

This module provides a Request object to manage and persist 
request settings (cookies, auth, proxies).
"""
from .dictionary import CaseInsensitiveDict

class Request():
    """The fully mutable "class" `Request <Request>` object,
    containing the exact bytes that will be sent to the server.

    Instances are generated from a "class" `Request <Request>` object, and
    should not be instantiated manually; doing so may produce undesirable
    effects.

    Usage::

      >>> import deamon.request
      >>> req = request.Request()
      ## Incoming message obtain aka. incoming_msg
      >>> r = req.prepare(incoming_msg)
      >>> r
      <Request>
    """
    __attrs__ = [
        "method",
        "url",
        "headers",
        "body",
        "reason",
        "cookies",
        "body",
        "routes",
        "hook",
    ]

    def __init__(self):
        #: HTTP verb to send to the server.
        self.method = None
        #: HTTP URL to send the request to.
        self.url = None
        #: dictionary of HTTP headers.
        self.headers = None
        #: HTTP path
        self.path = None        
        # The cookies set used to create Cookie header
        self.cookies = None
        #: request body to send to the server.
        self.body = None
        #: Routes
        self.routes = {}
        #: Hook point for routed mapped-path
        self.hook = None

    def extract_request_line(self, request):
        try:
            lines = request.splitlines()
            first_line = lines[0]
            method, path, version = first_line.split()

            # if path == '/':
            #     path = '/index.html'
        except Exception:
            return None, None

        return method, path, version
             
    def prepare_headers(self, request):
        """Prepares the given HTTP headers."""
        lines = request.split('\r\n')
        headers = {}
        for line in lines[1:]:
            if ':' in line:
                key, val = line.split(':', 1)
                headers[key.lower().strip()] = val.strip()
        return headers
    
    def parse_prepare(self, cookie_string):
        cookies = {}
        if not cookie_string:
            return cookies
        try:
            tokens = cookie_string.split(';')
            
            for token in tokens:
                token = token.strip()
                if '=' in token:
                    key, value = token.split('=', 1)
                    cookies[key.strip()] = value.strip()
        except Exception:
            print(f"[Request Error] Cookie string is invalid: {cookie_string}")
        return cookies

    def prepare(self, request, routes=None):
        """Prepares the entire request with the given parameters."""

        # Prepare the request line from the request header
        self.method, self.path, self.version = self.extract_request_line(request)
        print("[Request] {} path {} version {}".format(self.method, self.path, self.version))

        #
        # @bksysnet Preapring the webapp hook with WeApRous instance
        # The default behaviour with HTTP server is empty routed
        #
        # TODO manage the webapp hook in this mounting point
        #
        
        if routes is not None and routes != {}:
            self.routes = routes
            self.hook = routes.get((self.method, self.path))
            #
            # self.hook manipulation goes here
            # ...
            #

        self.headers = self.prepare_headers(request)
        cookies = self.headers.get('cookie', '')
        self.cookies = self.parse_prepare(cookies)

        if self.method in ['POST', 'PUT']:
            parts = request.split('\r\n\r\n', 1)
            if len(parts) > 1:
                self.body = parts[1].strip()
            else:
                self.body = ''
        else:
            self.body = ''

        return self

    def prepare_body(self, data=None, files=None, json=None):
        body = b''
        if json is not None:
            self.headers["Content-Type"] = "application/json"
            import json as js
            body = js.dumps(json).encode("utf-8")

        # Prepare form data
        elif data is not None:
            if isinstance(data, dict):
                form_data = "&".join(f"{k}={v}" for k, v in data.items())
                body = form_data.encode("utf-8")
            else:
                body = str(data).encode("utf-8")
            self.headers["Content-Type"] = "application/x-www-form-urlencoded"
        elif files is not None:
            self.headers["Content-Type"] = "application/octet-stream"
            body = files.read()

        self.prepare_content_length(body)
        self.body = body
	# self.auth = ...
        return


    def prepare_content_length(self, body):
        length = len(body) if body else 0
        self.headers["Content-Length"] = str(length)
        return


    def prepare_auth(self, auth, url=""):
        import base64
        if not auth:
            return
        if isinstance(auth, tuple) and len(auth) == 2:
            user_pass = f"{auth[0]}:{auth[1]}".encode("utf-8")
            encoded = base64.b64encode(user_pass).decode("utf-8")
            self.headers["Authorization"] = f"Basic {encoded}"
        elif isinstance(auth, str):
            self.headers["Authorization"] = f"Bearer {auth}"
        return

    def prepare_cookies(self, cookies):
        if not cookies:
            return
        if isinstance(cookies, dict):
            cookie_str = "; ".join(f"{k}={v}" for k, v in cookies.items())
        else:
            cookie_str = str(cookies)
        self.headers["Cookie"] = cookie_str
        return
