# mvTagManager - Bulk Tag Management for Music Video NFO Files

A specialized tool for adding or removing tags from music video NFO files based on artist lists. Designed to work with the directory structure created by mvOrganizer.py.

## Overview

`mvTagManager.py` allows bulk tag operations on NFO files for specific artists. You provide a list of artist names in a text file, and the script will add or remove a specified tag from all video NFO files under each artist's directory.

## Features

- **Bulk Tag Operations**: Add or remove tags across multiple artists and videos
- **Artist List Input**: Process artists from a simple text file
- **Smart Name Matching**: Uses same normalization as mvOrganizer.py for directory lookup
- **Duplicate Prevention**: Won't add tags that already exist
- **Safe Operations**: Logs when tags aren't present for removal
- **Detailed Statistics**: Comprehensive summary of operations performed
- **XML Preservation**: Maintains proper XML structure and formatting

## Usage

### Basic Command Structure
```bash
python3 mvTagManager.py <directory> <artists_file> --add|--remove <tag> [options]
```

### Adding Tags

Add a tag to all videos for specified artists:
```bash
python3 mvTagManager.py /media/MusicVideos artists.txt --add "80s"
```

Add tag with verbose output:
```bash
python3 mvTagManager.py /media/MusicVideos artists.txt --add "featured" --verbose
```

### Removing Tags

Remove a tag from all videos for specified artists:
```bash
python3 mvTagManager.py /media/MusicVideos artists.txt --remove "draft"
```

Remove tag with detailed output:
```bash
python3 mvTagManager.py /media/MusicVideos artists.txt --remove "old" -v
```

## Command Line Options

### Required Arguments
- `directory`: Parent directory containing artist subdirectories
- `artists_file`: File containing artist names (one per line)

### Action Arguments (mutually exclusive)
- `--add TAG`: Tag to add to NFO files
- `--remove TAG`: Tag to remove from NFO files

### Optional Arguments
- `-v, --verbose`: Show detailed output for each file processed

## Artists File Format

The artists file should contain one artist name per line. The script supports:
- Comment lines (starting with #)
- Empty lines (ignored)
- Original artist names (not normalized)

### Example artists.txt
```
# 80s Artists
Duran Duran
Depeche Mode
The Cure
A-ha
Tears for Fears

# 90s Artists  
Nirvana
Pearl Jam
Soundgarden

# Electronic
The Chemical Brothers
Fatboy Slim
```

## Directory Structure Expected

The script expects the standard mvOrganizer directory structure:
```
/media/MusicVideos/
├── duran_duran/
│   ├── hungry_like_the_wolf/
│   │   ├── hungry_like_the_wolf.mp4
│   │   └── hungry_like_the_wolf.nfo
│   ├── rio/
│   │   ├── rio.mp4
│   │   └── rio.nfo
│   └── artist.nfo
├── depeche_mode/
│   ├── enjoy_the_silence/
│   │   ├── enjoy_the_silence.mp4
│   │   └── enjoy_the_silence.nfo
│   └── artist.nfo
```

## Name Normalization

The script uses the same normalization rules as mvOrganizer.py to find artist directories:
- Convert to lowercase
- Remove special characters (including hyphens)
- Normalize diacritics (ä → a, é → e)
- Replace spaces with underscores

### Examples:
- "Guns N' Roses" → "guns_n_roses"
- "A-ha" → "aha"  
- "Björk" → "bjork"
- "The Cure" → "the_cure"

## Tag Management Behavior

### Adding Tags
- Checks if tag already exists before adding
- Creates new `<tag>` element in XML
- Preserves existing tags
- Maintains XML formatting

### Removing Tags
- Only removes exact matches
- Preserves other tags
- Handles multiple occurrences
- Safe when tag doesn't exist

### NFO File Structure
```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<musicvideo>
    <title>Video Title</title>
    <artist>Artist Name</artist>
    <tag>80s</tag>
    <tag>classic</tag>
    <tag>featured</tag>
    <!-- other elements -->
</musicvideo>
```

## Example Workflows

### Categorizing by Era

Create era-specific artist lists:
```bash
# Create artist lists
echo "Duran Duran
Depeche Mode
The Cure" > 80s_artists.txt

echo "Nirvana
Pearl Jam
Soundgarden" > 90s_artists.txt

# Add era tags
python3 mvTagManager.py /media/MusicVideos 80s_artists.txt --add "80s"
python3 mvTagManager.py /media/MusicVideos 90s_artists.txt --add "90s"
```

### Marking Featured Content

Mark videos from specific artists as featured:
```bash
# Create featured artists list
echo "Queen
Michael Jackson
Prince
Madonna" > featured_artists.txt

# Add featured tag
python3 mvTagManager.py /media/MusicVideos featured_artists.txt --add "featured"
```

### Cleanup Operations

Remove temporary or outdated tags:
```bash
# Remove draft tags after review
python3 mvTagManager.py /media/MusicVideos reviewed_artists.txt --remove "draft"

# Remove old categorization
python3 mvTagManager.py /media/MusicVideos all_artists.txt --remove "uncategorized"
```

## Output Examples

### Standard Output
```
Adding tag '80s' for 5 artist(s)
Base directory: /media/MusicVideos

Processing: Duran Duran
  ✓ Modified 12 file(s)
Processing: Depeche Mode
  ✓ Modified 8 file(s)
Processing: The Cure
  ⚠ Artist directory not found for: The Cure
Processing: A-ha
  ✓ Modified 4 file(s)
Processing: Tears for Fears
  ✓ Modified 6 file(s)

======================================================================
Summary
======================================================================
Artists processed: 5
NFO files found: 30
NFO files modified: 30
Tags added: 30
Already present: 0
======================================================================
```

### Verbose Output
```
Adding tag 'featured' for 2 artist(s)
Base directory: /media/MusicVideos

Processing: Queen
  Found 15 NFO file(s) in /media/MusicVideos/queen
    ✓ queen/bohemian_rhapsody/bohemian_rhapsody.nfo: Added tag 'featured'
    ✓ queen/we_will_rock_you/we_will_rock_you.nfo: Added tag 'featured'
    ○ queen/radio_ga_ga/radio_ga_ga.nfo: Tag 'featured' already present
    ...
  ✓ Modified 14 file(s)
```

## Integration with Other Scripts

### Complete Tagging Workflow

```bash
# 1. Download and organize videos
python3 mvOrganizer.py music_videos.csv /media/MusicVideos

# 2. Validate structure
python3 mvValidator.py /media/MusicVideos

# 3. Add genre tags
python3 mvTagManager.py /media/MusicVideos rock_artists.txt --add "rock"
python3 mvTagManager.py /media/MusicVideos pop_artists.txt --add "pop"

# 4. Add era tags
python3 mvTagManager.py /media/MusicVideos 80s_artists.txt --add "80s"
python3 mvTagManager.py /media/MusicVideos 90s_artists.txt --add "90s"

# 5. Export tagged collection
python3 mvNfoExporter.py /media/MusicVideos -o collection.csv
```

### Selective Processing

Use tag manager with validation to process specific subsets:
```bash
# Find artists missing tags
python3 mvValidator.py /media/MusicVideos > validation.txt

# Extract artist names needing tags
grep "Artist directory" validation.txt | cut -d: -f2 > need_tags.txt

# Add default tag to those artists
python3 mvTagManager.py /media/MusicVideos need_tags.txt --add "untagged"
```

## Error Handling

### Common Issues and Solutions

1. **Artist directory not found**
   - Cause: Artist name doesn't match normalized directory name
   - Solution: Check directory name follows normalization rules
   - Use verbose mode to see expected path

2. **No NFO files found**
   - Cause: Artist directory exists but contains no video NFO files
   - Solution: Run mvOrganizer to generate NFO files

3. **XML parse error**
   - Cause: Corrupted or invalid NFO file
   - Solution: Use mvNfoSourceCleaner.py to fix NFO files

4. **Permission denied**
   - Cause: Insufficient permissions to modify NFO files
   - Solution: Check file permissions or run with appropriate privileges

## Statistics Tracking

The script tracks and reports:
- **Artists processed**: Total number of artists from list
- **NFO files found**: Total video NFO files discovered
- **NFO files modified**: Files actually changed
- **Tags added/removed**: Successful tag operations
- **Already present**: Tags that already existed (for add)
- **Not present**: Tags that didn't exist (for remove)
- **Errors**: Any processing errors encountered

## Best Practices

1. **Backup First**: Always backup NFO files before bulk operations
2. **Test Small**: Test with a small artist list first
3. **Use Verbose Mode**: Enable verbose for initial runs to understand changes
4. **Organize Artist Lists**: Keep themed artist lists for easy tag management
5. **Document Tags**: Maintain a list of tags and their meanings
6. **Regular Cleanup**: Periodically review and remove obsolete tags

## Tag Naming Conventions

Recommended tag categories:
- **Era**: 70s, 80s, 90s, 2000s, 2010s
- **Genre**: rock, pop, metal, electronic, hip-hop
- **Quality**: hd, 4k, remastered, live
- **Status**: featured, favorite, new, archived
- **Source**: official, fanmade, concert
- **Special**: award-winner, chart-topper, classic

## Tips

1. **Batch Operations**: Process multiple tag operations in sequence
2. **Script Integration**: Combine with shell scripts for complex workflows
3. **Regular Maintenance**: Schedule periodic tag reviews
4. **Version Control**: Track artist lists in version control
5. **Validation**: Run mvValidator.py after tag operations to ensure consistency

## Exit Codes

- **0**: Successful operation
- **1**: Error occurred (missing files, parse errors, etc.)

This enables scripting:
```bash
#!/bin/bash
if python3 mvTagManager.py /media/MusicVideos artists.txt --add "processed"; then
    echo "Tags added successfully"
    # Continue with next step
else
    echo "Tag operation failed"
    exit 1
fi