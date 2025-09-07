# mvNfoExporter - Music Video NFO to CSV Exporter

Export music video metadata from NFO files to CSV format, creating a master list of your entire collection.

## Overview

`mvNfoExporter.py` recursively searches for NFO files in a directory tree and exports their metadata to a CSV file. It intelligently identifies the most recent successful download URL from the `<sources>` element and includes all metadata fields defined in the PRD.

## Features

- **Recursive NFO Discovery**: Finds all `.nfo` files (except `artist.nfo`) in the directory tree
- **Smart URL Selection**: Identifies the most recent successful download URL (excludes failed attempts)
- **Complete Metadata Export**: Exports all PRD-defined fields to CSV
- **Proper CSV Escaping**: Automatically quotes fields containing commas, quotes, or newlines
- **Progress Tracking**: Shows progress for large collections
- **Error Handling**: Gracefully handles malformed NFO files
- **Sorted Output**: CSV is sorted by artist and title for easy browsing

## Usage

### Basic Usage
```bash
python3 mvNfoExporter.py /path/to/music/videos
```

### Specify Output File
```bash
python3 mvNfoExporter.py /path/to/music/videos -o my_collection.csv
```

### Command Line Options
- `directory` (required): Parent directory to search for NFO files
- `-o`, `--output`: Output CSV filename (default: `music_videos.csv`)

## CSV Format

The exported CSV includes these fields (in order):
- `year` - Release year
- `artist` - Artist name
- `title` - Video title
- `album` - Album name (if applicable)
- `label` - Record label (from `<studio>` element in NFO)
- `genre` - Music genre
- `director` - Video director
- `tag` - Custom tags (comma-separated if multiple `<tag>` elements exist)
- `youtube_url` - Most recent successful YouTube URL

### CSV Escaping

The exporter properly handles special characters in CSV fields:
- **Commas in fields**: Automatically quoted (e.g., `"Rock, Pop"`)
- **Quotes in fields**: Escaped with double-quotes (e.g., `"She said ""Hello"""`)
- **Multi-line content**: Preserved and properly quoted
- **Empty fields**: Represented as empty strings (no quotes needed)

## Field Mapping

### Label Field
The `label` field in the CSV is extracted from the `<studio>` element in the NFO file, not from a `<label>` element. This follows Kodi's standard NFO format for music videos.

### Tag Field
The `tag` field combines all `<tag>` elements from the NFO into a comma-separated list. For example:
```xml
<tag>80s</tag>
<tag>classic</tag>
<tag>new wave</tag>
```
Becomes: `"80s, classic, new wave"` in the CSV.

## URL Selection Logic

The script identifies the most recent successful download URL by:
1. Parsing the `<sources>` element in each NFO
2. Filtering out URLs with `failed="true"` attribute
3. Sorting remaining URLs by their `ts` (timestamp) attribute
4. Selecting the most recent URL

Example NFO sources:
```xml
<sources>
    <url ts="2024-01-15T10:30:00" failed="true">https://youtube.com/watch?v=abc123</url>
    <url ts="2024-01-15T10:35:00">https://youtube.com/watch?v=abc123</url>
    <url ts="2024-01-16T14:20:00">https://youtube.com/watch?v=def456</url>
</sources>
```
Would select: `https://youtube.com/watch?v=def456` (most recent successful)

## Examples

### Export Entire Collection
```bash
python3 mvNfoExporter.py /media/MusicVideos
```

Output:
```
Searching for NFO files in: /media/MusicVideos
Found 523 NFO files

Processing NFO files...
Progress: 10/523 files processed...
Progress: 20/523 files processed...
...

Writing CSV file: music_videos.csv
✓ Successfully wrote 518 entries to CSV

Export Summary:
============================================================
Files found:     523
Files processed: 523
Files exported:  518
Errors:          5

CSV file created: music_videos.csv
============================================================
```

### Create Collection Inventory
```bash
python3 mvNfoExporter.py ~/Videos/MusicVideos -o collection_2024.csv
```

### Process Specific Artist Directories
```bash
python3 mvNfoExporter.py /media/MusicVideos/A-M -o artists_a_to_m.csv
```

## Sample CSV Output

```csv
year,artist,title,album,label,genre,director,tag,youtube_url
1984,Duran Duran,Wild Boys,Arena,EMI,New Wave,Russell Mulcahy,"80s, classic, new wave",https://youtube.com/watch?v=M43wsiNBwmo
2007,Justice,D.A.N.C.E.,Cross,Ed Banger,Electronic,So Me,"french house, electronic",https://youtube.com/watch?v=sy1dYFGkPUE
1982,Michael Jackson,Thriller,Thriller,Epic,Pop,John Landis,"zombie, classic, halloween",https://youtube.com/watch?v=sOnqjkJTMaA
1985,"Tears for Fears","Shout","Songs from the Big Chair","Mercury","New Wave, Pop","Nigel Dick","80s, anthem",https://youtube.com/watch?v=example
```

Note how fields containing commas (like genres "New Wave, Pop") are automatically quoted to ensure proper CSV parsing.

## Integration with mvOrganizer Workflow

This tool complements the mvOrganizer workflow:

1. **Download & Organize**: Use `mvOrganizer.py` to download and organize videos
2. **Find Duplicates**: Use `mvDuplicateFinder.py` to identify duplicates
3. **Clean Sources**: Use `mvNfoSourceCleaner.py` to clean up NFO files
4. **Export Collection**: Use `mvNfoExporter.py` to create a master CSV list

### Workflow Example
```bash
# 1. Download new videos
python3 mvOrganizer.py music_videos.csv /media/MusicVideos

# 2. Check for duplicates
python3 mvDuplicateFinder.py /media/MusicVideos

# 3. Clean up NFO sources
python3 mvNfoSourceCleaner.py /media/MusicVideos

# 4. Export updated collection
python3 mvNfoExporter.py /media/MusicVideos -o collection_master.csv
```

## Use Cases

### Collection Management
- Create a spreadsheet-friendly inventory of your collection
- Share your collection list without sharing the actual files
- Import into database or media management software

### Backup Documentation
- Document what videos you have before backup
- Verify collection integrity after restore
- Track collection growth over time

### Re-download Planning
- Identify videos with failed downloads (empty youtube_url)
- Find videos downloaded from non-preferred sources
- Plan re-downloads or upgrades

## Error Handling

The script handles various error conditions:
- **Malformed XML**: Skips NFO files that can't be parsed
- **Missing Required Fields**: Skips entries without artist/title
- **Invalid Timestamps**: Falls back to dateless sorting
- **File Access Errors**: Reports but continues processing

## Tips

1. **Regular Exports**: Run periodically to maintain an up-to-date inventory
2. **Version Control**: Keep dated copies of exports (e.g., `collection_2024_01.csv`)
3. **Spreadsheet Analysis**: Import into Excel/Google Sheets for analysis:
   - Sort by year, genre, or director
   - Filter by missing metadata
   - Create pivot tables for statistics
4. **Backup Strategy**: Include CSV exports with your video backups
5. **CSV Compatibility**: The RFC 4180-compliant output works with all major spreadsheet applications

## Technical Details

### CSV Writing Configuration

The CSV writer uses Python's standard `csv` module with these settings:
- **Quoting**: `QUOTE_MINIMAL` - only quotes fields when necessary
- **Quote Character**: Standard double quotes (`"`)
- **Escape Method**: Double-quote escaping (RFC 4180 compliant)
- **Encoding**: UTF-8 with full Unicode support
- **Line Terminator**: Platform-appropriate (CRLF on Windows, LF on Unix)

This ensures maximum compatibility with spreadsheet applications like Excel, Google Sheets, and LibreOffice Calc.