# Product Requirements Document (PRD): musicvideo_from_csv.py

## Purpose & Scope

Automate the downloading, organization, and metadata generation for music videos using a CSV input. Output is structured for Kodi media center compatibility.

## User Workflow

- User provides a CSV file containing music video metadata and YouTube links.
- Script processes each row:
  - Downloads the YouTube video via yt-dlp.
  - Ensures the video is in MP4 format (remux, with optional recode fallback).
  - Writes a Kodi-compatible .nfo file with metadata.
  - Organizes output files by artist/album/title.

## Functional Requirements

- **CSV Parsing:** Accepts flexible field aliases for required and optional metadata.
- **Video Download:** Uses yt-dlp to fetch videos at best quality.
- **MP4 Output:** Remuxes to MP4; recodes if remux fails (optional).
- **Metadata Generation:** Creates Kodi .nfo files with all relevant metadata.
- **Directory Structure:** Outputs files in artist/album/title hierarchy.
- **CLI Options:** Supports overwrite, recode fallback, search fallback, and cookies for authentication.
- **Error Logging:** Logs failed downloads, outputs summary and failed rows as CSV.

## Error Handling

- Checks for required dependencies (yt-dlp, ffmpeg).
- Handles missing or invalid URLs.
- Attempts alternative search if download fails (unless disabled).
- Logs errors and outputs a summary.

## Extensibility

- Modular design allows for new metadata fields and output formats.

## Non-Functional Requirements

- Python 3 compatible, cross-platform.
- Efficient processing of large CSV files.
- Clear logging and error messages.