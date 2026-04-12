# spotify-manager-skill

A Spotify skill for [OpenClaw](https://github.com/openclaw/openclaw) — search, playlists, playback control, library management, and listening history.

Fully compliant with Spotify's **February 2026 API changes**.

## Features

- **Search** — tracks, albums, artists
- **Playback** — play, pause, skip, queue, now playing, devices
- **Playlists** — create, list, add/remove items
- **Library** — save/remove any item type (unified endpoint)
- **User data** — top tracks/artists, recently played

## Install

### Via ClawHub registry

```bash
clawhub install spotify-manager
```

> **Note:** The slug is `spotify-manager`, not the GitHub path. `clawhub install` uses the ClawHub registry, not GitHub URLs.

### Manual install from GitHub

If the skill is not yet on the ClawHub registry, or you prefer to install from source:

```bash
git clone https://github.com/justinchuby-bot/spotify-manager-skill.git ~/spotify-manager-skill
mkdir -p ~/.openclaw/skills
cp -r ~/spotify-manager-skill/spotify-manager ~/.openclaw/skills/
```

You can remove the cloned repo afterwards if you no longer need it:

```bash
rm -rf ~/spotify-manager-skill
```

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

   If installed via `clawhub install`:
   ```bash
   python3 spotify-manager/scripts/spotify-auth.py --credentials ~/.openclaw/.spotify-credentials
   ```

   If installed manually to `~/.openclaw/skills/`:
   ```bash
   python3 ~/.openclaw/skills/spotify-manager/scripts/spotify-auth.py --credentials ~/.openclaw/.spotify-credentials
   ```
   Opens a browser for OAuth. Tokens are saved to `~/.openclaw/.spotify-token.json`.

   > **Remote server users:** The OAuth callback must reach port 8888 on the server. Choose one of:
   >
   > - **VS Code Remote SSH:** Press `Ctrl+Shift+P` → "Forward a Port" → enter `8888`
   > - **SSH port forwarding:** From your **local machine**, connect with:
   >   ```
   >   ssh -L 8888:127.0.0.1:8888 user@your-server
   >   ```
   >   Then run the auth script in that SSH session.
   >
   > If you get `OSError: [Errno 98] Address already in use`, a previous auth attempt may still be holding the port. Kill it with:
   > ```
   > lsof -ti :8888 | xargs kill -9
   > ```
   > Then retry the auth script.

## Quick Test

If installed via `clawhub install`:
```bash
python3 spotify-manager/scripts/spotify_api.py search "Bohemian Rhapsody"
python3 spotify-manager/scripts/spotify_api.py now-playing
python3 spotify-manager/scripts/spotify_api.py playlists
python3 spotify-manager/scripts/spotify_api.py top-tracks
python3 spotify-manager/scripts/spotify_api.py save spotify:track:6rqhFgbbKwnb9MLmUQDhG6
```

If installed manually to `~/.openclaw/skills/`:
```bash
python3 ~/.openclaw/skills/spotify-manager/scripts/spotify_api.py search "Bohemian Rhapsody"
python3 ~/.openclaw/skills/spotify-manager/scripts/spotify_api.py now-playing
python3 ~/.openclaw/skills/spotify-manager/scripts/spotify_api.py playlists
python3 ~/.openclaw/skills/spotify-manager/scripts/spotify_api.py top-tracks
python3 ~/.openclaw/skills/spotify-manager/scripts/spotify_api.py save spotify:track:6rqhFgbbKwnb9MLmUQDhG6
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

See [`spotify-manager/references/api-changes-2026.md`](spotify-manager/references/api-changes-2026.md) for full details.

## License

MIT
