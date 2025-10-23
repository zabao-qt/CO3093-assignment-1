from daemon.request import Request
from daemon.response import Response

def simulate(raw_request):
    req = Request()
    req.prepare(raw_request)
    resp = Response()
    result = resp.build_response(req)
    print(result.decode(errors="ignore"))
    print("-" * 80)

# === TEST 1: GET /index.html ===
print("=== Test 1: GET /index.html ===")
simulate(
    "GET /index.html HTTP/1.1\r\n"
    "Host: localhost\r\n"
    "User-Agent: curl/8.1\r\n\r\n"
)

# === TEST 2: GET / (no cookie) ===
print("=== Test 2: GET / (no cookie) ===")
simulate(
    "GET / HTTP/1.1\r\n"
    "Host: localhost\r\n"
    "User-Agent: curl/8.1\r\n\r\n"
)

# === TEST 3: GET / (with auth cookie) ===
print("=== Test 3: GET / (with auth cookie) ===")
simulate(
    "GET / HTTP/1.1\r\n"
    "Host: localhost\r\n"
    "Cookie: auth=true; theme=light\r\n"
    "User-Agent: curl/8.1\r\n\r\n"
)

# === TEST 4: POST /login (success) ===
print("=== Test 4: POST /login (success) ===")
simulate(
    "POST /login HTTP/1.1\r\n"
    "Host: localhost\r\n"
    "Content-Type: application/x-www-form-urlencoded\r\n"
    "Content-Length: 32\r\n\r\n"
    "username=admin&password=password"
)

# === TEST 5: POST /login (wrong password) ===
print("=== Test 5: POST /login (wrong password) ===")
simulate(
    "POST /login HTTP/1.1\r\n"
    "Host: localhost\r\n"
    "Content-Type: application/x-www-form-urlencoded\r\n"
    "Content-Length: 27\r\n\r\n"
    "username=admin&password=wrong"
)

# === TEST 6: GET /not_exist.html ===
print("=== Test 6: GET /not_exist.html ===")
simulate(
    "GET /not_exist.html HTTP/1.1\r\n"
    "Host: localhost\r\n"
    "User-Agent: curl/8.1\r\n\r\n"
)
