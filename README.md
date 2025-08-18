# Music Video CSV Downloader (.nfo generator)

Downloads YouTube links from a CSV and writes Kodi-compatible .nfo files beside the videos. Script: [scripts/musicvideo_from_csv.py](scripts/musicvideo_from_csv.py)

Features
- Best-quality download via yt-dlp; final container MP4 (remux; optional recode fallback).
- Output layout: <outdir>/<Artist>/<Album>/<Title>.mp4 plus a sibling .nfo.
- Flexible, case-insensitive CSV headers with common aliases.
- Filesystem-safe sanitization of Artist/Album/Title.
- Clear logging and summary.
- Maintains a source history in the .nfo under <source> with ordered <url index="n" ts="YYYY-MM-DDThh:mm:ssZ" channel="YouTubeChannel">...</url> entries; index 0 is always the most recent YouTube URL.

Requirements
- Python 3.8+
- yt-dlp
- ffmpeg

Install
- macOS (Homebrew):

```bash
brew install yt-dlp ffmpeg
```

- Python (optional, via pipx for isolated install of yt-dlp):

```bash
pipx install yt-dlp
```

Usage
- Basic:

```bash
python3 scripts/musicvideo_from_csv.py --csv data/tracks.csv --outdir output/musicvideos
```

- With fallback to recode if remux cannot produce MP4:

```bash
python3 scripts/musicvideo_from_csv.py --csv data/tracks.csv --outdir output/musicvideos --recode-fallback
```

- Overwrite existing MP4s:

```bash
python3 scripts/musicvideo_from_csv.py --csv data/tracks.csv --outdir output/musicvideos --overwrite
```

CSV schema
- Required fields (case-insensitive). Accepted header names:
  - year: year, release_year
  - title: title, track, track_title
  - artist: artist, artists
  - album: album
  - label: label, record_label, studio
  - youtube: youtube, youtube_url, link, url
- Optional fields (case-insensitive). Accepted header names:
  - director: director, directed_by
  - genre: genre, genres, style
  - youtube_channel: youtube_channel, channel, uploader, youtube_uploader, youtube_channel_name
  - tag: tag, tags

Sample CSV

```csv
Year,Title,Artist,Album,Label,YouTube,Director,Genre,YouTube_Channel,Tag
2020,Example Track,Example Artist,Example Album,Example Label,https://www.youtube.com/watch?v=dQw4w9WgXcQ,Jane Doe,Pop,ExampleChannel,party; feel good
```

- Alternate headers are accepted, e.g.:

```csv
release_year,track_title,artist,album,record_label,youtube_url,directed_by,genres,channel,tags
2019,Alt Track,Alt Artist,Alt Album,Alt Label,https://youtu.be/abc123,John Smith,Rock;Alternative,AltUploader,uplifting; 90s
```

Output layout
- Videos: <outdir>/<Artist>/<Album>/<Title>.mp4
- NFOs:   <outdir>/<Artist>/<Album>/<Title>.nfo

Kodi .nfo example

```xml
<?xml version="1.0" encoding="UTF-8"?>
<musicvideo>
  <title>Example Track</title>
  <album>Example Album</album>
  <studio>Example Label</studio>
  <year>2020</year>
  <director>Jane Doe</director>
  <genre>Pop</genre>
  <artist>Example Artist</artist>
  <tag>party, feel good</tag>
  <source>
    <url index="0" ts="2025-08-15T18:30:00Z" channel="ExampleChannel">https://www.youtube.com/watch?v=dQw4w9WgXcQ</url>
    <!-- older entries (if any) are shifted to index="1", "2", ... -->
  </source>
</musicvideo>
```

Notes
- Multiple artists/directors/genres can be separated by comma or semicolon; each becomes its own tag element.
- The Tag field accepts comma or semicolon; values are written into a single <tag> element as a comma-separated list.
- The .nfo maintains a source history: on each run, the current YouTube URL is written as <url index="0" ts="..." channel="YouTubeChannel"/> and any previous URLs (if present) are shifted to index="1", "2", etc.
- Filenames are sanitized: reserved characters <>:"/\\|?* are replaced with underscores; whitespace/dots trimmed.
- Existing outputs are skipped unless --overwrite is given.
- Requires yt-dlp and ffmpeg in PATH.

Troubleshooting
- Missing dependencies:

```bash
brew install yt-dlp ffmpeg
```

- If remux fails to produce MP4, add --recode-fallback.