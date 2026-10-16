# generated_playlists

Playlists Claude generates from reference songs, to continue in the same musical style.

- `playlists/YYYY-MM-DD_<style>.txt`: one `Artist - Title` per line. The first `#` line is the playlist name.
  Every playlist made on TIDAL ends in **(generated)**.
- `tools/tidal_playlist.py`: puts a list on TIDAL (same DJ Mantra app and API as SCREENSHOT_TO_TIDAL).

```
python3 tools/tidal_playlist.py login-url                  # open it, log in to TIDAL
python3 tools/tidal_playlist.py login-finish '<the localhost URL the browser landed on>'
python3 tools/tidal_playlist.py create playlists/2026-10-16_reggae-vocal-healing.txt [--dry-run]
```

The cloud environment must allow `login.tidal.com`, `auth.tidal.com` and `openapi.tidal.com`.
The token stays out of the repo (`~/.config/tidal_generated/`), or comes from the `TIDAL_REFRESH_TOKEN` secret.

## Permanent TIDAL access (no login each session)

Do this once, in the cloud environment's settings (environment menu → Edit):
1. Network access: allow `login.tidal.com`, `auth.tidal.com`, `openapi.tidal.com`.
2. Environment variables: add `TIDAL_REFRESH_TOKEN=<token>`. To copy the token on the Mac (the Screenshot to
   TIDAL app is logged in) without showing it on screen:
   `security find-generic-password -s community.auroville.screenshot2tidal -a token-JjTAmDVohiV7GgOL -w | python3 -c 'import json,sys;print(json.load(sys.stdin)["refresh"],end="")' | pbcopy`
3. Start a new session. `tools/tidal_playlist.py create ...` then works with no login.

If TIDAL starts refusing the token (`invalid_grant`), log in again in the Mac app and repeat step 2.

| Date | Playlist | Reference |
|---|---|---|
| 2026-10-16 | Reggae Vocal Healing (generated) | Nalini Blossom - The Water Blessing Song |
| 2026-10-16 | Tech House Groove (generated) | Marko's TIDAL.txt (100 tracks) |
