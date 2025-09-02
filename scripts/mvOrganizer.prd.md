# Product Requirements Document: mvOrganizer.py

## Overview
Automate downloading, organizing, and metadata generation for music videos using CSV input. Output is structured for Kodi media center compatibility.

## CSV Input Specification

### Required Fields
- **artist**: Artist credit
- **title**: Track title

### Optional Fields
- **year**: Release year (YYYY format)
- **album**: Album name
- **label**: Record label (normalized for filtering)
- **genre**: Primary genre (normalized to broad categories: Hip Hop/R&B, Rock, Pop, Metal, Country)
- **director**: Director credit (multiple names preserved as single string)
- **tag**: Tags (comma-separated list)
- **youtube_url**: YouTube video URL

## Core Functionality

### 1. Video Download
- **Tool**: yt-dlp with best quality settings
- **Format**: MP4 (using `--preset-alias mp4`)
- **Rate Limiting**: `--sleep-requests 1 --sleep-interval 1 --retry-sleep fragment:300`

### 2. Download Logic
**New Video (file doesn't exist):**
1. If youtube_url provided: attempt download
2. If download fails or no URL: search YouTube (unless `--no-search` flag)
   - Query: "{artist} {title} official music video"
   - Limit: 1 result
3. Record all unique attempted sources with timestamps

**Existing Video (file exists):**
1. Check for NFO file; create if missing
2. Skip if URL not unique in sources
3. With `--overwrite` flag: attempt download from new URL (no search fallback)

### 3. File Organization
**Naming Convention**:
- Convert to lowercase
- Remove special characters
- Normalize diacritics (ä → a)
- Replace spaces with underscores

**Directory Structure**: `{output_dir}/{artist}/{title}/`

**Output Files**:
- `{title}.mp4` - Video file
- `{title}.nfo` - Metadata file

### 4. NFO Metadata Generation
**XML Structure**:
```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<musicvideo>
    <year>YYYY</year>
    <artist>Artist Name</artist>
    <title>Track Title</title>
    <album>Album Name</album>
    <studio>Label Name</studio>
    <genre>Genre</genre>
    <director>Director Name(s)</director>
    <tag>Tag1</tag>
    <tag>Tag2</tag>
    <sources>
        <url ts="timestamp" failed="true/false" search="true/false">URL</url>
    </sources>
</musicvideo>
```

**Notes**:
- Pretty-print XML output
- Include only provided fields
- Multiple tags create multiple `<tag>` elements
- Sources track download history with attributes:
  - `ts`: Download attempt timestamp
  - `failed`: Set if download failed
  - `search`: Set if URL from search
- De-duplicate source URLs (keep latest timestamp)

## CLI Options
- `--csv`: csv input file (required)
- `--output-dir`: Base output directory (required)
- `--overwrite`: Re-download existing videos from new URLs
- `--no-search`: Disable YouTube search fallback
- `--cookies`: Cookie file for authentication

## Technical Requirements

### Dependencies
- Python 3.x
- yt-dlp
- ffmpeg

### Error Handling
- Validate required dependencies on startup
- Check CSV format and required fields
- Handle invalid/missing URLs gracefully
- Log all errors with context (row number, artist/title)

### Logging
- Color-coded console output
- Progress indicators with row number and artist/title
- Summary statistics on completion

## Non-Functional Requirements
- Cross-platform compatibility
- Efficient large CSV processing
- Modular, reusable functions
- Clear documentation and code comments