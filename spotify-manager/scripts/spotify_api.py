#!/usr/bin/env python3
"""Spotify Web API helper — Feb 2026 API compliant.

Can be imported as a module or run as CLI.

CLI usage:
    python3 spotify_api.py search "Bohemian Rhapsody"
    python3 spotify_api.py now-playing
    python3 spotify_api.py play | pause | skip | previous
    python3 spotify_api.py queue "spotify:track:xxx"
    python3 spotify_api.py devices
    python3 spotify_api.py playlists
    python3 spotify_api.py create-playlist "My Playlist" --description "desc" --public
    python3 spotify_api.py add-to-playlist PLAYLIST_ID spotify:track:xxx spotify:track:yyy
    python3 spotify_api.py remove-from-playlist PLAYLIST_ID spotify:track:xxx
    python3 spotify_api.py top-tracks [--range short_term|medium_term|long_term]
    python3 spotify_api.py top-artists [--range short_term|medium_term|long_term]
    python3 spotify_api.py recent
    python3 spotify_api.py save spotify:track:xxx spotify:album:yyy
    python3 spotify_api.py unsave spotify:track:xxx

Config (env vars or defaults):
    SPOTIFY_TOKEN_FILE  — path to token JSON (default: ~/.openclaw/.spotify-token.json)
    SPOTIFY_CREDENTIALS — path to credentials file (default: ~/.openclaw/.spotify-credentials)
    SPOTIFY_CLIENT_ID + SPOTIFY_CLIENT_SECRET — alternative to credentials file
"""

import base64
import json
import os
import stat
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://api.spotify.com/v1"
TOKEN_FILE = os.environ.get("SPOTIFY_TOKEN_FILE", os.path.expanduser("~/.openclaw/.spotify-token.json"))
CREDS_FILE = os.environ.get("SPOTIFY_CREDENTIALS", os.path.expanduser("~/.openclaw/.spotify-credentials"))


# ── Credentials & Tokens ────────────────────────────────────────────

def _check_file_permissions(path, label="file"):
    """Warn if sensitive file is world-readable."""
    try:
        mode = os.stat(path).st_mode
        if mode & (stat.S_IRGRP | stat.S_IROTH):
            print(f"⚠️  Warning: {label} ({path}) is readable by others. Run: chmod 600 {path}", file=sys.stderr)
    except OSError:
        pass


def load_credentials():
    """Load client_id and client_secret from env or credentials file."""
    client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")

    if (not client_id or not client_secret) and os.path.exists(CREDS_FILE):
        _check_file_permissions(CREDS_FILE, "credentials file")
        with open(CREDS_FILE) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    k, v = k.strip(), v.strip()
                    if k == "SPOTIFY_CLIENT_ID":
                        client_id = v
                    elif k == "SPOTIFY_CLIENT_SECRET":
                        client_secret = v

    if not client_id or not client_secret:
        raise RuntimeError("Missing SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET")
    return client_id, client_secret


def load_tokens():
    """Load token JSON from file."""
    _check_file_permissions(TOKEN_FILE, "token file")
    with open(TOKEN_FILE) as f:
        return json.load(f)


def save_tokens(tokens):
    """Persist token JSON with restricted permissions."""
    os.makedirs(os.path.dirname(os.path.abspath(TOKEN_FILE)), exist_ok=True)
    with open(TOKEN_FILE, "w") as f:
        json.dump(tokens, f, indent=2)
    os.chmod(TOKEN_FILE, 0o600)


def refresh_access_token(tokens=None):
    """Refresh the access token using the refresh_token grant."""
    if tokens is None:
        tokens = load_tokens()
    client_id, client_secret = load_credentials()

    data = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "refresh_token": tokens["refresh_token"],
    }).encode()

    creds = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    req = urllib.request.Request(
        "https://accounts.spotify.com/api/token",
        data=data,
        headers={
            "Authorization": f"Basic {creds}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    with urllib.request.urlopen(req) as resp:
        new = json.loads(resp.read())

    if "refresh_token" not in new:
        new["refresh_token"] = tokens["refresh_token"]

    new["_refreshed_at"] = int(time.time())
    save_tokens(new)
    return new


def get_token():
    """Return a valid access token, refreshing if near expiry."""
    tokens = load_tokens()
    refreshed_at = tokens.get("_refreshed_at", 0)
    expires_in = tokens.get("expires_in", 3600)
    if time.time() - refreshed_at > expires_in - 120:
        tokens = refresh_access_token(tokens)
    return tokens["access_token"]


# ── HTTP helpers ─────────────────────────────────────────────────────

def _request(method, url, token, data=None, retry_auth=True):
    """Make an authenticated API request. Auto-refreshes token on 401."""
    headers = {"Authorization": f"Bearer {token}"}
    body = None
    if data is not None:
        body = json.dumps(data).encode()
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        if e.code == 401 and retry_auth:
            new_tokens = refresh_access_token()
            return _request(method, url, new_tokens["access_token"], data, retry_auth=False)
        if e.code == 429:
            retry_after = int(e.headers.get("Retry-After", "5"))
            print(f"Rate limited. Waiting {retry_after}s...", file=sys.stderr)
            time.sleep(retry_after)
            return _request(method, url, token, data, retry_auth=retry_auth)
        raise


def api_get(path, token=None, params=None):
    token = token or get_token()
    url = f"{BASE}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    return _request("GET", url, token)


def api_post(path, token=None, data=None):
    token = token or get_token()
    return _request("POST", f"{BASE}{path}", token, data)


def api_put(path, token=None, data=None):
    token = token or get_token()
    return _request("PUT", f"{BASE}{path}", token, data)


def api_delete(path, token=None, data=None):
    token = token or get_token()
    return _request("DELETE", f"{BASE}{path}", token, data)


# ── Search ───────────────────────────────────────────────────────────

def search(query, types="track", limit=5):
    """Search Spotify. types: track,album,artist (comma-separated). Max limit: 10 (Feb 2026)."""
    limit = min(limit, 10)  # Feb 2026: max reduced from 50 to 10
    return api_get("/search", params={"q": query, "type": types, "limit": limit})


# ── Playback ─────────────────────────────────────────────────────────

def now_playing():
    """Get currently playing track."""
    return api_get("/me/player/currently-playing")


def play(context_uri=None, uris=None, device_id=None):
    """Start/resume playback."""
    data = {}
    if context_uri:
        data["context_uri"] = context_uri
    if uris:
        data["uris"] = uris
    path = "/me/player/play"
    if device_id:
        path += f"?device_id={urllib.parse.quote(device_id)}"
    return api_put(path, data=data or None)


def pause():
    return api_put("/me/player/pause")


def skip():
    return api_post("/me/player/next")


def previous():
    return api_post("/me/player/previous")


def queue(uri):
    """Add a track URI to the queue."""
    return api_post(f"/me/player/queue?uri={urllib.parse.quote(uri)}")


def devices():
    return api_get("/me/player/devices")


# ── Playlists (Feb 2026 API — /items not /tracks) ───────────────────

def my_playlists(limit=50):
    return api_get("/me/playlists", params={"limit": limit})


def get_playlist(playlist_id, fields=None):
    params = {}
    if fields:
        params["fields"] = fields
    return api_get(f"/playlists/{playlist_id}", params=params)


def get_playlist_items(playlist_id, limit=100, offset=0):
    """Get playlist items. Uses /items endpoint (Feb 2026 API)."""
    return api_get(f"/playlists/{playlist_id}/items", params={"limit": limit, "offset": offset})


def create_playlist(name, description="", public=False):
    """Create a playlist for the current user. Uses POST /me/playlists (Feb 2026 API)."""
    return api_post("/me/playlists", data={
        "name": name,
        "description": description,
        "public": public,
    })


def add_to_playlist(playlist_id, uris):
    """Add items to playlist. Uses /items endpoint (Feb 2026 API). Max 100 per call."""
    return api_post(f"/playlists/{playlist_id}/items", data={"uris": uris})


def remove_from_playlist(playlist_id, uris):
    """Remove items from playlist. Uses /items endpoint + items body param (Feb 2026 API)."""
    items = [{"uri": uri} for uri in uris]
    return api_delete(f"/playlists/{playlist_id}/items", data={"items": items})


# ── Library (Feb 2026 API — unified /me/library) ─────────────────────

def save_to_library(uris):
    """Save items to library. Accepts Spotify URIs (e.g. spotify:track:xxx). Feb 2026 unified endpoint."""
    return api_put("/me/library", data={"uris": uris})


def remove_from_library(uris):
    """Remove items from library. Accepts Spotify URIs. Feb 2026 unified endpoint."""
    return api_delete("/me/library", data={"uris": uris})


def check_saved(uris):
    """Check if items are in library. Accepts Spotify URIs. Feb 2026 unified endpoint."""
    return api_get("/me/library/contains", params={"uris": ",".join(uris)})


# ── User Data ────────────────────────────────────────────────────────

def me():
    """Get current user profile."""
    return api_get("/me")


def top_tracks(time_range="medium_term", limit=20):
    return api_get("/me/top/tracks", params={"time_range": time_range, "limit": limit})


def top_artists(time_range="medium_term", limit=20):
    return api_get("/me/top/artists", params={"time_range": time_range, "limit": limit})


def recently_played(limit=20):
    return api_get("/me/player/recently-played", params={"limit": limit})


# ── CLI ──────────────────────────────────────────────────────────────

def _fmt_track(t):
    artists = ", ".join(a["name"] for a in t.get("artists", []))
    return f"{t['name']} — {artists}"


def cli():
    if len(sys.argv) < 2:
        print("Usage: spotify_api.py <command> [args]")
        print("Commands: search, now-playing, play, pause, skip, previous, queue,")
        print("          devices, playlists, create-playlist, add-to-playlist,")
        print("          remove-from-playlist, top-tracks, top-artists, recent,")
        print("          save, unsave")
        sys.exit(1)

    cmd = sys.argv[1]

    try:
        if cmd == "search":
            q = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else input("Search: ")
            r = search(q)
            for t in r.get("tracks", {}).get("items", []):
                print(f"  {_fmt_track(t)}  [{t['uri']}]")

        elif cmd == "now-playing":
            r = now_playing()
            if r and r.get("item"):
                t = r["item"]
                print(f"Now playing: {_fmt_track(t)}")
                print(f"  Progress: {r.get('progress_ms', 0) // 1000}s / {t.get('duration_ms', 0) // 1000}s")
            else:
                print("Nothing playing")

        elif cmd == "play":
            play()
            print("Resumed playback")

        elif cmd == "pause":
            pause()
            print("Paused")

        elif cmd == "skip":
            skip()
            print("Skipped")

        elif cmd == "previous":
            previous()
            print("Previous track")

        elif cmd == "queue":
            if len(sys.argv) < 3:
                print("Usage: spotify_api.py queue <spotify:track:URI>")
                sys.exit(1)
            queue(sys.argv[2])
            print(f"Queued: {sys.argv[2]}")

        elif cmd == "devices":
            r = devices()
            for d in r.get("devices", []):
                active = " (active)" if d.get("is_active") else ""
                print(f"  {d['name']} [{d['type']}]{active} — {d['id']}")

        elif cmd == "playlists":
            r = my_playlists()
            for p in r.get("items", []):
                total = (p.get("items") or {}).get("total", "?")
                print(f"  {p['name']} ({total} items) [{p['id']}]")

        elif cmd == "create-playlist":
            name = sys.argv[2] if len(sys.argv) > 2 else input("Playlist name: ")
            desc = ""
            pub = False
            if "--description" in sys.argv:
                idx = sys.argv.index("--description")
                desc = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else ""
            if "--public" in sys.argv:
                pub = True
            p = create_playlist(name, desc, pub)
            print(f"Created: {p['name']} [{p['id']}]")
            print(f"  https://open.spotify.com/playlist/{p['id']}")

        elif cmd == "add-to-playlist":
            if len(sys.argv) < 4:
                print("Usage: spotify_api.py add-to-playlist PLAYLIST_ID uri1 uri2 ...")
                sys.exit(1)
            pid = sys.argv[2]
            uris = sys.argv[3:]
            add_to_playlist(pid, uris)
            print(f"Added {len(uris)} items to {pid}")

        elif cmd == "remove-from-playlist":
            if len(sys.argv) < 4:
                print("Usage: spotify_api.py remove-from-playlist PLAYLIST_ID uri1 uri2 ...")
                sys.exit(1)
            pid = sys.argv[2]
            uris = sys.argv[3:]
            remove_from_playlist(pid, uris)
            print(f"Removed {len(uris)} items from {pid}")

        elif cmd == "top-tracks":
            tr = "medium_term"
            if "--range" in sys.argv:
                idx = sys.argv.index("--range")
                tr = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else tr
            r = top_tracks(time_range=tr)
            for i, t in enumerate(r.get("items", []), 1):
                print(f"  {i}. {_fmt_track(t)}")

        elif cmd == "top-artists":
            tr = "medium_term"
            if "--range" in sys.argv:
                idx = sys.argv.index("--range")
                tr = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else tr
            r = top_artists(time_range=tr)
            for i, a in enumerate(r.get("items", []), 1):
                print(f"  {i}. {a['name']} ({', '.join(a.get('genres', [])[:3])})")

        elif cmd == "recent":
            r = recently_played()
            for item in r.get("items", []):
                t = item["track"]
                print(f"  {_fmt_track(t)}  [{item.get('played_at', '')}]")

        elif cmd == "save":
            if len(sys.argv) < 3:
                print("Usage: spotify_api.py save spotify:track:xxx spotify:album:yyy ...")
                sys.exit(1)
            uris = sys.argv[2:]
            save_to_library(uris)
            print(f"Saved {len(uris)} items to library")

        elif cmd == "unsave":
            if len(sys.argv) < 3:
                print("Usage: spotify_api.py unsave spotify:track:xxx ...")
                sys.exit(1)
            uris = sys.argv[2:]
            remove_from_library(uris)
            print(f"Removed {len(uris)} items from library")

        else:
            print(f"Unknown command: {cmd}")
            sys.exit(1)

    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        print(f"HTTP {e.code}: {body}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    cli()
