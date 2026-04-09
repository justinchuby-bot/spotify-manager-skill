#!/usr/bin/env python3
"""Spotify OAuth2 Authorization Flow — run locally to get access + refresh tokens.

Usage:
    # Using env vars:
    export SPOTIFY_CLIENT_ID=xxx
    export SPOTIFY_CLIENT_SECRET=xxx
    python3 spotify-auth.py

    # Using credentials file:
    python3 spotify-auth.py --credentials /path/to/creds

    # Custom token output path:
    python3 spotify-auth.py --token-file /path/to/token.json

Credentials file format (one per line):
    SPOTIFY_CLIENT_ID=xxx
    SPOTIFY_CLIENT_SECRET=xxx
    SPOTIFY_REDIRECT_URI=http://127.0.0.1:8888/callback  (optional)
"""

import argparse
import base64
import http.server
import json
import os
import secrets
import sys
import urllib.parse
import urllib.request

DEFAULT_REDIRECT_URI = "http://127.0.0.1:8888/callback"
DEFAULT_TOKEN_FILE = os.path.expanduser("~/.openclaw/.spotify-token.json")

SCOPES = " ".join([
    "user-read-playback-state",
    "user-modify-playback-state",
    "user-read-currently-playing",
    "playlist-read-private",
    "playlist-read-collaborative",
    "playlist-modify-public",
    "playlist-modify-private",
    "user-library-read",
    "user-library-modify",
    "user-top-read",
    "user-read-recently-played",
])

auth_code = None
auth_error = None


def load_credentials(creds_path=None):
    """Load client_id and client_secret from file or env vars."""
    client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")
    redirect_uri = os.environ.get("SPOTIFY_REDIRECT_URI", DEFAULT_REDIRECT_URI)

    if creds_path:
        with open(creds_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    key, val = key.strip(), val.strip()
                    if key == "SPOTIFY_CLIENT_ID":
                        client_id = val
                    elif key == "SPOTIFY_CLIENT_SECRET":
                        client_secret = val
                    elif key == "SPOTIFY_REDIRECT_URI":
                        redirect_uri = val

    if not client_id or not client_secret:
        print("Error: SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET required.", file=sys.stderr)
        print("Set env vars or pass --credentials /path/to/file", file=sys.stderr)
        sys.exit(1)

    return client_id, client_secret, redirect_uri


class CallbackHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code, auth_error
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)

        # CSRF check: verify state matches
        returned_state = params.get("state", [None])[0]
        if returned_state != self.server.expected_state:
            self.send_response(400)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><body><h1>Error: state mismatch (possible CSRF). Try again.</h1></body></html>")
            auth_error = "state mismatch"
            return

        if "code" in params:
            auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><body><h1>Success! You can close this tab.</h1></body></html>")
        elif "error" in params:
            auth_error = params["error"][0]
            self.send_response(400)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            msg = params["error"][0]
            self.wfile.write(f"<html><body><h1>Error: {msg}</h1></body></html>".encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass


def exchange_code(code, client_id, client_secret, redirect_uri):
    """Exchange authorization code for access + refresh tokens."""
    data = urllib.parse.urlencode({
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
    }).encode()

    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    req = urllib.request.Request(
        "https://accounts.spotify.com/api/token",
        data=data,
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )

    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def main():
    parser = argparse.ArgumentParser(description="Spotify OAuth2 flow")
    parser.add_argument("--credentials", help="Path to credentials file")
    parser.add_argument("--token-file", default=DEFAULT_TOKEN_FILE, help="Where to save tokens")
    args = parser.parse_args()

    client_id, client_secret, redirect_uri = load_credentials(args.credentials)

    # Parse port from redirect URI
    parsed = urllib.parse.urlparse(redirect_uri)
    port = parsed.port or 8888

    # Generate random state for CSRF protection
    state = secrets.token_urlsafe(32)

    # Build auth URL
    params = urllib.parse.urlencode({
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "scope": SCOPES,
        "state": state,
    })
    auth_url = f"https://accounts.spotify.com/authorize?{params}"

    print(f"\nSpotify Authorization")
    print(f"\nOpen this URL in your browser:\n")
    print(f"  {auth_url}\n")

    # Start callback server with expected state
    server = http.server.HTTPServer(("127.0.0.1", port), CallbackHandler)
    server.expected_state = state
    print(f"Waiting for callback on {redirect_uri} ...")

    while auth_code is None and auth_error is None:
        server.handle_request()

    server.server_close()

    if auth_error:
        print(f"\nAuthorization failed: {auth_error}", file=sys.stderr)
        sys.exit(1)

    # Exchange code for tokens
    print("\nExchanging code for tokens...")
    tokens = exchange_code(auth_code, client_id, client_secret, redirect_uri)

    # Save tokens
    os.makedirs(os.path.dirname(os.path.abspath(args.token_file)), exist_ok=True)
    with open(args.token_file, "w") as f:
        json.dump(tokens, f, indent=2)
    os.chmod(args.token_file, 0o600)

    print(f"\nToken saved to {args.token_file}")
    print(f"  Access token expires in {tokens.get('expires_in', '?')} seconds")
    print(f"  Refresh token: {'yes' if tokens.get('refresh_token') else 'no'}")
    print(f"  Scopes: {tokens.get('scope', '?')}")


if __name__ == "__main__":
    main()
