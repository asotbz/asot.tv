#!/usr/bin/env python3
"""
Tag MTV '120 Minutes' recordings with SxxExx via TheTVDB by matching air date in the filename.

Example filename:
    MTV -120 Minutes and Dream Time -1995-04-23.mkv

What it does:
  1) Parses YYYY-MM-DD from the filename
  2) Logs into TheTVDB v4 with your API key (and optional PIN)
  3) Looks up the series by slug to get its ID
  4) Pages through "official" episodes and finds an episode whose airdate matches
  5) Prints a suggested new name, and optionally renames on disk

Environment:
  export THETVDB_APIKEY="YOUR_V4_API_KEY"
  export THETVDB_PIN="YOUR_SUBSCRIBER_PIN"   # optional, only if your key needs it

Usage:
  python3 thetvdb_airdate_tag.py "/path/MTV -120 Minutes and Dream Time -1995-04-23.mkv"
  python3 thetvdb_airdate_tag.py --rename "/path/to/folder"

Notes:
  - Uses /series/{id}/episodes/official?page=N (no /{lang} in path).
  - Normalizes payloads where "data" may be a list or a dict containing "episodes".
  - Falls back to /episodes/{id} if the list yields IDs instead of objects.
"""

import os
import re
import sys
import json
import time
import argparse
import pathlib
import requests
import typing

API_BASE = "https://api4.thetvdb.com/v4"
DATE_RX = re.compile(r"(?P<date>\d{4}-\d{2}-\d{2})")


def tvdb_login(apikey: str, pin: typing.Optional[str] = None) -> str:
    """Return a bearer token for TheTVDB v4."""
    payload: typing.Dict[str, typing.Any] = {"apikey": apikey}
    if pin:
        payload["pin"] = pin
    r = requests.post(f"{API_BASE}/login", json=payload, timeout=20)
    r.raise_for_status()
    data = r.json()
    return data["data"]["token"]


def get_series_id_by_slug(token: str, slug: str) -> int:
    """Resolve a TheTVDB series ID from a series slug."""
    r = requests.get(
        f"{API_BASE}/series/slug/{slug}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=20,
    )
    r.raise_for_status()
    return int(r.json()["data"]["id"])


def get_episode(token: str, episode_id: int) -> typing.Optional[typing.Dict[str, typing.Any]]:
    """Fetch a single episode record by ID."""
    r = requests.get(
        f"{API_BASE}/episodes/{episode_id}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=20,
    )
    r.raise_for_status()
    return r.json().get("data")


def _normalize_official_page(payload: typing.Dict[str, typing.Any]) -> typing.List[typing.Any]:
    """
    Normalize /series/{id}/episodes/official?page=N results into a list of episode-like items.
    TheTVDB sometimes returns:
      - {"data": [ {...}, {...} ], "links": {...}}
      - {"data": {"episodes": [ {...} ]}, "links": {...}}
      - {"data": {"episodes": [ 12345, 67890 ]}, "links": {...}}  # IDs only
    """
    data = payload.get("data")
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        if isinstance(data.get("episodes"), list):
            return data["episodes"]
        # Fallback: first list-looking value inside data
        for v in data.values():
            if isinstance(v, list):
                return v
    return []


def iter_official_episodes(token: str, series_id: int) -> typing.Iterator[typing.Dict[str, typing.Any]]:
    """
    Iterate 'official' episodes for a series, yielding full episode dicts.
    Handles pages where items may be dicts or bare IDs by hydrating IDs via /episodes/{id}.
    """
    headers = {"Authorization": f"Bearer {token}"}
    page = 0
    while True:
        url = f"{API_BASE}/series/{series_id}/episodes/official?page={page}"
        r = requests.get(url, headers=headers, timeout=30)
        r.raise_for_status()
        payload = r.json()

        items = _normalize_official_page(payload)
        if not items:
            break

        for item in items:
            if isinstance(item, dict):
                yield item
            else:
                # Hydrate ID-like entries
                ep_id: typing.Optional[int] = None
                if isinstance(item, int):
                    ep_id = item
                elif isinstance(item, str):
                    try:
                        ep_id = int(item)
                    except ValueError:
                        ep_id = None
                if ep_id is not None:
                    try:
                        ep = get_episode(token, ep_id)
                        if ep:
                            yield ep
                    except Exception:
                        # Skip any hydration failures and continue
                        continue

        links = payload.get("links") or {}
        next_page = links.get("next")
        if next_page is None:
            break
        try:
            page = int(next_page)
        except Exception:
            # Defensive: if next is malformed, stop
            break


def parse_airdate_from_filename(name: str) -> typing.Optional[str]:
    """Extract YYYY-MM-DD from filename."""
    m = DATE_RX.search(name)
    return m.group("date") if m else None


def proposed_new_name(
    original_path: pathlib.Path,
    series_display: str,
    season: int,
    episode: int,
    airdate: str,
) -> str:
    ext = original_path.suffix
    return f"{series_display} - S{season:02d}E{episode:02d} - {airdate}{ext}"


def resolve_for_file(
    p: pathlib.Path,
    token: str,
    series_id: int,
    series_display: str,
    do_rename: bool,
) -> None:
    airdate = parse_airdate_from_filename(p.name)
    if not airdate:
        print(f"[skip] {p.name} — no YYYY-MM-DD found")
        return

    match: typing.Optional[typing.Dict[str, typing[Any]]] = None
    for ep in iter_official_episodes(token, series_id):
        # Airdate can appear as "aired" or "firstAired"; take first 10 chars for safety.
        fa_raw = ep.get("aired") or ep.get("firstAired") or ""
        fa = str(fa_raw)[:10]
        if fa == airdate:
            match = ep
            break

    if not match:
        print(f"[warn] {p.name} — no TheTVDB episode with airdate {airdate} found")
        return

    season_num = match.get("seasonNumber")
    ep_num = match.get("number") or match.get("episodeNumber")
    if season_num is None or ep_num is None:
        print(f"[warn] {p.name} — found episode for {airdate}, but missing season/episode numbers")
        return

    new_name = proposed_new_name(p, series_display, int(season_num), int(ep_num), airdate)
    print(f"{p.name}  ->  {new_name}   (S{int(season_num):02d}E{int(ep_num):02d})")

    if do_rename:
        try:
            new_path = p.with_name(new_name)
            p.rename(new_path)
        except Exception as e:
            print(f"[error] rename failed for {p.name}: {e}")


def main() -> None:
    apikey = os.getenv("THETVDB_APIKEY")
    pin = os.getenv("THETVDB_PIN")  # optional
    if not apikey:
        print("Set THETVDB_APIKEY (and THETVDB_PIN if applicable) in your environment.", file=sys.stderr)
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description="Tag recordings with SxxExx via TheTVDB (by air date)."
    )
    parser.add_argument("paths", nargs="+", help="Files or directories to scan")
    parser.add_argument("--slug", default="120-minutes", help="TheTVDB series slug (default: 120-minutes)")
    parser.add_argument("--series", default="120 Minutes", help="Series name to use in the new filename")
    parser.add_argument("--rename", action="store_true", help="Actually rename files on disk")
    args = parser.parse_args()

    try:
        token = tvdb_login(apikey, pin)
    except Exception as e:
        print(f"[error] TVDB login failed: {e}", file=sys.stderr)
        sys.exit(2)

    try:
        series_id = get_series_id_by_slug(token, args.slug)
    except Exception as e:
        print(f"[error] Failed to resolve series slug '{args.slug}': {e}", file=sys.stderr)
        sys.exit(3)

    targets: typing.List[pathlib.Path] = []
    for raw in args.paths:
        path = pathlib.Path(raw)
        if path.is_dir():
            for f in sorted(path.iterdir()):
                if f.is_file():
                    targets.append(f)
        else:
            targets.append(path)

    for p in targets:
        resolve_for_file(p, token, series_id, args.series, args.rename)


if __name__ == "__main__":
    main()
