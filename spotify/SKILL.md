---
name: spotify
description: Control Spotify — search, playlists, playback, library, user data. Use when user asks to play music, create playlists, search for tracks/albums/artists, control playback (play/pause/skip/queue), manage their Spotify library (save/remove), or view listening history (top tracks, recently played). Requires user to complete OAuth setup first.
---

# Spotify

Control Spotify via the Web API. All operations use `scripts/spotify_api.py` (stdlib only, no pip deps).

## Setup

Before first use, the user must:

1. **Create a Spotify app** at <https://developer.spotify.com/dashboard>
   - Set redirect URI to `http://127.0.0.1:8888/callback`
   - Note the Client ID and Client Secret
   - **Add their Spotify email** in Settings → User Management

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

## Dev Mode Limitations (Feb 2026)

- Premium required for the app owner
- Max 5 authorized users
- 1 client ID per developer account
- Many endpoints removed or renamed — see `references/api-changes-2026.md`

## CLI Usage

```bash
python3 scripts/spotify_api.py search "Bohemian Rhapsody"
python3 scripts/spotify_api.py now-playing
python3 scripts/spotify_api.py play | pause | skip | previous
python3 scripts/spotify_api.py queue "spotify:track:xxx"
python3 scripts/spotify_api.py devices
python3 scripts/spotify_api.py playlists
python3 scripts/spotify_api.py create-playlist "My Playlist" --description "desc"
python3 scripts/spotify_api.py add-to-playlist PLAYLIST_ID spotify:track:xxx
python3 scripts/spotify_api.py remove-from-playlist PLAYLIST_ID spotify:track:xxx
python3 scripts/spotify_api.py top-tracks [--range short_term|medium_term|long_term]
python3 scripts/spotify_api.py top-artists [--range short_term|medium_term|long_term]
python3 scripts/spotify_api.py recent
python3 scripts/spotify_api.py save spotify:track:xxx spotify:album:yyy
python3 scripts/spotify_api.py unsave spotify:track:xxx
```

## Module Usage

```python
import importlib.util, sys, pathlib
spec = importlib.util.spec_from_file_location("spotify_api", pathlib.Path(__file__).parent / "scripts/spotify_api.py")
spotify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(spotify)

results = spotify.search("Daft Punk", types="track", limit=5)
spotify.play(uris=["spotify:track:xxx"])
spotify.pause()
spotify.skip()
np = spotify.now_playing()
spotify.create_playlist("Weekend Vibes", description="Chill tracks")
spotify.add_to_playlist("playlist_id", ["spotify:track:xxx"])
spotify.remove_from_playlist("playlist_id", ["spotify:track:xxx"])
spotify.save_to_library(["spotify:track:xxx", "spotify:album:yyy"])
spotify.remove_from_library(["spotify:track:xxx"])
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
3. `add_to_playlist(playlist_id, uris)` — max 100 per call

### Check listening history
- `top_tracks(time_range="short_term")` — last 4 weeks
- `top_tracks(time_range="medium_term")` — last 6 months
- `recently_played()` — last 50 tracks

## Key API Notes

- Tokens expire every hour; the script auto-refreshes on 401 or near-expiry
- 429 rate limits are auto-retried with Retry-After
- Playback control requires an active Spotify session (Premium)
- Search max limit is **10** per request (paginate with offset for more)
- **Feb 2026 breaking changes** are fully handled in the scripts. If you encounter 403/404, see `references/api-changes-2026.md`
