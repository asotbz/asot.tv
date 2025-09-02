# mvOrganizer - Music Video Downloader and Organizer for Kodi

A Python tool that automates the downloading, organization, and metadata generation for music videos using CSV input. The output is structured for Kodi media center compatibility.

## Features

- **Automated Downloads**: Downloads music videos from YouTube using yt-dlp
- **Smart Organization**: Creates artist/title directory structure
- **Kodi Integration**: Generates NFO metadata files compatible with Kodi
- **Duplicate Handling**: Intelligently manages existing videos and metadata
- **Search Fallback**: Automatically searches YouTube when URLs are missing
- **Rate Limiting**: Built-in throttling to respect YouTube's rate limits
- **Progress Tracking**: Color-coded terminal output with detailed progress

## Installation

### Prerequisites

1. **Python 3.6+** installed on your system
2. **yt-dlp** - Install via pip:
   ```bash
   pip install yt-dlp
   ```
3. **ffmpeg** - Required for video processing:
   - **macOS**: `brew install ffmpeg`
   - **Ubuntu/Debian**: `sudo apt install ffmpeg`
   - **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html)

### Script Installation

1. Clone or download the repository
2. Make the script executable:
   ```bash
   chmod +x mvOrganizer.py
   ```

## Usage

### Basic Command

```bash
python mvOrganizer.py input.csv -o /path/to/output
```

### Command-Line Options

| Option | Description |
|--------|-------------|
| `csv_file` | Path to CSV file containing music video metadata (required) |
| `-o, --output-dir` | Base output directory for organized videos (required) |
| `--overwrite` | Re-download existing videos from new URLs |
| `--no-search` | Disable YouTube search fallback |
| `--cookies` | Cookie file for YouTube authentication |

### Examples

```bash
# Basic usage
python mvOrganizer.py videos.csv -o /media/MusicVideos

# Force re-download with new URLs
python mvOrganizer.py videos.csv -o ./output --overwrite

# Disable search fallback and use cookies for auth
python mvOrganizer.py videos.csv -o ./output --no-search --cookies cookies.txt
```

## CSV Format

### Required Fields

- **artist**: Artist name
- **title**: Song title

### Optional Fields

- **year**: Release year (YYYY format)
- **album**: Album name
- **label**: Record label
- **genre**: Music genre (e.g., Rock, Pop, Hip Hop/R&B)
- **director**: Music video director
- **tag**: Comma-separated tags
- **youtube_url**: YouTube video URL

### Example CSV

```csv
year,artist,title,album,label,genre,director,tag,youtube_url
2023,The Weeknd,Blinding Lights,After Hours,Republic,Pop,Anton Tammi,"synthwave,80s",https://www.youtube.com/watch?v=4NRXx6U8ABQ
2022,Dua Lipa,Levitating,Future Nostalgia,Warner,Pop,,"disco,dance",
2021,Olivia Rodrigo,good 4 u,SOUR,Geffen,Rock,Petra Collins,"pop punk,teen",https://www.youtube.com/watch?v=gNi_6U5Pm_o
```

### Field Aliases

The script recognizes common field name variations:
- `artists` → `artist`
- `song` or `track` → `title`
- `record_label` → `label`
- `youtube` or `url` → `youtube_url`
- `tags` → `tag`

## Output Structure

### Directory Layout

```
output_dir/
├── the_weeknd/
│   ├── blinding_lights.mp4
│   └── blinding_lights.nfo
├── dua_lipa/
│   ├── levitating.mp4
│   └── levitating.nfo
└── olivia_rodrigo/
    ├── good_4_u.mp4
    └── good_4_u.nfo
```

### File Naming

- Converted to lowercase
- Special characters are removed
- Diacritics are normalized (ä → a, é → e)
- Spaces are replaced with underscores
- Multiple underscores are condensed to single

### NFO Format

Generated NFO files follow Kodi's musicvideo specification:

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<musicvideo>
    <year>2023</year>
    <artist>The Weeknd</artist>
    <title>Blinding Lights</title>
    <album>After Hours</album>
    <studio>Republic</studio>
    <genre>Pop</genre>
    <director>Anton Tammi</director>
    <tag>synthwave</tag>
    <tag>80s</tag>
    <sources>
        <url ts="2024-01-15T10:30:00" failed="false" search="false">https://www.youtube.com/watch?v=4NRXx6U8ABQ</url>
    </sources>
</musicvideo>
```

## Download Logic

### New Videos (File Doesn't Exist)

1. **URL Provided**: Attempts download from provided YouTube URL
2. **No URL/Failed**: Searches YouTube for "{artist} {title} official music video"
3. **Tracking**: Records all attempted URLs with timestamps in NFO

### Existing Videos (File Exists)

1. **NFO Check**: Creates NFO if missing
2. **URL Comparison**: Checks if CSV URL is already in sources
3. **Overwrite Mode**: Downloads from new URL if `--overwrite` flag is set
4. **Skip**: Skips download if URL exists in sources or overwrite is disabled

## Error Handling

- **Dependency Check**: Verifies yt-dlp and ffmpeg are installed
- **CSV Validation**: Checks for required fields and proper formatting
- **Download Failures**: Logs errors and continues processing
- **Network Issues**: Implements retry logic with exponential backoff
- **Invalid URLs**: Validates YouTube URLs before attempting download

## Rate Limiting

Built-in throttling to avoid YouTube rate limits:
- 1 second delay between requests
- 1 second interval between downloads
- 5 minute retry sleep for fragment failures

## Terminal Output

Color-coded output for easy monitoring:
- 🟦 **Blue**: Download in progress
- 🟩 **Green**: Successful operations
- 🟨 **Yellow**: Warnings and skipped items
- 🔴 **Red**: Errors and failures
- 🟣 **Purple**: Headers and important info

### Sample Output

```
Music Video Organizer
Processing: videos.csv
Output directory: /media/MusicVideos
------------------------------------------------------------

[Row 2] The Weeknd - Blinding Lights
  Downloading from: https://www.youtube.com/watch?v=4NRXx6U8ABQ
  ✓ Download successful
  Output: the_weeknd/blinding_lights.mp4

[Row 3] Dua Lipa - Levitating
  Searching YouTube: Dua Lipa Levitating official music video
  Found video: https://www.youtube.com/watch?v=TUVcZfQe-Kw
  ✓ Download successful
  Output: dua_lipa/levitating.mp4

============================================================
Processing Summary
------------------------------------------------------------
Total processed: 3
Downloaded: 2
Skipped: 0
Failed: 1
NFO files created: 3
============================================================
```

## Tips and Best Practices

### CSV Preparation

1. **Clean Data**: Remove extra spaces and special characters
2. **Validate URLs**: Ensure YouTube URLs are correct format
3. **Consistent Genres**: Use standardized genre names for better organization
4. **Director Credits**: Preserve full names (e.g., "Anton Tammi")

### Performance Optimization

1. **Batch Processing**: Process large CSV files overnight
2. **Network Stability**: Ensure stable internet connection
3. **Storage Space**: Verify adequate disk space (videos can be 100-500MB each)

### Kodi Integration

1. **Library Updates**: Set Kodi to auto-scan the output directory
2. **Thumbnail Support**: Kodi will fetch thumbnails from YouTube
3. **Custom Tags**: Use tags for smart playlists in Kodi

### Authentication

If you encounter authentication issues:

1. Export cookies from your browser using a cookie extension
2. Save as `cookies.txt` in Netscape format
3. Use `--cookies cookies.txt` flag

## Troubleshooting

### Common Issues

**yt-dlp not found**
```bash
pip install --upgrade yt-dlp
```

**ffmpeg not found**
- Ensure ffmpeg is in your system PATH
- Test with: `ffmpeg -version`

**Download failures**
- Check internet connection
- Try with `--cookies` if authentication required
- Verify YouTube URL is valid

**Permission denied**
- Ensure write permissions for output directory
- Run with appropriate user privileges

## License

This tool is for personal use only. Respect copyright laws and YouTube's Terms of Service.

## Contributing

Contributions are welcome! Please ensure:
- Code follows PEP 8 style guidelines
- Functions include docstrings
- New features include documentation

## Version History

- **1.0.0** - Initial release with core functionality
  - CSV processing
  - YouTube downloading
  - NFO generation
  - Kodi compatibility