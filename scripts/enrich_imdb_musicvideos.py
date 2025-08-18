#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
enrich_imdb_musicvideos.py

Known issues:
- Genre selection is loose and falls back to first entry in the normalized list too frequently.
- YouTube searches are too frequent and will hit the default 10k quota almost immediately.

Parse an IMDb list export CSV (Music Video items) and produce an enriched CSV with:
- year: release year (YYYY)
- artist: artist credit (parsed from Title "Artist: Track")
- title: track title (parsed from Title "Artist: Track")
- album: album/single release title (from MusicBrainz if possible)
- label: record label normalized to direct/canonical form
- genre: primary broad genre (Hip Hop/R&B, Rock, Pop, Metal, Country, Electronic, Alternative, Dance)
- director: from IMDb Directors column, first credited (or empty)
- tag: "80s" / "90s" / "00s" if year within those decades; else empty
- youtube_url: a YouTube URL for the video (preferring artist/label, then official e.g., VEVO, else best relevance)
- youtube_channel: channel/uploader name for youtube_url

APIs:
- MusicBrainz WS/2 (polite: 1 req/sec). Configure UA via --mb-user-agent (default: "asot.tv-mv-enricher/0.1")
- YouTube Data API v3; provide key via --youtube-api-key

Caching:
- JSON cache to avoid repeated network calls. Keyed by "mb|artist|title|year" and "yt|artist|title".

Usage examples:
  python3 scripts/enrich_imdb_musicvideos.py \
    --in 93efcd06-e106-4f1c-9e19-4901bc66e680.csv \
    --out 90s-enriched.csv \
    --youtube-api-key YOUR_KEY \
    --verbose

  python3 scripts/enrich_imdb_musicvideos.py --help
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests


MB_BASE = "https://musicbrainz.org/ws/2"
MB_DEFAULT_UA = "asot.tv-mv-enricher/0.1"
YT_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"


# -------------------------------
# Pretty Logger (ANSI colors)
# -------------------------------

class _Ansi:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    GRAY = "\033[90m"


_LEVELS = {"DEBUG": 10, "INFO": 20, "WARN": 30, "ERROR": 40, "SUCCESS": 25}


class Logger:
    def __init__(self, use_color: bool = True, level: str = "DEBUG"):
        self.use_color = use_color
        self.level = _LEVELS.get(level.upper(), 10)

    def _ts(self) -> str:
        return time.strftime("%H:%M:%S")

    def _fmt(self, emoji: str, color: str, label: str, msg: str) -> str:
        base = f"{emoji} [{self._ts()}] {label}: {msg}"
        if not self.use_color:
            return base
        return f"{color}{base}{_Ansi.RESET}"

    def _emit(self, lvl: str, msg: str, stream):
        if _LEVELS[lvl] < self.level:
            return
        if lvl == "INFO":
            line = self._fmt("ℹ️", _Ansi.BLUE, "INFO", msg)
            print(line, file=stream, flush=True)
        elif lvl == "WARN":
            line = self._fmt("⚠️", _Ansi.YELLOW, "WARN", msg)
            print(line, file=stream, flush=True)
        elif lvl == "ERROR":
            line = self._fmt("❌", _Ansi.RED, "ERROR", msg)
            print(line, file=stream, flush=True)
        elif lvl == "DEBUG":
            color = _Ansi.MAGENTA + _Ansi.DIM if self.use_color else ""
            end_color = _Ansi.RESET if self.use_color else ""
            base = f"🐞 [{self._ts()}] DEBUG: {msg}"
            print(f"{color}{base}{end_color}", file=stream, flush=True)
        elif lvl == "SUCCESS":
            line = self._fmt("✅", _Ansi.GREEN, "OK", msg)
            print(line, file=stream, flush=True)

    def info(self, msg: str):
        self._emit("INFO", msg, sys.stdout)

    def warn(self, msg: str):
        self._emit("WARN", msg, sys.stderr)

    def error(self, msg: str):
        self._emit("ERROR", msg, sys.stderr)

    def debug(self, msg: str):
        self._emit("DEBUG", msg, sys.stdout)

    def success(self, msg: str):
        self._emit("SUCCESS", msg, sys.stdout)


# -------------------------------
# Utilities
# -------------------------------

def parse_year(value: str) -> str:
    """
    Extract a 4-digit year from IMDb 'Year' or 'Release Date' fields.
    """
    if not value:
        return ""
    m = re.search(r"\b(19|20)\d{2}\b", value)
    return m.group(0) if m else ""


def split_title_to_artist_track(title: str) -> Tuple[str, str]:
    """
    IMDb 'Title' usually looks like "Artist: Track".
    Split on the first colon. Trim results.
    If no colon, return ("", title).
    """
    if not title:
        return "", ""
    parts = title.split(":", 1)
    if len(parts) == 2:
        artist = parts[0].strip()
        track = parts[1].strip()
        return artist, track
    return "", title.strip()


def first_or_empty(items: List[str]) -> str:
    for it in items:
        s = (it or "").strip()
        if s:
            return s
    return ""


def derive_decade_tag(year_str: str) -> str:
    try:
        y = int(year_str)
    except Exception:
        return ""
    if 1980 <= y <= 1989:
        return "80s"
    if 1990 <= y <= 1999:
        return "90s"
    if 2000 <= y <= 2009:
        return "00s"
    return ""


def ensure_dir(p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)


# -------------------------------
# Caching
# -------------------------------

class JsonCache:
    def __init__(self, path: Path, logger: Optional[Logger] = None):
        self.path = path
        self.logger = logger
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            try:
                with self.path.open("r", encoding="utf-8") as f:
                    self.data = json.load(f)
                if self.logger:
                    self.logger.debug(f"Cache loaded: {self.path}")
            except Exception:
                self.data = {}
                if self.logger:
                    self.logger.warn(f"Cache load failed; starting empty: {self.path}")
        else:
            self.data = {}

    def get(self, key: str) -> Optional[Any]:
        val = self.data.get(key)
        if self.logger:
            if val is None:
                self.logger.debug(f"Cache MISS: {key}")
            else:
                self.logger.debug(f"Cache HIT: {key}")
        return val

    def set(self, key: str, value: Any) -> None:
        self.data[key] = value
        try:
            tmp = self.path.with_suffix(self.path.suffix + ".tmp")
            with tmp.open("w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            tmp.replace(self.path)
            if self.logger:
                self.logger.debug(f"Cache WRITE: {key}")
        except Exception:
            if self.logger:
                self.logger.warn("Cache write failed (continuing).")


# -------------------------------
# Normalization
# -------------------------------

_LABEL_NORMALIZE = {
    # Common canonicalizations
    "def jam recordings": "Def Jam",
    "def jam": "Def Jam",
    "warner bros. records": "Warner Bros.",
    "warner bros": "Warner Bros.",
    "warner records": "Warner Bros.",
    "a&m records": "A&M",
    "a&m records": "A&M",
    "a&m": "A&M",
    "virgin records": "Virgin",
    "virgin music": "Virgin",
    "virgin": "Virgin",
    "columbia records": "Columbia",
    "sony music": "Sony",
    "sony music entertainment": "Sony",
    "universal music": "Universal",
    "umg": "Universal",
    "reprise records": "Reprise",
    "atlantic recording corporation": "Atlantic",
    "atlantic records": "Atlantic",
    "island records": "Island",
    "epic records": "Epic",
    "capitol records": "Capitol",
    "capitol": "Capitol",
    "geffen records": "Geffen",
    "geffen": "Geffen",
    "mca records": "MCA",
    "mca": "MCA",
    "motown records": "Motown",
    "motown": "Motown",
    "interscope records": "Interscope",
    "interscope": "Interscope",
    "laface records": "LaFace",
    "laface": "LaFace",
    "ruffhouse records": "Ruffhouse",
    "ruffhouse": "Ruffhouse",
    "chrysalis records": "Chrysalis",
    "chrysalis": "Chrysalis",
    "jive records": "Jive",
    "jive": "Jive",
    "epitaph records": "Epitaph",
    "epitaph": "Epitaph",
    "4ad": "4AD",
}

def normalize_label(label: str) -> str:
    """
    Normalize label to its direct/canonical form:
    - Lowercase, strip corporate suffixes (records, recordings, entertainment, inc., llc, ltd)
    - Map via _LABEL_NORMALIZE
    - Title-case remnants with known uppercase exceptions
    """
    s = (label or "").strip()
    if not s:
        return ""

    low = s.lower()
    # Remove common suffixes
    low = re.sub(r"\b(records?|recordings?|entertainment|music group|group|llc|l\.l\.c\.|inc\.?|ltd\.?|limited|company|corp\.?|corporation)\b", "", low)
    low = re.sub(r"\s+", " ", low).strip(" ,.-")
    if not low:
        return ""

    if low in _LABEL_NORMALIZE:
        return _LABEL_NORMALIZE[low]

    # Title case while keeping known all-caps
    special = {"A&M", "UMG", "MCA", "RCA", "EMI", "DGC", "SBK", "4AD"}
    tc = " ".join(w.capitalize() for w in low.split())
    for sp in special:
        tc = re.sub(rf"\b{re.escape(sp.capitalize())}\b", sp, tc)
    return tc


_BROAD_GENRES = [
    "Hip Hop/R&B",
    "Rock",
    "Pop",
    "Metal",
    "Country",
    "Electronic",
    "Alternative",
    "Dance",
]

def map_to_broad_genre(candidates: List[str]) -> str:
    """
    Map a list of candidate genre/tag strings to one broad genre.
    Priority by first match in order below.
    """
    keys = [c.lower() for c in candidates if c]
    # Hip Hop / R&B
    if any(k in keys for k in ["hip hop", "hip-hop", "rap", "r&b", "new jack swing"]):
        return "Hip Hop/R&B"
    # Metal
    if any("metal" in k for k in keys):
        return "Metal"
    # Rock / Alternative / Punk
    if any(k in keys for k in ["rock", "alternative", "alt rock", "alt-rock", "punk", "punk rock", "grunge", "indie rock", "hard rock"]):
        return "Rock"
    # Electronic / Dance
    if any(k in keys for k in ["electronic", "dance", "house", "techno", "edm", "trip-hop", "triphop"]):
        if "dance" in keys:
            return "Dance"
        return "Electronic"
    # Pop
    if any("pop" in k for k in keys):
        return "Pop"
    # Country
    if any("country" in k for k in keys):
        return "Country"
    # Fallback Alternative if appears
    if any("alternative" in k for k in keys):
        return "Alternative"
    # Last resort: first normalized
    return first_or_empty(_BROAD_GENRES)


# -------------------------------
# IMDb parsing
# -------------------------------

IMDB_COLS = {
    "Title": "Title",
    "Year": "Year",
    "Genres": "Genres",
    "Directors": "Directors",
}

def parse_imdb_row(row: Dict[str, str]) -> Dict[str, str]:
    title = (row.get("Title") or "").strip()
    artist, track = split_title_to_artist_track(title)
    year = parse_year(row.get("Year") or row.get("Release Date") or "")
    directors = [d.strip() for d in (row.get("Directors") or "").split(",") if d.strip()]
    primary_director = directors[0] if directors else ""
    imdb_genres = [g.strip() for g in (row.get("Genres") or "").split(",") if g.strip()]
    return {
        "artist": artist,
        "title": track,
        "year": year,
        "director": primary_director,
        "imdb_genres": imdb_genres,
    }


# -------------------------------
# MusicBrainz
# -------------------------------

@dataclass
class MBResult:
    album: str = ""
    label: str = ""
    tags: List[str] = None

class MBClient:
    def __init__(self, user_agent: str, rate_limit_sec: float = 1.0, logger: Optional[Logger] = None, session: Optional[requests.Session] = None):
        self.user_agent = user_agent or MB_DEFAULT_UA
        self.rate_limit_sec = max(rate_limit_sec, 0.5)
        self.session = session or requests.Session()
        self._last = 0.0
        self.logger = logger

    def _wait(self):
        now = time.time()
        delta = now - self._last
        if delta < self.rate_limit_sec:
            time.sleep(self.rate_limit_sec - delta)
        self._last = time.time()

    def _get(self, path: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        self._wait()
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/json",
        }
        url = f"{MB_BASE}/{path}"
        if self.logger:
            self.logger.info(f"MB GET {url} params={params}")
        try:
            resp = self.session.get(url, params=params, headers=headers, timeout=15)
            if resp.status_code == 503:
                if self.logger:
                    self.logger.warn("MB 503 Service Unavailable; retrying once after 2s...")
                time.sleep(2)
                resp = self.session.get(url, params=params, headers=headers, timeout=15)
            if self.logger:
                self.logger.info(f"MB RESP status={resp.status_code} len={len(resp.content)}")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            if self.logger:
                self.logger.error(f"MB request failed: {e}")
            return None

    def search_recording(self, artist: str, title: str, year: str) -> Optional[MBResult]:
        """
        Search for a recording and pick a good release to infer album, label, and tags.
        """
        if not title:
            if self.logger:
                self.logger.warn("MB search skipped: empty title")
            return None

        query_parts = [f'recording:"{title}"']
        if artist:
            query_parts.append(f'artist:""{artist}""' if '"' in artist else f'artist:"{artist}"')
        query = " AND ".join(query_parts)

        params = {
            "fmt": "json",
            "query": query,
            "limit": "10",
            "inc": "artists+releases+release-groups+tags",
        }
        data = self._get("recording", params)
        if not data or "recordings" not in data:
            if self.logger:
                self.logger.warn("MB search returned no data")
            return None

        recs = data.get("recordings", [])
        if self.logger:
            self.logger.info(f"MB candidates: {len(recs)} for '{artist} - {title}' y={year or '?'}")

        # Scoring: prefer MB "score", then year proximity on release/release-group
        candidates: List[Tuple[int, Dict[str, Any]]] = []
        for rec in recs:
            score = int(rec.get("score", 0))
            proximity_bonus = 0
            y_target = None
            try:
                y_target = int(year)
            except Exception:
                y_target = None

            rel_years = []
            for rel in rec.get("releases", []) or []:
                d = rel.get("date") or rel.get("release-date") or ""
                y = parse_year(d)
                if y:
                    try:
                        rel_years.append(int(y))
                    except Exception:
                        pass
            if y_target is not None and rel_years:
                best_diff = min(abs(ry - y_target) for ry in rel_years)
                proximity_bonus = max(0, 10 - best_diff)

            candidates.append((score + proximity_bonus, rec))

        if not candidates:
            if self.logger:
                self.logger.warn("MB: no scored candidates")
            return None

        candidates.sort(key=lambda t: t[0], reverse=True)
        if self.logger:
            preview = ", ".join(str(s) for s, _ in candidates[:3])
            self.logger.debug(f"MB top scores: {preview}")
        best = candidates[0][1]
        
        # Choose a release: prefer release-group primary-type Album or Single and year closest to target
        chosen_release = None
        y_target = None
        try:
            y_target = int(year)
        except Exception:
            y_target = None

        def rel_score(rel: Dict[str, Any]) -> int:
            rg = rel.get("release-group") or {}
            primary = (rg.get("primary-type") or rg.get("primaryType") or "").lower()
            type_bonus = 5 if primary in ("album", "single", "ep") else 0
            d = rel.get("date") or rel.get("release-date") or ""
            ry = parse_year(d)
            prox_bonus = 0
            if y_target and ry:
                try:
                    prox_bonus = max(0, 10 - abs(int(ry) - y_target))
                except Exception:
                    prox_bonus = 0
            status_bonus = 2 if (rel.get("status") or "").lower() == "official" else 0
            return type_bonus + prox_bonus + status_bonus

        rels = best.get("releases", []) or []
        if rels:
            chosen_release = sorted(rels, key=rel_score, reverse=True)[0]

        album = ""
        label = ""
        tags: List[str] = []

        if chosen_release:
            album = chosen_release.get("title") or ""
            for li in (chosen_release.get("label-info") or chosen_release.get("label-info-list") or []):
                lab = (li.get("label") or {}).get("name") or li.get("label-name") or ""
                if lab:
                    label = lab
                    break
            rg = chosen_release.get("release-group") or {}
            for t in (rg.get("tags") or []):
                name = t.get("name") or ""
                if name:
                    tags.append(name)

        for t in (best.get("tags") or []):
            name = t.get("name") or ""
            if name and name not in tags:
                tags.append(name)

        if self.logger:
            self.logger.success(f"MB chosen album='{album or '-'}' label='{label or '-'}' tags={len(tags)}")
        return MBResult(album=album, label=label, tags=tags or [])


# -------------------------------
# YouTube
# -------------------------------

def _norm_name_for_match(s: str) -> str:
    s = (s or "").lower()
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _channel_preference_score(channel_title: str, video_title: str, artist: str, label: str) -> int:
    score = 0
    c = _norm_name_for_match(channel_title)
    a = _norm_name_for_match(artist)
    l = _norm_name_for_match(label)
    vt = _norm_name_for_match(video_title)

    if a and c == a:
        score += 50
    if l and c == l:
        score += 40

    if a and (a in c) and ("vevo" in c or "official" in c):
        score += 30
    if "official video" in vt or "music video" in vt:
        score += 10

    if a and a in c:
        score += 5
    if l and l in c:
        score += 5

    return score

def youtube_search_best(artist: str, title: str, label: str, api_key: Optional[str], logger: Optional[Logger] = None) -> Tuple[str, str]:
    """
    Return (url, channelTitle) or ("","") if no key or no result.
    """
    if not api_key:
        if logger:
            logger.info("YouTube search skipped (no API key provided).")
        return "", ""
    if not title:
        if logger:
            logger.warn("YouTube search skipped (empty title).")
        return "", ""

    q_variants = [
        f"{artist} {title} official video",
        f"{artist} {title} music video",
        f"{artist} {title}",
        f"{title} {artist}",
    ]

    best: Tuple[int, str, str, str] = (0, "", "", "")  # score, videoId, channelTitle, videoTitle
    session = requests.Session()

    for q in q_variants:
        if logger:
            logger.info(f"YT search q='{q}'")
        params = {
            "key": api_key,
            "part": "snippet",
            "type": "video",
            "videoCategoryId": "10",
            "maxResults": "10",
            "q": q,
        }
        try:
            resp = session.get(YT_SEARCH_URL, params=params, timeout=15)
            if logger:
                logger.info(f"YT RESP status={resp.status_code}")
            if resp.status_code != 200:
                continue
            data = resp.json()
        except Exception as e:
            if logger:
                logger.warn(f"YT request failed: {e}")
            continue

        items = data.get("items", [])
        if logger:
            logger.info(f"YT items returned: {len(items)}")

        for item in items:
            vid = (((item.get("id") or {}).get("videoId")) or "")
            snippet = item.get("snippet") or {}
            ch = snippet.get("channelTitle") or ""
            vtitle = snippet.get("title") or ""
            if not vid:
                continue
            score = _channel_preference_score(ch, vtitle, artist, label) + 1
            if score > best[0]:
                best = (score, vid, ch, vtitle)
                if logger:
                    logger.info(f"YT candidate new-best: score={score} channel='{ch}' title='{vtitle}'")

        if logger:
            logger.info(f"YT best after q='{q}': score={best[0]} channel='{best[2]}' title='{best[3]}'")
        if best[0] >= 60:
            break

    if best[1]:
        url = f"https://www.youtube.com/watch?v={best[1]}"
        if logger:
            logger.success(f"YT chosen: channel='{best[2]}' score={best[0]} title='{best[3]}' url={url}")
        return url, best[2]
    if logger:
        logger.warn("YT no suitable result.")
    return "", ""


# -------------------------------
# Pipeline
# -------------------------------

@dataclass
class EnrichedRow:
    year: str
    artist: str
    title: str
    album: str
    label: str
    genre: str
    director: str
    tag: str
    youtube_url: str
    youtube_channel: str


def enrich_row(row: Dict[str, str], mb: Optional[MBClient], yt_key: Optional[str], cache: JsonCache, logger: Logger) -> EnrichedRow:
    parsed = parse_imdb_row(row)
    artist = parsed["artist"]
    title = parsed["title"]
    year = parsed["year"]
    director = parsed["director"]
    imdb_genres = parsed["imdb_genres"]

    logger.info(f"Process: {artist or 'Unknown'} — {title or 'Unknown'} [{year or '?'}]")
    logger.debug(f"Parsed IMDb -> artist='{artist}', title='{title}', year='{year}', director='{director}', imdb_genres={imdb_genres}")
    
    # Cache keys
    mb_key = f"mb|{artist}|{title}|{year}"
    yt_key_cache = f"yt|{artist}|{title}"

    # MusicBrainz
    album = ""
    label = ""
    mb_tags: List[str] = []
    if mb:
        cached = cache.get(mb_key)
        if cached is None:
            logger.debug("MB lookup (MISS) -> querying MusicBrainz")
            res = mb.search_recording(artist, title, year)
            cached = {
                "album": (res.album if res else ""),
                "label": (res.label if res else ""),
                "tags": (res.tags if res else []),
            }
            cache.set(mb_key, cached)
        else:
            logger.debug("MB lookup (HIT) -> using cached result")
        album = cached.get("album", "") or ""
        label = cached.get("label", "") or ""
        mb_tags = cached.get("tags", []) or []

    # Normalize label
    norm_label = normalize_label(label) if label else ""
    if label:
        logger.info(f"Label: raw='{label}' normalized='{norm_label or '-'}'")

    # Genre mapping, prefer MB tags
    broad_genre = map_to_broad_genre(mb_tags if mb_tags else imdb_genres)
    logger.debug(f"Genre candidates -> mb_tags={mb_tags} imdb_genres={imdb_genres}")
    logger.info(f"Genre: {broad_genre or '-'}")
    
    # YouTube
    cached_yt = cache.get(yt_key_cache)
    if cached_yt is None:
        logger.debug("YT lookup (MISS) -> querying YouTube")
        yt_url, yt_channel = youtube_search_best(artist, title, norm_label or label, yt_key, logger)
        cached_yt = {"url": yt_url, "channel": yt_channel}
        cache.set(yt_key_cache, cached_yt)
    else:
        logger.debug("YT lookup (HIT) -> using cached result")
        yt_url = cached_yt.get("url", "")
        yt_channel = cached_yt.get("channel", "")
        if yt_key and (not yt_url or not yt_channel):
            logger.debug("YT cached result incomplete -> re-querying")
            yt_url, yt_channel = youtube_search_best(artist, title, norm_label or label, yt_key, logger)
            cached_yt = {"url": yt_url, "channel": yt_channel}
            cache.set(yt_key_cache, cached_yt)

    yt_url = cached_yt.get("url", "")
    yt_channel = cached_yt.get("channel", "")

    tag = derive_decade_tag(year)
    if tag:
        logger.debug(f"Tag: {tag}")

    logger.success(f"Done: {artist or 'Unknown'} — {title or 'Unknown'}")
    return EnrichedRow(
        year=year or "",
        artist=artist or "",
        title=title or "",
        album=album or "",
        label=norm_label or (label or ""),
        genre=broad_genre or "",
        director=director or "",
        tag=tag or "",
        youtube_url=yt_url or "",
        youtube_channel=yt_channel or "",
    )


def run_pipeline(in_csv: Path, out_csv: Path, youtube_api_key: Optional[str], mb_user_agent: str, cache_path: Path, mb_rate_limit: float, logger: Logger) -> Tuple[int, int]:
    cache = JsonCache(cache_path, logger=logger)
    mb_client = MBClient(user_agent=mb_user_agent, rate_limit_sec=mb_rate_limit, logger=logger) if mb_user_agent else None

    rows_in = 0
    rows_out = 0

    with in_csv.open("r", encoding="utf-8-sig", newline="") as f_in, out_csv.open("w", encoding="utf-8", newline="") as f_out:
        reader = csv.DictReader(f_in)
        fieldnames = ["year", "artist", "title", "album", "label", "genre", "director", "tag", "youtube_url", "youtube_channel"]
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()
        logger.debug("Start processing rows...")
        
        for row in reader:
            rows_in += 1
            try:
                ttype = (row.get("Title Type") or row.get("TitleType") or "").strip().lower()
                if ttype and ttype not in ("music video", "musicvideo"):
                    logger.debug(f"Skip non-music-video row #{rows_in} (Title Type={ttype})")
                    continue

                enr = enrich_row(row, mb_client, youtube_api_key, cache, logger)
                writer.writerow({
                    "year": enr.year,
                    "artist": enr.artist,
                    "title": enr.title,
                    "album": enr.album,
                    "label": enr.label,
                    "genre": enr.genre,
                    "director": enr.director,
                    "tag": enr.tag,
                    "youtube_url": enr.youtube_url,
                    "youtube_channel": enr.youtube_channel,
                })
                rows_out += 1
                logger.debug(f"Wrote row #{rows_in}")
            except Exception as e:
                logger.warn(f"Row #{rows_in} failed: {e}")

    return rows_in, rows_out


# -------------------------------
# CLI
# -------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Enrich an IMDb music video CSV using MusicBrainz and YouTube")
    p.add_argument("--in", dest="in_csv", required=True, help="Path to IMDb CSV (export)")
    p.add_argument("--out", dest="out_csv", required=True, help="Path to write enriched CSV (e.g., 90s-enriched.csv)")
    p.add_argument("--youtube-api-key", dest="youtube_api_key", default=None, help="YouTube Data API v3 key")
    p.add_argument("--mb-user-agent", dest="mb_user_agent", default=MB_DEFAULT_UA, help=f"MusicBrainz User-Agent (default: {MB_DEFAULT_UA})")
    p.add_argument("--cache", dest="cache", default=".cache/enrich_cache.json", help="Path to JSON cache file")
    p.add_argument("--mb-rate", dest="mb_rate", type=float, default=1.0, help="MusicBrainz wait time between requests (seconds). Minimum 0.5")
    p.add_argument("--verbose", action="store_true", help="Enable verbose DEBUG logging")
    p.add_argument("--no-color", action="store_true", help="Disable ANSI color output")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    in_csv = Path(args.in_csv).expanduser().resolve()
    out_csv = Path(args.out_csv).expanduser().resolve()
    cache_path = Path(args.cache).expanduser().resolve()

    logger = Logger(use_color=not args.no_color, level=("DEBUG" if args.verbose else "INFO"))
    logger.debug("Debug logging enabled.")
    logger.debug(f"Color output: {'on' if (not args.no_color) else 'off'}")
    
    if not in_csv.exists():
        logger.error(f"Input CSV not found: {in_csv}")
        sys.exit(2)

    ensure_dir(out_csv)

    youtube_api_key = args.youtube_api_key
    mb_user_agent = args.mb_user_agent or MB_DEFAULT_UA
    mb_rate_limit = max(0.5, float(args.mb_rate))

    logger.info(f"Input:  {in_csv}")
    logger.info(f"Output: {out_csv}")
    logger.info(f"YouTube key: {'provided' if youtube_api_key else 'not provided'}")
    logger.info(f"MusicBrainz UA: {mb_user_agent}")
    logger.info(f"Cache: {cache_path}")
    logger.info(f"MB wait (sec): {mb_rate_limit}")

    rows_in, rows_out = run_pipeline(in_csv, out_csv, youtube_api_key, mb_user_agent, cache_path, mb_rate_limit, logger)
    logger.success(f"Processed rows: {rows_in} -> Enriched rows: {rows_out}")


if __name__ == "__main__":
    main()