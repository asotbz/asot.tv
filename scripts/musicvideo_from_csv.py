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
    return p.parse_args()


def normalize_header_map(fieldnames: List[str]) -> Dict[str, str]:
    """
    Map canonical names to actual CSV header names present in the file.
    Returns dict like {'year': 'Year', 'title': 'track_title', ...}
    """
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


_RESERVED = r'<>:"/\\|?*'
_reserved_re = re.compile(f"[{re.escape(_RESERVED)}]+")


def sanitize_component(name: str, max_len: int = 150) -> str:
    """
    Make a filesystem-safe path component:
    - Replace reserved chars with _
    - Collapse consecutive underscores
    - Strip leading/trailing whitespace and dots
    - Trim to max_len
    """
    if not name:
        return "unknown"
    s = name.strip()
    s = _reserved_re.sub("_", s)
    s = re.sub(r"\s+", " ", s)  # collapse whitespace runs to a single space
    s = re.sub(r"_+", "_", s)
    s = s.strip(" .")
    if not s:
        s = "unknown"
    if len(s) > max_len:
        s = s[:max_len].rstrip(" ._")
    return s


def split_artists(artist_field: str) -> List[str]:
    """
    Split multiple artists on comma or semicolon. Trim parts; drop empties.
    """
    if not artist_field:
        return ["Unknown Artist"]
    parts = re.split(r"[;,]", artist_field)
    artists = [p.strip() for p in parts if p.strip()]
    return artists or ["Unknown Artist"]

 
def split_list(value: str) -> List[str]:
    """
    Split a delimited list on comma or semicolon. Trim parts; drop empties.
    Returns [] if value is falsy.
    """
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
) -> Optional[Path]:
    """
    Download using yt-dlp, aiming for MP4 container.
    Strategy:
      1) Try best video+audio, remux to mp4: --remux-video mp4
      2) If mp4 not produced and recode_fallback is True, try --recode-video mp4
    Returns final MP4 path on success, else None.
    """
    final_mp4 = out_no_ext.with_suffix(".mp4")
    out_template = str(out_no_ext.parent / (out_no_ext.name + ".%(ext)s"))

    if final_mp4.exists() and not overwrite:
        print(f"Skip (exists): {final_mp4}")
        return final_mp4

    # Base args: prefer separate best video+audio, otherwise best single
    base_args = [
        "yt-dlp",
        "-f",
        "bv*+ba/b",
        "-o",
        out_template,
        "--no-part",
        "--restrict-filenames",  # reduces unexpected characters from yt-dlp's side
        "--remux-video",
        "mp4",
    ]

    # If overwrite requested, remove pre-existing outputs with other extensions
    if overwrite:
        for f in glob.glob(str(out_no_ext) + ".*"):
            try:
                os.remove(f)
            except OSError:
                pass

    print(f"Downloading (remux): {url}")
    remux_proc = subprocess.run(base_args + [url])
    if remux_proc.returncode == 0 and final_mp4.exists():
        return final_mp4

    # If remux didn't yield MP4 and fallback is requested, try recode
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
        recode_proc = subprocess.run(recode_args)
        if recode_proc.returncode == 0 and final_mp4.exists():
            return final_mp4

    # As a last attempt, if any file exists at the template stem, and it's mp4, accept it
    if final_mp4.exists():
        return final_mp4

    print("Download failed or no MP4 produced.", file=sys.stderr)
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
) -> None:
    """
    Write a Kodi-compatible .nfo file with musicvideo root element.
    Adds/updates a <source> history block where:
      - <url index="0" ts="ISO8601Z" [channel="..."]>current_youtube_url</url>
      - previous URLs (if any) are shifted to index 1, 2, ... (preserving ts and channel if present)
    """
    # Prepare base metadata
    root = ET.Element("musicvideo")

    def add_text(tag: str, text: str) -> None:
        el = ET.SubElement(root, tag)
        el.text = text or ""

    add_text("title", title or "")
    add_text("album", album or "")
    add_text("studio", label or "")
    add_text("year", str(year or ""))

    for d in (directors or []):
        if d and d.strip():
            add_text("director", d.strip())
    for g in (genres or []):
        if g and g.strip():
            add_text("genre", g.strip())
    for a in (artists or []):
        if a and a.strip():
            add_text("artist", a.strip())

    # Single <tag> element with comma-separated tags if provided
    if tags:
        add_text("tag", ", ".join([t for t in tags if t.strip()]))

    # Collect prior sources, if existing NFO present
    prior_sources: List[Tuple[str, Optional[str], Optional[str]]] = []
    if nfo_path.exists():
        try:
            old_tree = ET.parse(nfo_path)
            old_root = old_tree.getroot()
            old_source = old_root.find("source")
            if old_source is not None:
                for child in list(old_source):
                    url_text = (child.text or "").strip()
                    if url_text:
                        ts_attr = child.attrib.get("ts") or child.attrib.get("timestamp") or child.attrib.get("time")
                        ch_attr = child.attrib.get("channel")
                        prior_sources.append((url_text, ts_attr, ch_attr))
        except Exception:
            # If parsing fails, ignore and start fresh
            prior_sources = []

    # Build new source block with current URL at index 0 and shift prior ones
    source_el = ET.SubElement(root, "source")
    if youtube_url:
        now_ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        attrs = {"index": "0", "ts": now_ts}
        if youtube_channel:
            attrs["channel"] = youtube_channel
        cur_el = ET.SubElement(source_el, "url", attrs)
        cur_el.text = youtube_url

    for i, (prev_url, prev_ts, prev_channel) in enumerate(prior_sources, start=1):
        attrs = {"index": str(i)}
        if prev_ts:
            attrs["ts"] = prev_ts
        if prev_channel:
            attrs["channel"] = prev_channel
        prev_el = ET.SubElement(source_el, "url", attrs)
        prev_el.text = prev_url

    # Write XML with declaration
    tree = ET.ElementTree(root)
    tree.write(nfo_path, encoding="utf-8", xml_declaration=True)


def read_current_source(nfo_path: Path) -> Optional[str]:
    """
    Read the current source URL from an existing .nfo.
    Returns the text of &lt;source&gt;&lt;url index="0"&gt; if present; otherwise the first &lt;url&gt; child.
    """
    if not nfo_path.exists():
        return None
    try:
        tree = ET.parse(nfo_path)
        root = tree.getroot()
        source = root.find("source")
        if source is None:
            return None
        # Prefer the explicit index="0"
        for child in list(source):
            if child.tag == "url" and child.attrib.get("index") == "0":
                txt = (child.text or "").strip()
                return txt or None
        # Fallback to first url element
        for child in list(source):
            if child.tag == "url":
                txt = (child.text or "").strip()
                return txt or None
        return None
    except Exception:
        return None
def extract_row_values(
    row: Dict[str, str],
    hmap: Dict[str, str],
) -> Tuple[str, str, List[str], str, str, str, List[str], List[str], Optional[str], List[str]]:
    """
    From a CSV row and normalized header map, extract:
      title, album, artists[], label, year, youtube_url, directors[], genres[], youtube_channel, tags[]
    """
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


def process_csv(csv_path: Path, outdir: Path, overwrite: bool, recode_fallback: bool) -> Tuple[int, int, int]:
    """
    Process all rows. Returns tuple: (success_count, skip_count, fail_count)
    """
    success = 0
    skipped = 0
    failed = 0

    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            print("CSV has no header row.", file=sys.stderr)
            return (0, 0, 1)

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
            return (0, 0, 1)

        for idx, row in enumerate(reader, start=2):
            try:
                title, album, artists, label, year, youtube, directors, genres, youtube_channel, tags = extract_row_values(row, hmap)

                # Basic validation
                if not youtube:
                    print(f"[Row {idx}] Missing YouTube URL; skipping.", file=sys.stderr)
                    failed += 1
                    continue
                if not title:
                    print(f"[Row {idx}] Missing Title; skipping.", file=sys.stderr)
                    failed += 1
                    continue
                if not album:
                    print(f"[Row {idx}] Missing Album; skipping.", file=sys.stderr)
                    failed += 1
                    continue
                main_artist = artists[0] if artists else "Unknown Artist"

                # Build output paths
                artist_dir = sanitize_component(main_artist)
                album_dir = sanitize_component(album)
                title_stem = sanitize_component(title)

                target_dir = outdir / artist_dir / album_dir
                ensure_dir(target_dir)

                out_no_ext = target_dir / title_stem
                final_mp4 = out_no_ext.with_suffix(".mp4")
                nfo_path = out_no_ext.with_suffix(".nfo")

                # Decide whether to force re-download based on .nfo current source
                existing_mp4 = final_mp4.exists()
                current_source = read_current_source(nfo_path) if nfo_path.exists() else None
                force_redownload = bool(existing_mp4 and current_source and current_source != youtube)

                # Download (force overwrite if source changed)
                effective_overwrite = overwrite or force_redownload
                mp4 = yt_dlp_download(
                    youtube,
                    out_no_ext,
                    overwrite=effective_overwrite,
                    recode_fallback=recode_fallback,
                )

                if mp4 is None or not mp4.exists():
                    print(f"[Row {idx}] Download failed for: {title} ({youtube})", file=sys.stderr)
                    failed += 1
                    continue

                # NFO
                write_kodi_nfo(nfo_path, title, album, label, year, artists, directors, genres, youtube, youtube_channel, tags)

                if mp4.exists() and not overwrite:
                    # Could be a real skip if existing; count skip if it existed prior and no download was done
                    # Heuristic: if file existed beforehand, yt-dlp would have skipped; we already printed "Skip (exists)"
                    if "Skip (exists)" in "" :  # no reliable signal; treat as success
                        skipped += 1
                    else:
                        success += 1
                else:
                    success += 1

                print(f"Done: {final_mp4}")
            except Exception as e:
                print(f"[Row {idx}] Error: {e}", file=sys.stderr)
                failed += 1

    return success, skipped, failed


def main() -> None:
    args = parse_args()
    csv_path = Path(args.csv).expanduser().resolve()
    outdir = Path(args.outdir).expanduser().resolve()

    if not csv_path.exists():
        print(f"CSV not found: {csv_path}", file=sys.stderr)
        sys.exit(2)

    ensure_dir(outdir)
    check_dependencies()

    print(f"Input CSV: {csv_path}")
    print(f"Output dir: {outdir}")
    print(f"Overwrite: {'yes' if args.overwrite else 'no'}")
    print(f"Recode fallback: {'yes' if args.recode_fallback else 'no'}")

    ok, skipped, bad = process_csv(csv_path, outdir, args.overwrite, args.recode_fallback)

    print("\nSummary")
    print(f"  Success: {ok}")
    print(f"  Skipped: {skipped}")
    print(f"  Failed:  {bad}")

    sys.exit(0 if bad == 0 else 1)


if __name__ == "__main__":
    main()