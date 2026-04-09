# openclaw-spotify

A Spotify skill for [OpenClaw](https://github.com/openclaw/openclaw) — search, playlists, playback control, library management, and listening history.

Fully compliant with Spotify's **February 2026 API changes**.

## Features

- **Search** — tracks, albums, artists
- **Playback** — play, pause, skip, queue, now playing, devices
- **Playlists** — create, list, add/remove items
- **Library** — save/remove any item type (unified endpoint)
- **User data** — top tracks/artists, recently played

## Install

```bash
clawhub install justinchuby-bot/openclaw-spotify
```

Or manually copy the `spotify/` folder into your OpenClaw skills directory (`~/.openclaw/skills/` or `<workspace>/skills/`).

## Setup

1. **Create a Spotify app** at [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard)
   - Click **Create app**
   - **App name:** anything you like (e.g. "My OpenClaw")
   - **App description:** anything (e.g. "Personal Spotify control")
   - **Redirect URI:** `http://127.0.0.1:8888/callback` — click **Add**
   - **Which API/SDKs are you planning to use?** Select **Web API**
   - Check the ToS box and click **Save**
   - Go to **Settings** → copy your **Client ID** and **Client Secret** (click "View client secret")
   - Go to **Settings → User Management** → add your Spotify account email (required for Dev Mode apps to work)

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
python3 spotify/scripts/spotify_api.py search "Bohemian Rhapsody"
python3 spotify/scripts/spotify_api.py now-playing
python3 spotify/scripts/spotify_api.py playlists
python3 spotify/scripts/spotify_api.py top-tracks
python3 spotify/scripts/spotify_api.py save spotify:track:6rqhFgbbKwnb9MLmUQDhG6
```

## Requirements

- Python 3.7+ (stdlib only — no pip dependencies)
- Spotify Premium (required for playback control and Dev Mode apps)
- Linux or macOS

## Feb 2026 API Changes

This skill is fully updated for Spotify's February 2026 breaking changes:
- Playlist endpoints: `/tracks` → `/items`
- Library endpoints: unified `PUT/DELETE /me/library` with Spotify URIs
- Search limit reduced to 10 per request
- Many batch/browse endpoints removed

See [`spotify/references/api-changes-2026.md`](spotify/references/api-changes-2026.md) for full details.

## License

MIT
