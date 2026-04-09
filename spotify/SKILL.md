---
name: spotify
description: Control Spotify — search, playlists, playback, library, user data. Use when user asks to play music, create playlists, search for tracks/albums/artists, control playback (play/pause/skip/queue), manage their Spotify library (save/remove), or view listening history (top tracks, recently played). Requires user to complete OAuth setup first.
---

# Spotify

Control Spotify via the Web API. All operations use `scripts/spotify-api.py` (stdlib only, no pip deps).

## Setup

Before first use, the user must:

1. **Create a Spotify app** at <https://developer.spotify.com/dashboard>
   - Set redirect URI to `http://127.0.0.1:8888/callback`
   - Note the Client ID and Client Secret

2. **Save credentials** to `~/.openclaw/.spotify-credentials`:
   ```
   SPOTIFY_CLIENT_ID=your_client_id
   SPOTIFY_CLIENT_SECRET=your_client_secret
   ```
   Then `chmod 600 ~/.openclaw/.spotify-credentials`.

3. **Run the auth flow** (requires browser access):
   ```bash
   python3 scripts/spotify-auth.py --credentials ~/.openclaw/.spotify-credentials
   ```
   This saves tokens to `~/.openclaw/.spotify-token.json`.

If setup is not done, guide the user through these steps. The auth flow needs a browser — if running headless, print the URL for the user to open manually.

## Dev Mode Limitations

New Spotify apps start in Dev Mode:
- Premium required for the app owner
- Max 5 authorized users
- 1 client ID per developer account

For broader access, the app must be submitted for quota extension.

## Using the API Script

`scripts/spotify-api.py` works both as CLI and importable module.

### CLI usage

```bash
python3 scripts/spotify-api.py search "Bohemian Rhapsody"
python3 scripts/spotify-api.py now-playing
python3 scripts/spotify-api.py play
python3 scripts/spotify-api.py pause
python3 scripts/spotify-api.py skip
python3 scripts/spotify-api.py queue "spotify:track:xxx"
python3 scripts/spotify-api.py playlists
python3 scripts/spotify-api.py create-playlist "My Playlist" --description "desc"
python3 scripts/spotify-api.py add-to-playlist PLAYLIST_ID spotify:track:xxx
python3 scripts/spotify-api.py top-tracks
python3 scripts/spotify-api.py recent
python3 scripts/spotify-api.py devices
```

### As module (from Python)

```python
import importlib.util, sys
spec = importlib.util.spec_from_file_location("spotify", "scripts/spotify-api.py")
spotify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(spotify)

# Search
results = spotify.search("Daft Punk", types="track", limit=3)

# Playback
spotify.play(uris=["spotify:track:xxx"])
spotify.pause()
spotify.skip()
np = spotify.now_playing()

# Playlists
spotify.create_playlist("Weekend Vibes", description="Chill tracks")
spotify.add_to_playlist("playlist_id", ["spotify:track:xxx"])
spotify.remove_from_playlist("playlist_id", ["spotify:track:xxx"])

# Library
spotify.save_to_library(["track_id_1", "track_id_2"])
spotify.remove_from_library(["track_id_1"])

# User data
spotify.top_tracks(time_range="short_term")
spotify.recently_played()
```

Token refresh is automatic — no manual intervention needed.

## Common Workflows

### Play a song by name
1. `search("song name")` → get URI from results
2. `play(uris=[uri])` or `queue(uri)`

### Create a themed playlist
1. Search for tracks matching the theme
2. `create_playlist("name")` → get playlist ID
3. `add_to_playlist(playlist_id, uris)`

### Check listening history
- `top_tracks(time_range="short_term")` — last 4 weeks
- `top_tracks(time_range="medium_term")` — last 6 months
- `recently_played()` — last 50 tracks

## API Notes

- Tokens expire every hour; the script auto-refreshes
- Playback control requires an active Spotify session (Premium)
- Rate limits: back off on 429 responses
- **Feb 2026 breaking changes** apply — see `references/api-changes-2026.md` if you hit playlist/library endpoint issues
