#!/usr/bin/env python3
"""Get a TIDAL refresh token on an Android phone (Termux), for TIDAL_REFRESH_TOKEN.

Same TIDAL app as SCREENSHOT_TO_TIDAL (DJ Mantra, client id JjTAmDVohiV7GgOL, OAuth 2.1 + PKCE).
It listens on localhost:8765 (the app's registered redirect), opens TIDAL's login in the phone's
browser, catches the code, swaps it for tokens and copies the refresh token to the clipboard
(termux-clipboard-set, from the Termux:API app), or prints it if that is missing.

    pkg install python termux-api        # termux-api is optional (clipboard + opening the browser)
    python tidal_token_termux.py
"""
import base64, hashlib, http.server, json, secrets, shutil, subprocess, sys, threading
import urllib.error, urllib.parse, urllib.request

CLIENT_ID = "JjTAmDVohiV7GgOL"
PORT = 8765
REDIRECT = f"http://localhost:{PORT}/tidal-callback"
SCOPES = "user.read search.read playlists.read playlists.write"


def b64url(b):
    return base64.urlsafe_b64encode(b).decode().rstrip("=")


verifier = b64url(secrets.token_bytes(48))
state = b64url(secrets.token_bytes(16))
url = "https://login.tidal.com/authorize?" + urllib.parse.urlencode({
    "response_type": "code", "client_id": CLIENT_ID, "redirect_uri": REDIRECT, "scope": SCOPES,
    "code_challenge_method": "S256", "code_challenge": b64url(hashlib.sha256(verifier.encode()).digest()),
    "state": state})
got = {}
done = threading.Event()


class Catch(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        if u.path != "/tidal-callback":
            self.send_response(404); self.end_headers(); return
        got.update(urllib.parse.parse_qsl(u.query))
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write("<h2>TIDAL login received. Go back to Termux.</h2>".encode())
        done.set()

    def log_message(self, *a):
        pass


srv = http.server.HTTPServer(("127.0.0.1", PORT), Catch)
threading.Thread(target=srv.serve_forever, daemon=True).start()

print("Opening TIDAL login. If the browser does not open, open this link yourself:\n\n" + url + "\n")
if shutil.which("termux-open-url"):
    subprocess.run(["termux-open-url", url])
print("Waiting for the login (up to 15 minutes)...")
if not done.wait(900):
    sys.exit("No login came back in 15 minutes.")
srv.shutdown()

if "error" in got:
    sys.exit(f"TIDAL login error: {got['error']} {got.get('error_description', '')}")
if got.get("state") != state or "code" not in got:
    sys.exit("TIDAL login: state mismatch or no code.")

body = urllib.parse.urlencode({"grant_type": "authorization_code", "client_id": CLIENT_ID, "code": got["code"],
                               "redirect_uri": REDIRECT, "code_verifier": verifier, "scope": SCOPES}).encode()
req = urllib.request.Request("https://auth.tidal.com/v1/oauth2/token", body,
                             {"Content-Type": "application/x-www-form-urlencoded"})
try:
    with urllib.request.urlopen(req) as r:
        tok = json.load(r)
except urllib.error.HTTPError as e:
    sys.exit(f"TIDAL token error {e.code}: {e.read().decode()}")

refresh = tok.get("refresh_token")
if not refresh:
    sys.exit("TIDAL gave no refresh token.")
scope = tok.get("scope", "")
print("Logged in. Scope:", scope or "(not reported)")
if scope and "playlists.write" not in scope.split():
    print("WARNING: no playlists.write; add it to the DJ Mantra app on developer.tidal.com, then run this again.")

if shutil.which("termux-clipboard-set"):
    subprocess.run(["termux-clipboard-set"], input=refresh.encode())
    print("\nThe refresh token is in the clipboard. Paste it as the value of TIDAL_REFRESH_TOKEN.")
else:
    print("\nTIDAL_REFRESH_TOKEN value (copy it; do not share it):\n\n" + refresh + "\n")
