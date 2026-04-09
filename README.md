# openclaw-spotify

A Spotify skill for [OpenClaw](https://github.com/openclaw) — search, playlists, playback control, library management, and listening history.

## Features

- **Search** — tracks, albums, artists
- **Playback** — play, pause, skip, queue, now playing, devices
- **Playlists** — create, list, add/remove items
- **Library** — save/remove tracks, albums, episodes
- **User data** — top tracks/artists, recently played

## Install

```bash
clawhub install justinchuby-bot/openclaw-spotify
```

Or manually copy the `spotify/` folder into your OpenClaw skills directory.

## Setup

1. **Create a Spotify app** at [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard)
   - Set redirect URI to `http://127.0.0.1:8888/callback`

2. **Save credentials:**
   ```bash
   cat > ~/.openclaw/.spotify-credentials << 'EOF'
   SPOTIFY_CLIENT_ID=your_client_id
   SPOTIFY_CLIENT_SECRET=your_client_secret
   EOF
   chmod 600 ~/.openclaw/.spotify-credentials
   ```

3. **Authenticate:**
   ```bash
   python3 spotify/scripts/spotify-auth.py --credentials ~/.openclaw/.spotify-credentials
   ```
   Opens a browser for OAuth. Tokens are saved to `~/.openclaw/.spotify-token.json`.

## Quick Test

```bash
python3 spotify/scripts/spotify-api.py search "Bohemian Rhapsody"
python3 spotify/scripts/spotify-api.py now-playing
python3 spotify/scripts/spotify-api.py playlists
```

## Requirements

- Python 3.7+ (stdlib only — no pip dependencies)
- Spotify Premium (required for playback control in Dev Mode)
- Linux or macOS

## Notes

- Tokens auto-refresh (they expire every hour)
- New Spotify apps use [Dev Mode](https://developer.spotify.com/documentation/web-api) — max 5 users, Premium required for app owner
- Uses the **Feb 2026 API** (`/playlists/{id}/items` instead of `/tracks`). See `spotify/references/api-changes-2026.md` for details.

## License

MIT
