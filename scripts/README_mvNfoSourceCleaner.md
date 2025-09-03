# mvNfoSourceCleaner - Music Video NFO Source Cleaner

A Python tool that recursively searches for NFO files and cleans up their `<sources>` elements by removing duplicate URLs, unwanted attributes, and organizing source entries efficiently.

## Features

- **Recursive NFO Processing**: Scans all subdirectories for music video NFO files
- **Duplicate URL Removal**: Intelligently handles duplicate URLs, keeping the most informative version
- **Attribute Cleanup**: Removes unwanted 'index' and 'channel' attributes
- **Failed URL Preservation**: When duplicates exist, keeps versions marked as failed
- **Search URL Retention**: Preserves URLs marked with search=true attribute
- **Dry Run Mode**: Preview changes before applying them
- **Detailed Reporting**: Shows exactly what was cleaned in each file

## Installation

### Prerequisites

- Python 3.6+ installed on your system
- No additional packages required (uses standard library only)

### Script Installation

1. Clone or download the repository
2. Make the script executable:
   ```bash
   chmod +x mvNfoSourceCleaner.py
   ```

## Usage

### Basic Command

```bash
python3 mvNfoSourceCleaner.py /path/to/music/videos
```

### Command-Line Options

| Option | Description |
|--------|-------------|
| `directory` | Parent directory to search for NFO files (required) |
| `-d, --dry-run` | Show what would be done without making changes |
| `-v, --verbose` | Show detailed processing information |

### Examples

```bash
# Basic cleaning - apply changes
python3 mvNfoSourceCleaner.py /media/MusicVideos

# Preview changes without modifying files
python3 mvNfoSourceCleaner.py /media/MusicVideos --dry-run

# Verbose output with detailed information
python3 mvNfoSourceCleaner.py ./videos --verbose
```

## How It Works

### Source Cleaning Rules

1. **Duplicate URL Handling**:
   - When the same URL appears multiple times, keeps only one instance
   - Priority order: failed version > search version > regular version
   - This ensures failed download attempts are preserved for reference

2. **Attribute Removal**:
   - Removes `index` attributes (not needed for Kodi)
   - Removes `channel` attributes (YouTube channel info)
   - Preserves important attributes: `ts` (timestamp), `failed`, `search`

3. **NFO File Selection**:
   - Processes all `.nfo` files except `artist.nfo`
   - Focuses on musicvideo NFO files created by mvOrganizer

### Example Transformation

**Before cleaning:**
```xml
<sources>
    <url ts="2024-01-15T10:30:00" index="1">https://youtube.com/watch?v=abc123</url>
    <url ts="2024-01-15T10:35:00" failed="true">https://youtube.com/watch?v=abc123</url>
    <url ts="2024-01-15T10:40:00" search="true" channel="UC123">https://youtube.com/watch?v=xyz789</url>
    <url ts="2024-01-15T10:45:00" index="2">https://youtube.com/watch?v=xyz789</url>
</sources>
```

**After cleaning:**
```xml
<sources>
    <url ts="2024-01-15T10:35:00" failed="true">https://youtube.com/watch?v=abc123</url>
    <url ts="2024-01-15T10:40:00" search="true">https://youtube.com/watch?v=xyz789</url>
</sources>
```

Changes made:
- Kept failed version of abc123 (removed regular duplicate)
- Kept search version of xyz789 (removed regular duplicate)
- Removed all 'index' and 'channel' attributes

## Output Format

### Console Output

```
Searching for NFO files in: /media/MusicVideos
Found 245 NFO files

Processing NFO files...

Processing: the_beatles/hey_jude/hey_jude.nfo
  Removed 2 duplicate source(s)
  Removed 3 attribute(s)
  ✓ File updated

Processing: queen/bohemian_rhapsody/bohemian_rhapsody.nfo
  Removed 1 attribute(s)
  ✓ File updated

Processing Summary:
============================================================
Files found:        245
Files processed:    245
Files modified:     37
Sources removed:    42
Attributes removed: 89
Errors:            0
============================================================
```

### Dry Run Output

When using `--dry-run`, the tool shows:
1. An example of the cleaning transformation
2. Which files would be modified
3. What changes would be made
4. No actual file modifications

## Use Cases

### After Bulk Downloads

When you've processed many videos with mvOrganizer and some had multiple download attempts:
```bash
python3 mvNfoSourceCleaner.py /media/MusicVideos
```

### Before Kodi Library Update

Clean up NFO files to ensure Kodi reads them efficiently:
```bash
python3 mvNfoSourceCleaner.py /media/MusicVideos --dry-run
# Review changes, then run without --dry-run
```

### Regular Maintenance

Periodically clean up accumulated duplicate sources:
```bash
# Monthly cleanup task
python3 mvNfoSourceCleaner.py /media/MusicVideos
```

## Integration with mvOrganizer

This tool is designed to work with NFO files created by mvOrganizer.py:

1. **mvOrganizer** creates NFO files with source tracking
2. **mvNfoSourceCleaner** cleans up duplicate sources and attributes
3. Result: Clean, efficient NFO files for Kodi

The cleaner preserves important mvOrganizer metadata:
- Failed download attempts (for troubleshooting)
- Search-based URLs (to track auto-discovered videos)
- Timestamps (to track download history)

## Safety Features

- **No Data Loss**: Only removes true duplicates, preserves unique information
- **Parse Error Handling**: Skips malformed NFO files instead of crashing
- **Dry Run Mode**: Always preview changes before applying
- **Backup Friendly**: Original file structure preserved

## Troubleshooting

### No NFO Files Found

- Verify the directory path is correct
- Check that NFO files exist in subdirectories
- Ensure files have `.nfo` extension

### Parse Errors

- Some NFO files may be corrupted or non-standard
- The tool skips these and continues processing
- Error count shown in summary

### No Changes Made

- Sources may already be clean
- Use `--verbose` to see detailed processing

## Best Practices

1. **Always Dry Run First**: Use `--dry-run` to preview changes
2. **Backup Important Data**: While safe, backups are always recommended
3. **Regular Cleaning**: Run monthly or after bulk downloads
4. **Check Logs**: Review which files were modified

## Future Enhancements

Potential improvements:
- Backup option before modifications
- Detailed change log export
- Custom attribute removal rules
- Source URL validation
- Integration with duplicate finder

## License

This tool is for personal use only. Always maintain backups before batch processing files.

## Version History

- **1.0.0** - Initial release
  - Duplicate URL removal with intelligent selection
  - Attribute cleanup (index, channel)
  - Dry run mode
  - Detailed reporting