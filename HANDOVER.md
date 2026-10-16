# HANDOVER: generated_playlists

Updated 2026-10-16. Read this first in a new session; then wait for Marko's next reference song.

## What this repository is for

Marko (a DJ) sends reference songs, usually screenshots from his DJ app. Claude continues them into a playlist
in the same musical style, then:

1. writes `playlists/YYYY-MM-DD_<style>.txt`: one `Artist - Title` per line, first `#` line = playlist name;
2. creates the playlist on Marko's **TIDAL** account (his DJ app reads TIDAL), name ending in **(generated)**;
3. adds a row with the TIDAL link to the table in `README.md`, saves the reference screenshots in `handover/`,
   commits and pushes.

His rules so far:
- Put **(generated)** in every TIDAL playlist name, so he knows Claude made it.
- Include every song he sends, then continue in the same style up to the length he asks for (last one: 108).
- **The song matters, not the exact version.** If a named remix isn't on TIDAL, use the original or another
  version of the same song. Only swap for a different song when the song itself isn't there, and say so.
- A new reference in a new style becomes a **new** playlist (ask if it's unclear).

## Playlists made

| File | TIDAL | Songs | Notes |
|---|---|---|---|
| `2026-10-16_reggae-vocal-healing.txt` | [Reggae Vocal Healing (generated)](https://tidal.com/playlist/f819de05-39e0-4f6d-ab8e-c270e183d36d) | 36 | Reference: Nalini Blossom - The Water Blessing Song (`handover/reference_nalini-*.png`). Mike Love "Human Revolution" and Koffee "Toast" (only a remix) were swapped for "Love Will Find a Way" and "Raggamuffin". |
| `2026-10-16_nu-disco.txt` | [Nu Disco Chart (generated)](https://tidal.com/playlist/3fb44298-fa71-4bec-8016-eeda23e81105) | 108 | Reference: his DJ app's Nu Disco / Disco chart, #1-17 (`handover/reference_nu-disco-chart_*.png`), then nu disco, disco house, disco pop, classics. #18 was cut off in the screenshot and left out. On TIDAL, "Le Freak" is the original (the script now finds the Dimitri From Paris remix, so a rebuild would use it). |

## The TIDAL tool: `tools/tidal_playlist.py` (stdlib only)

```
python3 tools/tidal_playlist.py login-url                    # prints a TIDAL login URL
python3 tools/tidal_playlist.py login-finish '<localhost URL>'
python3 tools/tidal_playlist.py create playlists/X.txt --dry-run   # check every match first
python3 tools/tidal_playlist.py create playlists/X.txt             # creates the playlist, prints its link
```

- Same TIDAL app and API as Marko's `markoboskoauroville/SCREENSHOT_TO_TIDAL`: the "DJ Mantra" app, client id
  `JjTAmDVohiV7GgOL` (public, no secret), OAuth 2.1 + PKCE, redirect `http://localhost:8765/tidal-callback`,
  API `https://openapi.tidal.com/v2`. Playlists are created `UNLISTED`; tracks are added 20 at a time.
- Token: `~/.config/tidal_generated/token.json` (never commit or print it), or the `TIDAL_REFRESH_TOKEN`
  environment variable. **That variable is not set yet**, so each new container needs the login again.
  Offer Marko once to save it in the environment so future sessions skip the login.
- `create` always makes a **new** playlist; it cannot edit an existing one.

**How matching works** (`find`): it tries searches from exact to loose (full line → title without the
"(... Remix)" → first artist only → title without punctuation, e.g. "D.A.N.C.E." → "DANCE" → title alone) and
stops at a perfect match. A candidate must match the title (≥ 50 % of words) **and** the artist, so another
song by the same artist, or a cover by someone else, is never taken. Among versions of the right song it
prefers, in order: the named remix if the line names one → the plain original → other versions. Remixes,
live, demo, reprise and "Mixed" (cuts from continuous DJ mixes) lose a tie. Lines scoring under 60 % are
reported with `--` and skipped.

If search still can't reach a track, pin it: `Artist - Title [tidal:<track id>]` (used for "Lola's Theme (VIP)").

## Logging in (Marko is on an Android phone)

1. Run `login-url` and send Marko the URL. **All the steps must run in the same container**, because the PKCE
   verifier lives in `~/.config/tidal_generated/pkce.json`.
2. After he logs in, his browser shows **"Unable to connect / localhost"**. This is expected; the code is in the
   address. Because the page is in an in-app browser, the address is hidden: tell him to tap **⋮ → Copy link**
   (or "Open in browser" and copy the address bar) and paste the whole
   `http://localhost:8765/tidal-callback?code=...&state=...` back.
3. `login-finish '<that URL>'`. The scope it prints must include `playlists.write`.

## Environment

- Works in the **Code_Space_108j** environment (Custom network access with `login.tidal.com`,
  `auth.tidal.com`, `openapi.tidal.com`). In the account's Default environment the proxy refused TIDAL.
- Quick check: `for h in login.tidal.com auth.tidal.com openapi.tidal.com; do curl -s -o /dev/null -w "$h %{http_code}\n" https://$h/; done`.
  A 403 or 404 from CloudFront means the host is reachable. A refused CONNECT (403 from the proxy, no
  `server: CloudFront`) means it is blocked: tell Marko which host.

## Git

- Current work: branch `claude/generate-playlist-mpncvw` (contains everything). The older branch
  `ccr-bd69dadb-47iidg` holds the first session's work and the first handover, already merged here.
  No pull request has been opened.

## Open items

- "Apache": Marko mentioned a band with a name like that, singing about women healers, for the reggae style.
  Nobody has identified it yet. If you recognise it, offer to add 1-3 songs.
- `TIDAL_REFRESH_TOKEN` is not saved yet (see above).
