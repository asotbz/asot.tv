#!/usr/bin/env python3
import os, re, sys, json, time, argparse, pathlib
import requests

API_BASE = "https://api4.thetvdb.com/v4"

def tvdb_login(apikey: str, pin: str | None = None) -> str:
    payload = {"apikey": apikey}
    if pin:
        payload["pin"] = pin
    r = requests.post(f"{API_BASE}/login", json=payload, timeout=20)
    r.raise_for_status()
    return r.json()["data"]["token"]

def get_series_id_by_slug(token: str, slug: str) -> int:
    # e.g., slug "120-minutes" → series page: https://thetvdb.com/series/120-minutes
    # v4: GET /series/slug/{slug}
    r = requests.get(
        f"{API_BASE}/series/slug/{slug}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=20,
    )
    r.raise_for_status()
    return r.json()["data"]["id"]

def iter_official_episodes(token: str, series_id: int, lang: str = "eng"):
    # v4: GET /series/{id}/episodes/official/{lang}?page=N
    page = 0
    headers = {"Authorization": f"Bearer {token}"}
    while True:
        url = f"{API_BASE}/series/{series_id}/episodes/official/{lang}?page={page}"
        r = requests.get(url, headers=headers, timeout=30)
        r.raise_for_status()
        data = r.json()
        eps = data.get("data", [])
        if not eps:
            break
        for ep in eps:
            yield ep
        if not data.get("links") or data["links"].get("next") is None:
            break
        page = data["links"]["next"]

DATE_RX = re.compile(r"(?P<date>\d{4}-\d{2}-\d{2})")

def parse_airdate_from_filename(name: str) -> str | None:
    m = DATE_RX.search(name)
    return m.group("date") if m else None

def clean_series_name(name: str) -> str:
    # Your file might read "120 Minutes and Dream Time" for a combined capture.
    # Keep the primary show before " and ".
    base = name.strip()
    if " and " in base.lower():
        base = base.split(" and ", 1)[0]
    # Normalize some common spacing artifacts after prefixes like "MTV -"
    base = base.replace("MTV -", "").strip()
    return base

def proposed_new_name(original_path: pathlib.Path, series: str, season: int, episode: int, airdate: str) -> str:
    ext = original_path.suffix
    return f"{series} - S{season:0>2}E{episode:0>2} - {airdate}{ext}"

def resolve_for_file(p: pathlib.Path, token: str, series_slug: str, do_rename: bool):
    airdate = parse_airdate_from_filename(p.name)
    if not airdate:
        print(f"[skip] {p.name} — no YYYY-MM-DD found")
        return

    series_id = get_series_id_by_slug(token, series_slug)

    match = None
    for ep in iter_official_episodes(token, series_id):
        # v4 payloads can use `aired` or `firstAired`; be tolerant
        fa = ep.get("aired") or ep.get("firstAired")
        if fa == airdate:
            match = ep
            break

    if not match:
        print(f"[warn] {p.name} — no TheTVDB episode with airdate {airdate} found")
        return

    season_num = match.get("seasonNumber")
    ep_num = match.get("number") or match.get("episodeNumber")
    if season_num is None or ep_num is None:
        print(f"[warn] {p.name} — episode found for {airdate}, but missing season/episode numbers")
        return

    # Build a tidy rename (don’t actually rename unless --rename is passed)
    series_display = "120 Minutes"  # for this workflow; adjust if you generalize
    new_name = proposed_new_name(p, series_display, season_num, ep_num, airdate)
    print(f"{p.name}  ->  {new_name}   (S{season_num:02}E{ep_num:02})")

    if do_rename:
        new_path = p.with_name(new_name)
        p.rename(new_path)

def main():
    apikey = os.getenv("THETVDB_APIKEY")
    pin = os.getenv("THETVDB_PIN")  # optional
    if not apikey:
        print("Set THETVDB_APIKEY (and THETVDB_PIN if applicable) in your environment.", file=sys.stderr)
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Tag 120 Minutes recordings with SxxExx via TheTVDB (by air date).")
    parser.add_argument("paths", nargs="+", help="Files or folders to scan")
    parser.add_argument("--slug", default="120-minutes", help="TheTVDB series slug (default: 120-minutes)")
    parser.add_argument("--rename", action="store_true", help="Actually rename files on disk")
    args = parser.parse_args()

    token = tvdb_login(apikey, pin)

    targets = []
    for raw in args.paths:
        path = pathlib.Path(raw)
        if path.is_dir():
            for f in path.iterdir():
                if f.is_file():
                    targets.append(f)
        else:
            targets.append(path)

    for p in sorted(targets):
        resolve_for_file(p, token, args.slug, args.rename)

if __name__ == "__main__":
    main()
