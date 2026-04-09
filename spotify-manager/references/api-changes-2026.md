# Spotify Web API — February 2026 Breaking Changes

Reference this when encountering unexpected 403/404 errors. These changes are mandatory for all Dev Mode apps.

Source: <https://developer.spotify.com/documentation/web-api/references/changes/february-2026>
Migration guide: <https://developer.spotify.com/documentation/web-api/tutorials/february-2026-migration-guide>

## Playlist Endpoints — Renamed

| Old (REMOVED) | New |
|---|---|
| `POST /playlists/{id}/tracks` | `POST /playlists/{id}/items` |
| `GET /playlists/{id}/tracks` | `GET /playlists/{id}/items` |
| `PUT /playlists/{id}/tracks` | `PUT /playlists/{id}/items` |
| `DELETE /playlists/{id}/tracks` | `DELETE /playlists/{id}/items` |

DELETE body param also renamed: `tracks` → `items`.

Response field rename: `tracks` → `items`, `tracks.tracks` → `items.items`, `tracks.tracks.track` → `items.items.item`.

Playlist items only returned for playlists the user owns or collaborates on. Other playlists return metadata only.

## Library Endpoints — Unified

All type-specific save/remove/check endpoints replaced with generic ones using Spotify URIs:

| Old (REMOVED) | New |
|---|---|
| `PUT /me/tracks`, `PUT /me/albums`, `PUT /me/following`, etc. | `PUT /me/library` (body: `{"uris": [...]}`) |
| `DELETE /me/tracks`, `DELETE /me/albums`, `DELETE /me/following`, etc. | `DELETE /me/library` (body: `{"uris": [...]}`) |
| `GET /me/tracks/contains`, `GET /me/albums/contains`, etc. | `GET /me/library/contains` (param: `uris=...`) |

URIs are full Spotify URIs: `spotify:track:xxx`, `spotify:album:xxx`, `spotify:artist:xxx`.

## Playlist Creation — Changed

| Old (REMOVED) | New |
|---|---|
| `POST /users/{user_id}/playlists` | `POST /me/playlists` |

## Batch/Bulk Endpoints — Removed (no replacement)

`GET /tracks`, `GET /albums`, `GET /artists`, `GET /episodes`, `GET /shows`, `GET /audiobooks`, `GET /chapters` — all removed. Fetch individually: `GET /tracks/{id}`, etc.

## Browse & Discovery — Removed (no replacement)

- `GET /browse/new-releases`
- `GET /browse/categories` and `GET /browse/categories/{id}`
- `GET /artists/{id}/top-tracks`
- `GET /markets`

## Other User Data — Removed

- `GET /users/{id}` — use `GET /me` for current user
- `GET /users/{id}/playlists` — use `GET /me/playlists`

## Search Limit Change

`GET /search` — max `limit` reduced from 50 to **10**, default from 20 to **5**. Paginate with `offset` for more results.

## Removed Response Fields

Across all endpoints:
- **Track:** `available_markets`, `linked_from`, `popularity` removed. (`external_ids` restored in March 2026.)
- **Album:** `album_group`, `available_markets`, `label`, `popularity` removed.
- **Artist:** `followers`, `popularity` removed.
- **User (GET /me):** `country`, `email`, `explicit_content`, `followers`, `product` removed.
- **Show:** `available_markets`, `publisher` removed.

## Dev Mode Restrictions

- Premium required for app owner
- Max 5 authorized users per app
- 1 client ID per developer
- Add users in Dashboard → Settings → User Management
- For broader access: apply for Extended Quota Mode
