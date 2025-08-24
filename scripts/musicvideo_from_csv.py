#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
musicvideo_from_csv.py

Reads a CSV of music videos and, for each row:
- Downloads the linked YouTube video via yt-dlp at best quality
- Ensures the final container is MP4 (remux; optional recode fallback)
- Writes a Kodi-compatible .nfo file alongside the video

Required CSV fields (case-insensitive; aliases supported):
  - year: year, release_year
  - title: title, track, track_title
  - artist: artist
  - album: album
  - label: label, record_label, studio
  - youtube: youtube, youtube_url, link, url
Optional fields:
  - director: director, directed_by
  - genre: genre, genres, style

Usage:
  python3 scripts/musicvideo_from_csv.py --csv data/tracks.csv --outdir output --recode-fallback
"""

import argparse
import csv
import sys
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from xml.sax.saxutils import escape as xml_escape
from datetime import datetime, timezone
import xml.etree.ElementTree as ET
import re
import glob
import os

CANON_ALIASES = {
    "year": {"year", "release_year"},
    "title": {"title", "track", "track_title"},
    "artist": {"artist", "artists"},
    "album": {"album"},
    "label": {"label", "record_label", "studio"},
    "youtube": {"youtube", "youtube_url", "link", "url"},
    "director": {"director", "directed_by"},
    "genre": {"genre", "genres", "style"},
    "youtube_channel": {"youtube_channel", "channel", "uploader", "youtube_uploader", "youtube_channel_name"},
    "tag": {"tag", "tags"},
}

_RESERVED = r'<>:"/\\|?*'
_reserved_re = re.compile(f"[{re.escape(_RESERVED)}]+")

def check_dependencies() -> None:
    """Ensure yt-dlp and ffmpeg are available in PATH."""
    missing = []
    if shutil.which("yt-dlp") is None:
        missing.append("yt-dlp")
    if shutil.which("ffmpeg") is None:
        missing.append("ffmpeg")
    if missing:
        msg = [
            "Missing required dependencies: " + ", ".join(missing),
            "Install suggestions:",
            "  macOS (Homebrew): brew install yt-dlp ffmpeg",
            "  Pipx: pipx install yt-dlp ; brew install ffmpeg",
            "  Pip (user): python3 -m pip install --user yt-dlp ; install ffmpeg per OS",
        ]
        print("\n".join(msg), file=sys.stderr)
        sys.exit(2)

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Download music videos from CSV and write Kodi .nfo files."
    )
    p.add_argument("--csv", required=True, help="Path to input CSV file")
    p.add_argument("--outdir", required=True, help="Base output directory")
    p.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing MP4 files (default: skip if exists)",
    )
    p.add_argument(
        "--recode-fallback",
        action="store_true",
        help="If remux to MP4 fails, recode to MP4 as fallback",
    )
    p.add_argument(
        "--no-search",
        action="store_true",
        help="Disable automatic video source searching on download failure",
    )
    p.add_argument(
        "--cookies",
        type=str,
        default=None,
        help="Path to cookies.txt file for yt-dlp (optional)",
    )
    return p.parse_args()

def normalize_header_map(fieldnames: List[str]) -> Dict[str, str]:
    """Map canonical names to actual CSV header names present in the file."""
    if not fieldnames:
        return {}
    lower_map = {fn.strip().lower(): fn for fn in fieldnames}
    result: Dict[str, str] = {}
    for canon, aliases in CANON_ALIASES.items():
        found = None
        for a in aliases:
            if a in lower_map:
                found = lower_map[a]
                break
        if found:
            result[canon] = found
    return result

import unicodedata
import musicbrainzngs

def normalize_name(name: str, max_len: int = 150) -> str:
    """Normalize artist/title: underscores for spaces, lowercase, remove diacritics, remove non-alphanumerics."""
    if not name:
        return "unknown"
    s = name.strip().lower()
    # Remove diacritics
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    # Replace spaces with underscores
    s = re.sub(r"\s+", "_", s)
    # Remove non-alphanumeric/underscore
    s = re.sub(r"[^a-z0-9_]", "", s)
    # Collapse multiple underscores
    s = re.sub(r"_+", "_", s)
    s = s.strip("_")
    if not s:
        s = "unknown"
    if len(s) > max_len:
        s = s[:max_len].rstrip("_")
    return s

def fetch_musicbrainz_artist_metadata(artist_name: str) -> dict:
    """Fetch artist metadata from MusicBrainz using python-musicbrainzngs, with logging."""
    musicbrainzngs.set_useragent("asot.tv-musicvideo-script", "1.0", "example@example.com")
    print(f"[MusicBrainz] Searching for artist: {artist_name}")
    try:
        result = musicbrainzngs.search_artists(artist=artist_name, country="US", limit=1)
        print(f"[MusicBrainz] Search response: {result}")
        if not result["artist-list"]:
            return {
                "name": artist_name,
                "biography": "",
            }
        artist = result["artist-list"][0]
        if artist.get("name") != artist_name:
            print(f"[MusicBrainz] Result does not match query: {artist} != {artist_name}")
            return {
                "name": artist_name,
                "biography": "",
            }
        mbid = artist.get("id")
        bio = ""
        try:
            print(f"[MusicBrainz] Fetching details for MBID: {mbid}")
            details = musicbrainzngs.get_artist_by_id(mbid, includes=["annotation"])
            print(f"[MusicBrainz] Details response: {details}")
            bio = details.get("artist", {}).get("annotation", "")
        except Exception as e:
            print(f"[MusicBrainz] Error fetching details: {e}")
        return {
            "name": artist.get("name", artist_name),
            "biography": bio,
        }
    except Exception as e:
        print(f"[MusicBrainz] Error searching artist: {e}")
        return {
            "name": artist_name,
            "biography": "",
        }

def write_artist_nfo(nfo_path: Path, metadata: dict) -> None:
    """Write Kodi-compatible artist.nfo XML file (pretty printed, omit null/empty elements)."""
    import xml.dom.minidom
    root = ET.Element("artist")
    for tag in ["name", "biography"]:
        value = metadata.get(tag, "")
        if value:
            el = ET.SubElement(root, tag)
            el.text = value
    xml_bytes = ET.tostring(root, encoding="utf-8")
    pretty_xml = xml.dom.minidom.parseString(xml_bytes).toprettyxml(indent="  ", encoding="utf-8")
    # minidom.toprettyxml already includes the XML declaration, so don't write it manually
    with nfo_path.open("wb") as f:
        f.write(pretty_xml)

def split_artists(artist_field: str) -> List[str]:
    """Split multiple artists on comma or semicolon."""
    if not artist_field:
        return ["Unknown Artist"]
    parts = re.split(r"[;,]", artist_field)
    artists = [p.strip() for p in parts if p.strip()]
    return artists or ["Unknown Artist"]

def split_list(value: str) -> List[str]:
    """Split a delimited list on comma or semicolon."""
    if not value:
        return []
    parts = re.split(r"[;,]", value)
    return [p.strip() for p in parts if p.strip()]

def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)

def yt_dlp_download(
    url: str,
    out_no_ext: Path,
    overwrite: bool,
    recode_fallback: bool,
    cookies_path: Optional[Path] = None,
) -> Optional[Path]:
    """Download using yt-dlp, aiming for MP4 container."""
    final_mp4 = out_no_ext.with_suffix(".mp4")
    out_template = str(out_no_ext.parent / (out_no_ext.name + ".%(ext)s"))

    if final_mp4.exists() and not overwrite:
        print(f"Skip (exists): {final_mp4}")
        return final_mp4

    base_args = [
        "yt-dlp",
        "-f",
        "bv*+ba/b",
        "-o",
        out_template,
        "--no-part",
        "--restrict-filenames",
        "--preset-alias",
        "mp4",
    ]
    if cookies_path:
        base_args += ["--cookies", str(cookies_path)]

    if overwrite:
        for f in glob.glob(str(out_no_ext) + ".*"):
            try:
                os.remove(f)
            except OSError:
                pass

    print(f"Downloading (remux): {url}")
    remux_proc = subprocess.run(base_args + [url])
    # Check for expected file, or any .mp4 file matching the stem
    if remux_proc.returncode == 0:
        if final_mp4.exists():
            return final_mp4
        # Try to find any matching .mp4 file
        candidates = list(out_no_ext.parent.glob(out_no_ext.name + "*.mp4"))
        if candidates:
            # Optionally rename to final_mp4 for consistency
            if candidates[0] != final_mp4:
                try:
                    candidates[0].rename(final_mp4)
                except Exception:
                    return candidates[0]
            return final_mp4

    if recode_fallback:
        print("Remux did not produce MP4; attempting recode fallback...")
        recode_args = [
            "yt-dlp",
            "-f",
            "bv*+ba/b",
            "-o",
            out_template,
            "--no-part",
            "--restrict-filenames",
            "--recode-video",
            "mp4",
            url,
        ]
        if cookies_path:
            recode_args += ["--cookies", str(cookies_path)]
        recode_proc = subprocess.run(recode_args)
        if recode_proc.returncode == 0:
            if final_mp4.exists():
                return final_mp4
            candidates = list(out_no_ext.parent.glob(out_no_ext.name + "*.mp4"))
            if candidates:
                if candidates[0] != final_mp4:
                    try:
                        candidates[0].rename(final_mp4)
                    except Exception:
                        return candidates[0]
                return final_mp4

    if final_mp4.exists():
        return final_mp4

    print("Download failed or no MP4 produced.", file=sys.stderr)
    return None

def yt_dlp_search_url(title: str, artist: str, cookies_path: Optional[Path] = None) -> Optional[Tuple[str, str]]:
    """Search YouTube for 'title artist official music video' and return (video URL, video ID)."""
    query = f"{title} {artist} official music video"
    args = [
        "yt-dlp",
        f"ytsearch1:{query}",
        "--get-id"
    ]
    if cookies_path:
        args += ["--cookies", str(cookies_path)]
    try:
        result = subprocess.run(args, capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.strip().splitlines()
            vid_id = lines[0]
            url = f"https://www.youtube.com/watch?v={vid_id}"
            return url, vid_id
    except Exception as e:
        print(f"yt_dlp_search_url error: {e}", file=sys.stderr)
    return None

def write_kodi_nfo(
    nfo_path: Path,
    title: str,
    album: str,
    label: str,
    year: str,
    artists: List[str],
    directors: List[str],
    genres: List[str],
    youtube_url: str,
    youtube_channel: Optional[str],
    tags: List[str],
    extra_sources: Optional[List[dict]] = None,
) -> None:
    """Write a Kodi-compatible .nfo file with musicvideo root element."""
    root = ET.Element("musicvideo")

    def add_text(tag: str, text: str) -> None:
        el = ET.SubElement(root, tag)
        el.text = text or ""

    add_text("title", title or "")
    add_text("album", album or "")
    add_text("studio", label or "")
    add_text("year", year or "")
    # premiered_val = f"{year}-01-01" if year else ""
    # add_text("premiered", premiered_val)

    for d in (directors or []):
        if d and d.strip():
            add_text("director", d.strip())
    for g in (genres or []):
        if g and g.strip():
            add_text("genre", g.strip())
    for a in (artists or []):
        if a and a.strip():
            add_text("artist", a.strip())

    if tags:
        add_text("tag", ", ".join([t for t in tags if t.strip()]))

    prior_sources: List[dict] = []
    prior_urls = set()
    if nfo_path.exists():
        try:
            old_tree = ET.parse(nfo_path)
            old_root = old_tree.getroot()
            sources_el = old_root.find("sources")
            if sources_el is not None:
                for child in list(sources_el):
                    url_text = (child.text or "").strip()
                    if url_text:
                        entry = dict(child.attrib)
                        entry["url"] = url_text
                        prior_sources.append(entry)
                        prior_urls.add(url_text)
        except Exception:
            prior_sources = []
            prior_urls = set()

    sources_el = ET.Element("sources")
    for entry in prior_sources:
        url_text = entry.get("url", "")
        attrs = {k: v for k, v in entry.items() if k != "url"}
        attrs["index"] = str(len(sources_el))
        el = ET.SubElement(sources_el, "url", attrs)
        el.text = url_text

    if extra_sources:
        for entry in extra_sources:
            url_text = entry.get("url", "")
            attrs = {k: v for k, v in entry.items() if k != "url"}
            attrs["index"] = str(len(sources_el))
            el = ET.SubElement(sources_el, "url", attrs)
            el.text = url_text

    if youtube_url and youtube_url not in prior_urls:
        now_ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        attrs = {"ts": now_ts}
        if youtube_channel:
            attrs["channel"] = youtube_channel
        attrs["index"] = str(len(sources_el))
        cur_el = ET.SubElement(sources_el, "url", attrs)
        cur_el.text = youtube_url

    top_level = ET.ElementTree()
    elements = [root, sources_el]
    with nfo_path.open("wb") as f:
        f.write(b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n')
        for el in elements:
            f.write(ET.tostring(el, encoding="utf-8"))

def extract_row_values(
    row: Dict[str, str],
    hmap: Dict[str, str],
) -> Tuple[str, str, List[str], str, str, str, List[str], List[str], Optional[str], List[str]]:
    """From a CSV row and normalized header map, extract all needed fields."""
    def get(canon: str) -> str:
        key = hmap.get(canon)
        return (row.get(key, "") if key else "").strip()

    year = get("year")
    title = get("title")
    artist_field = get("artist")
    album = get("album")
    label = get("label")
    youtube = get("youtube")
    director_field = get("director")
    genre_field = get("genre")
    youtube_channel = get("youtube_channel")
    tag_field = get("tag")

    artists = split_artists(artist_field)
    directors = split_list(director_field)
    genres = split_list(genre_field)
    tags = split_list(tag_field)
    return title, album, artists, label, year, youtube, directors, genres, youtube_channel, tags

def get_prior_urls(nfo_path: Path) -> set:
    """Get all prior source URLs from NFO file."""
    prior_urls = set()
    if nfo_path.exists():
        try:
            old_tree = ET.parse(nfo_path)
            old_root = old_tree.getroot()
            sources_el = old_root.find("sources")
            if sources_el is not None:
                for child in list(sources_el):
                    url_text = (child.text or "").strip()
                    if url_text:
                        prior_urls.add(url_text)
        except Exception:
            prior_urls = set()
    return prior_urls

def handle_failed_download_row(row, all_fieldnames, title, main_artist, exists, reason="invalid_url"):
    fail_row = {k: "" for k in all_fieldnames}
    fail_row["title"] = title
    fail_row["artist"] = main_artist
    fail_row["youtube"] = reason
    fail_row["exists"] = str(exists).lower()
    fail_row["search_attempt"] = "false"
    return fail_row

def process_row(
    idx: int,
    row: Dict[str, str],
    hmap: Dict[str, str],
    all_fieldnames: List[str],
    outdir: Path,
    overwrite: bool,
    recode_fallback: bool,
    no_search: bool,
    url_re: re.Pattern,
    failed_download_rows: List[Dict[str, str]],
    cookies_path: Optional[Path] = None,
) -> Tuple[int, int, int]:
    """Process a single CSV row. Returns (success, skipped, failed) counts."""
    success = skipped = failed = 0
    title, album, artists, label, year, youtube, directors, genres, youtube_channel, tags = extract_row_values(row, hmap)
    main_artist = artists[0] if artists else "Unknown Artist"
    normalized_artist = normalize_name(main_artist)
    normalized_title = normalize_name(title)
    target_dir = outdir / normalized_artist
    ensure_dir(target_dir)
    out_no_ext = target_dir / normalized_title
    final_mp4 = out_no_ext.with_suffix(".mp4")
    nfo_path = out_no_ext.with_suffix(".nfo")
    exists = final_mp4.exists()
    fail_row = row.copy()
    fail_row["exists"] = str(exists).lower()
    fail_row["search_attempt"] = "false"

    def yt_dlp_download_with_cookies(url, out_no_ext, overwrite, recode_fallback):
        return yt_dlp_download(
            url,
            out_no_ext,
            overwrite=overwrite,
            recode_fallback=recode_fallback,
            cookies_path=cookies_path,
        )

    def yt_dlp_search_url_with_cookies(title, artist):
        return yt_dlp_search_url(title, artist, cookies_path=cookies_path)

    if not youtube or not url_re.match(youtube):
        print(f"[Row {idx}] Invalid YouTube URL; skipping download/search.", file=sys.stderr)
        failed += 1
        failed_download_rows.append(handle_failed_download_row(row, all_fieldnames, title, main_artist, exists))
        return success, skipped, failed

    prior_urls = get_prior_urls(nfo_path)

    if exists:
        if not nfo_path.exists():
            # Video exists, but NFO does not; create NFO and skip download
            write_kodi_nfo(nfo_path, title, album, label, year, artists, directors, genres, youtube, youtube_channel, tags)
            skipped += 1
            print(f"[Row {idx}][{artists} - {title}] Video exists, NFO created: {final_mp4}")
            return success, skipped, failed
        if youtube in prior_urls:
            print(f"[Row {idx}][{artists} - {title}] Video exists and source matches; skipping download: {youtube}", file=sys.stderr)
            skipped += 1
            return success, skipped, failed
        else:
            mp4 = yt_dlp_download_with_cookies(
                youtube,
                out_no_ext,
                overwrite=overwrite,
                recode_fallback=recode_fallback,
            )
            if mp4 is None or not mp4.exists():
                print(f"[Row {idx}] Download failed for: {title} ({youtube})", file=sys.stderr)
                failed += 1
                failed_download_rows.append(fail_row)
                return success, skipped, failed
            write_kodi_nfo(nfo_path, title, album, label, year, artists, directors, genres, youtube, youtube_channel, tags)
            success += 1
            print(f"[Row {idx}][{artists} - {title}] Done: {final_mp4}")
            return success, skipped, failed

    mp4 = yt_dlp_download_with_cookies(
        youtube,
        out_no_ext,
        overwrite=overwrite,
        recode_fallback=recode_fallback,
    )
    if mp4 is None or not mp4.exists():
        print(f"[Row {idx}] Download failed for: {title} ({youtube})", file=sys.stderr)
        if not no_search:
            print(f"[Row {idx}][{artists} - {title}] Attempting search for alternative video...", file=sys.stderr)
            search_result = yt_dlp_search_url_with_cookies(title, main_artist)
            if search_result:
                search_url, search_vid_id = search_result
                if search_url != youtube:
                    print(f"[Row {idx}][{artists} - {title}] Attempting search-based download: {search_url}", file=sys.stderr)
                    fail_row["search_attempt"] = "true"
                    mp4 = yt_dlp_download_with_cookies(
                        search_url,
                        out_no_ext,
                        overwrite=overwrite,
                        recode_fallback=recode_fallback,
                    )
                    if mp4 is not None and mp4.exists():
                        try:
                            extra_sources = [
                                {
                                    "url": youtube,
                                    "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                                    "failed": "true",
                                },
                                {
                                    "url": f"https://www.youtube.com/watch?v={search_vid_id}",
                                    "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                                    "search": "true",
                                },
                            ]
                            write_kodi_nfo(
                                nfo_path,
                                title,
                                album,
                                label,
                                year,
                                artists,
                                directors,
                                genres,
                                youtube,
                                youtube_channel,
                                tags,
                                extra_sources=extra_sources,
                            )
                        except Exception as e:
                            print(f"[Row {idx}] Error writing NFO with search attributes: {e}", file=sys.stderr)
                        success += 1
                        print(f"Done (search): {final_mp4}")
                        return success, skipped, failed
                    else:
                        print(f"[Row {idx}] Search-based download also failed.", file=sys.stderr)
                        failed += 1
                        failed_download_rows.append(fail_row)
                        return success, skipped, failed
                else:
                    print(f"[Row {idx}][{artists} - {title}] Search returned same URL; not retrying.", file=sys.stderr)
                    failed += 1
                    failed_download_rows.append(fail_row)
                    return success, skipped, failed
            else:
                print(f"[Row {idx}] No search results found.", file=sys.stderr)
                failed += 1
                failed_download_rows.append(fail_row)
                return success, skipped, failed
        else:
            print(f"[Row {idx}] No-search flag set; not attempting search.", file=sys.stderr)
            failed += 1
            failed_download_rows.append(fail_row)
            return success, skipped, failed
    write_kodi_nfo(nfo_path, title, album, label, year, artists, directors, genres, youtube, youtube_channel, tags)
    success += 1
    print(f"Done: {final_mp4}")
    return success, skipped, failed

def process_csv(
    csv_path: Path,
    outdir: Path,
    overwrite: bool,
    recode_fallback: bool,
    no_search: bool = False,
    cookies_path: Optional[Path] = None,
) -> Tuple[int, int, int, List[Dict[str, str]], List[str]]:
    """Download logic for all CSV rows."""
    success = 0
    skipped = 0
    failed = 0
    failed_download_rows: List[Dict[str, str]] = []
    all_fieldnames: List[str] = []
    unique_artists: dict = {}

    url_re = re.compile(r"^https?://[^\s]+$")
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            print("CSV has no header row.", file=sys.stderr)
            return (0, 0, 1, [], [])
        all_fieldnames = reader.fieldnames

        hmap = normalize_header_map(reader.fieldnames)
        required = ["year", "title", "artist", "album", "label", "youtube"]
        missing = [r for r in required if r not in hmap]
        if missing:
            print(
                "CSV is missing required headers (accepted aliases in parentheses):",
                file=sys.stderr,
            )
            for r in missing:
                aliases = ", ".join(sorted(CANON_ALIASES[r]))
                print(f"  - {r}: {aliases}", file=sys.stderr)
            return (0, 0, 1, [], all_fieldnames)

        # Collect unique raw artist names
        for row in reader:
            title, album, artists, label, year, youtube, directors, genres, youtube_channel, tags = extract_row_values(row, hmap)
            main_artist = artists[0] if artists else "Unknown Artist"
            if main_artist not in unique_artists:
                unique_artists[main_artist] = normalize_name(main_artist)
        # Reset reader for row processing
        f.seek(0)
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader, start=2):
            try:
                s, sk, f_ = process_row(
                    idx,
                    row,
                    hmap,
                    all_fieldnames,
                    outdir,
                    overwrite,
                    recode_fallback,
                    no_search,
                    url_re,
                    failed_download_rows,
                    cookies_path,
                )
                success += s
                skipped += sk
                failed += f_
            except Exception as e:
                print(f"[Row {idx}] Error: {e}", file=sys.stderr)
                failed += 1

    # For each unique artist, create artist.nfo if missing
    for raw_artist, norm_artist in unique_artists.items():
        artist_dir = outdir / norm_artist
        nfo_path = artist_dir / "artist.nfo"
        if not nfo_path.exists():
            ensure_dir(artist_dir)
            metadata = fetch_musicbrainz_artist_metadata(raw_artist)
            write_artist_nfo(nfo_path, metadata)

    return success, skipped, failed, failed_download_rows, all_fieldnames

def main() -> None:
    args = parse_args()
    csv_path = Path(args.csv).expanduser().resolve()
    outdir = Path(args.outdir).expanduser().resolve()

    cookies_path = None
    if getattr(args, "cookies", None):
        cookies_path = Path(args.cookies).expanduser().resolve()
        if not cookies_path.exists():
            print(f"Cookies file not found: {cookies_path}", file=sys.stderr)
            sys.exit(2)

    if not csv_path.exists():
        print(f"CSV not found: {csv_path}", file=sys.stderr)
        sys.exit(2)

    ensure_dir(outdir)
    check_dependencies()

    print(f"Input CSV: {csv_path}")
    print(f"Output dir: {outdir}")
    print(f"Overwrite: {'yes' if args.overwrite else 'no'}")
    print(f"Recode fallback: {'yes' if args.recode_fallback else 'no'}")
    print(f"No search: {'yes' if args.no_search else 'no'}")
    if cookies_path:
        print(f"Cookies: {cookies_path}")

    ok, skipped, bad, failed_rows, fieldnames = process_csv(
        csv_path,
        outdir,
        args.overwrite,
        args.recode_fallback,
        no_search=getattr(args, "no_search", False),
        cookies_path=cookies_path,
    )

    print("\nSummary")
    print(f"  Success: {ok}")
    print(f"  Skipped: {skipped}")
    print(f"  Failed:  {bad}")

    if failed_rows:
        print("\nFailed download rows (CSV):")
        extra_fields = ["exists", "search_attempt"]
        out_fields = fieldnames + [f for f in extra_fields if f not in fieldnames]
        writer = csv.DictWriter(sys.stdout, fieldnames=out_fields)
        writer.writeheader()
        writer.writerows(failed_rows)

    sys.exit(0 if bad == 0 else 1)

if __name__ == "__main__":
    main()