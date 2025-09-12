# mvReplacer - Music Video Replacer for Kodi

A Python tool that searches for and downloads alternative sources for existing music videos. Takes NFO file paths as input, searches YouTube for new sources, downloads if unique sources are found, and updates the NFO metadata.

## Features

- **NFO-Based Processing**: Works with existing Kodi NFO files
- **Smart Source Detection**: Identifies and skips duplicate sources
- **YouTube Search**: Automatically searches for alternative sources
- **Batch Processing**: Can process multiple NFO files at once
- **Dry Run Mode**: Preview changes without downloading
- **Source Tracking**: Updates NFO with all attempted sources
- **Color-Coded Output**: Clear visual feedback during processing

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
   chmod +x mvReplacer.py
   ```

## Usage

### Basic Command

```bash
python mvReplacer.py /path/to/video.nfo
```

### Command-Line Options

| Option | Description |
|--------|-------------|
| `nfo_files` | One or more NFO file paths to process (required) |
| `--cookies` | Cookie file for YouTube authentication |
| `--dry-run` | Show what would be done without making changes |

### Examples

```bash
# Process single NFO file
python mvReplacer.py /music_videos/artist/song.nfo

# Process multiple NFO files
python mvReplacer.py video1.nfo video2.nfo video3.nfo

# Use wildcard to process all NFO files in directory
python mvReplacer.py /music_videos/*/*.nfo

# Dry run to preview changes
python mvReplacer.py /path/to/video.nfo --dry-run

# Use cookies for authentication
python mvReplacer.py /path/to/video.nfo --cookies cookies.txt
```

## How It Works

### Processing Flow

1. **Parse NFO**: Reads the existing NFO file to extract artist and title
2. **Check Sources**: Identifies all previously attempted source URLs
3. **Search YouTube**: Searches for "{artist} {title} official music video"
4. **Verify Uniqueness**: Checks if the found URL is not already in sources
5. **Download Video**: If unique, downloads and replaces the existing video
6. **Update NFO**: Adds the new source URL to the NFO metadata

### NFO Source Tracking

The script maintains a complete history of all download attempts in the NFO:

```xml
<sources>
    <url ts="2024-01-15T10:30:00" search="true">https://www.youtube.com/watch?v=ABC123</url>
    <url ts="2024-01-16T14:20:00" search="true">https://www.youtube.com/watch?v=XYZ789</url>
</sources>
```

- `ts`: Timestamp of when the download was attempted
- `search`: Indicates the URL was found via search (always true for this tool)
- `failed`: Added if the download failed (optional)

## File Structure

### Expected Directory Layout

```
music_videos/
├── artist_name/
│   ├── song_title.mp4
│   └── song_title.nfo
```

The script expects:
- NFO files to be named identically to their video files (except extension)
- Video files to be MP4 format
- NFO files to contain at minimum `<artist>` and `<title>` elements

## Terminal Output

Color-coded output for easy monitoring:
- 🟦 **Blue**: Download in progress
- 🟩 **Green**: Successful operations
- 🟨 **Yellow**: Warnings and skipped items
- 🔴 **Red**: Errors and failures
- 🟣 **Purple**: Headers and file information
- 🔷 **Cyan**: Informational messages

### Sample Output

```
Music Video Replacer - Batch Mode
Processing 3 NFO file(s)
------------------------------------------------------------

Processing: /music_videos/the_weeknd/blinding_lights.nfo
  Artist: The Weeknd
  Title: Blinding Lights
  Existing sources: 1
    1. https://www.youtube.com/watch?v=4NRXx6U8ABQ
  Video file exists: blinding_lights.mp4
  Searching YouTube: The Weeknd Blinding Lights official music video
  Found video: https://www.youtube.com/watch?v=fHI8X4OXluQ
  Found new unique source, attempting download
  Downloading from: https://www.youtube.com/watch?v=fHI8X4OXluQ
  ✓ Download successful
  ✓ NFO updated
  ✓ Video replaced successfully

============================================================
Processing Summary
------------------------------------------------------------
Total processed: 3
Replaced: 2
Skipped: 1
Failed: 0
============================================================
```

## Use Cases

### Finding Better Quality Videos

If you have low-quality videos, use this tool to search for and download better versions:

```bash
# Replace all videos in a directory
python mvReplacer.py /music_videos/*/*.nfo
```

### Recovering Lost Videos

If video files are missing but NFO files remain:

```bash
# The tool will detect missing videos and attempt to download them
python mvReplacer.py /path/to/video.nfo
```

### Testing Alternative Sources

Use dry-run mode to see what sources would be found:

```bash
python mvReplacer.py *.nfo --dry-run
```

## Integration with Other Tools

### Works Well With

- **mvOrganizer.py**: Initial organization and download
- **mvValidator.py**: Verify files before/after replacement
- **mvNfoSourceCleaner.py**: Clean up duplicate sources after multiple runs
- **mvDuplicateFinder.py**: Find duplicates before replacing

### Workflow Example

```bash
# 1. Validate existing structure
python mvValidator.py /music_videos --rules all

# 2. Replace videos with new sources
python mvReplacer.py /music_videos/*/*.nfo

# 3. Clean up any duplicate sources
python mvNfoSourceCleaner.py /music_videos

# 4. Export updated metadata
python mvNfoExporter.py /music_videos -o updated_videos.csv
```

## Tips and Best Practices

### Performance

1. **Batch Processing**: Process multiple files at once for efficiency
2. **Network Stability**: Ensure stable internet for downloads
3. **Storage Space**: Verify adequate disk space before batch replacement

### Quality Control

1. **Dry Run First**: Always test with `--dry-run` before actual replacement
2. **Backup NFOs**: Keep backups of NFO files before modification
3. **Verify Results**: Check replaced videos for quality and correctness

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

**No new sources found**
- The search query might be too specific
- Try manually searching YouTube to verify availability
- Check if the artist/title in NFO is correct

**Download failures**
- Check internet connection
- Try with `--cookies` if authentication required
- Verify YouTube URL is accessible

**NFO parsing errors**
- Ensure NFO is valid XML format
- Check that `<artist>` and `<title>` elements exist
- Validate NFO structure matches Kodi specifications

## License

This tool is for personal use only. Respect copyright laws and YouTube's Terms of Service.

## Version History

- **1.0.0** - Initial release
  - NFO-based video replacement
  - YouTube search integration
  - Batch processing support
  - Dry-run mode