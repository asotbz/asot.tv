# mvDuplicateFinder - Music Video Duplicate Finder

A Python tool that recursively searches for NFO files and identifies duplicate music video tracks using fuzzy matching on artist and title metadata.

## Features

- **Recursive NFO Search**: Scans all subdirectories for music video NFO files
- **Fuzzy Matching**: Uses intelligent text comparison to find similar artist/title combinations
- **Configurable Threshold**: Adjust sensitivity for duplicate detection
- **Detailed Reporting**: Shows duplicate groups with match percentages
- **File Size Information**: Displays video file sizes when available
- **Export Capability**: Generate text reports of found duplicates
- **Smart Normalization**: Handles variations in text (case, special characters, common abbreviations)

## Installation

### Prerequisites

- Python 3.6+ installed on your system
- No additional packages required (uses standard library only)

### Script Installation

1. Clone or download the repository
2. Make the script executable:
   ```bash
   chmod +x mvDuplicateFinder.py
   ```

## Usage

### Basic Command

```bash
python3 mvDuplicateFinder.py /path/to/music/videos
```

### Command-Line Options

| Option | Description |
|--------|-------------|
| `directory` | Parent directory to search for NFO files (required) |
| `-t, --threshold` | Fuzzy match threshold between 0-1 (default: 0.85) |
| `-e, --export` | Export results to a text file |

### Examples

```bash
# Basic scan with default threshold (85%)
python3 mvDuplicateFinder.py /media/MusicVideos

# More strict matching (90% similarity required)
python3 mvDuplicateFinder.py /media/MusicVideos --threshold 0.9

# Export results to a file
python3 mvDuplicateFinder.py ./videos --export duplicates_report.txt

# More lenient matching (75% similarity)
python3 mvDuplicateFinder.py ./videos -t 0.75
```

## How It Works

### NFO File Detection

The script searches for all `.nfo` files (except `artist.nfo`) recursively in the specified directory. It expects NFO files in Kodi's musicvideo format:

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<musicvideo>
    <artist>The Beatles</artist>
    <title>Hey Jude</title>
    <!-- other metadata ignored for duplicate detection -->
</musicvideo>
```

### Fuzzy Matching Algorithm

1. **Text Normalization**:
   - Converts to lowercase
   - Removes special characters
   - Normalizes Unicode (é → e, ñ → n)
   - Standardizes common variations:
     - "and" → "&"
     - "featuring/feat" → "ft"
     - "versus" → "vs"
     - "part" → "pt"

2. **Scoring**:
   - Artist match: 40% weight
   - Title match: 60% weight
   - Combined score must exceed threshold

### Duplicate Grouping

Tracks are grouped when their combined fuzzy match score exceeds the threshold. Each group shows:
- The "original" (first found)
- All duplicates with their match percentages
- File paths and sizes

## Output Format

### Terminal Output

```
Music Video Duplicate Report
================================================================================

Duplicate Group 1:
----------------------------------------

[ORIGINAL]
Artist: The Beatles
Title:  Hey Jude
NFO:    /media/MusicVideos/the_beatles/hey_jude/hey_jude.nfo
Video:  /media/MusicVideos/the_beatles/hey_jude/hey_jude.mp4 (125.3 MB)

[DUPLICATE (92% match)]
Artist: Beatles
Title:  Hey Jude (Remastered)
NFO:    /media/MusicVideos/beatles/hey_jude_remastered/hey_jude_remastered.nfo
Video:  /media/MusicVideos/beatles/hey_jude_remastered/hey_jude_remastered.mp4 (132.1 MB)

================================================================================

Summary:
  Total tracks analyzed: 543
  Duplicate groups found: 12
  Total duplicate files: 15
```

## Threshold Guidelines

| Threshold | Use Case |
|-----------|----------|
| 0.95-1.00 | Near-exact matches only |
| 0.85-0.94 | Default - catches most duplicates with minor variations |
| 0.75-0.84 | Includes remixes, live versions with similar names |
| 0.65-0.74 | Very loose matching - may have false positives |

## Tips for Best Results

### Before Running

1. **Ensure NFO Files Exist**: Use mvOrganizer.py to generate NFO files if missing
2. **Check Artist Consistency**: Standardize artist names in your collection
3. **Consider Versions**: Decide if remixes/live versions should be considered duplicates

### Interpreting Results

1. **High Match Scores (90%+)**: Likely true duplicates
2. **Medium Scores (80-89%)**: May be variations (remix, remaster, live)
3. **Threshold Scores**: Review manually before deleting

### Common Duplicate Patterns

- Same video with different quality/format
- Remastered versions with similar titles
- Artist name variations ("The Beatles" vs "Beatles")
- Title variations ("Part 1" vs "Pt. 1")

## Integration with mvOrganizer

This tool is designed to work with music video collections organized by mvOrganizer.py:

1. Use mvOrganizer to download and organize videos
2. Run mvDuplicateFinder to identify duplicates
3. Manually review and remove unwanted duplicates
4. Keep the higher quality version when applicable

## Troubleshooting

### No NFO Files Found

- Verify the directory path is correct
- Check that NFO files exist in subdirectories
- Ensure files have `.nfo` extension (lowercase)

### Too Many/Few Duplicates Found

- Adjust the threshold:
  - Increase for fewer false positives
  - Decrease to catch more variations

### Unicode/Special Character Issues

The script handles most Unicode normalization automatically, but some edge cases may require manual review.

## Future Enhancements

Potential improvements for future versions:
- Compare additional metadata (year, director, duration)
- Automatic duplicate removal options
- Video quality comparison
- GUI interface
- Database backend for large collections

## License

This tool is for personal use only. Always maintain backups before removing files.

## Version History

- **1.0.0** - Initial release
  - Recursive NFO scanning
  - Fuzzy artist/title matching
  - Configurable threshold
  - Export functionality