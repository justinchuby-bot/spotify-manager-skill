# Spotify Web API — February 2026 Breaking Changes

Spotify enforces these changes for all new Dev Mode apps by default. Existing apps must migrate.

## Playlist Endpoints

**Old → New:**
- `GET /playlists/{id}/tracks` → `GET /playlists/{id}/items`
- `POST /playlists/{id}/tracks` → `POST /playlists/{id}/items`
- `PUT /playlists/{id}/tracks` → `PUT /playlists/{id}/items`
- `DELETE /playlists/{id}/tracks` → `DELETE /playlists/{id}/items`

**DELETE body change:**
```json
// Old
{"tracks": [{"uri": "spotify:track:xxx"}]}

// New
{"items": [{"uri": "spotify:track:xxx"}]}
```

## Library Endpoints

Consolidated to generic endpoints:
- `PUT /me/library` — save any item type
- `DELETE /me/library` — remove any item type

Legacy type-specific endpoints (`/me/tracks`, `/me/albums`, `/me/episodes`) still work but the new unified endpoints are preferred.

## Dev Mode

- New apps default to Dev Mode (enforces Feb 2026 changes)
- Premium required for app owner
- Max 5 authorized users
- 1 client ID per developer
- Submit for quota extension for broader access

## References

- Changes overview: <https://developer.spotify.com/documentation/web-api/references/changes/february-2026>
- Migration guide: <https://developer.spotify.com/documentation/web-api/tutorials/february-2026-migration-guide>
