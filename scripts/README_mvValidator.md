# mvValidator - Music Video Directory Structure Validator

A modular and extensible validation tool for music video directory structures. Detects common issues and ensures consistency in your music video collection organization.

## Overview

`mvValidator.py` recursively scans a directory tree and validates the structure against a set of configurable rules. It's designed to be easily extended with new validation rules to meet specific requirements.

## Features

### Core Validation Rules

1. **Orphan NFO Files**: Detects NFO metadata files without corresponding MP4 video files
2. **Orphan Video Files**: Detects MP4 video files without corresponding NFO metadata
3. **Missing Artist NFO**: Identifies artist directories that lack an artist.nfo file
4. **Unexpected Files**: Finds files that aren't MP4 videos or NFO metadata files
5. **Empty Directories**: Locates directories that contain no files
6. **Duplicate Videos** (optional): Detects potential duplicate videos based on filename similarity

### Key Features

- **Modular Architecture**: Easy to add, remove, or modify validation rules
- **Color-Coded Output**: Clear visual feedback in terminal
- **Report Export**: Save validation results to text file
- **Configurable Rules**: Enable/disable specific checks via command line
- **Exit Codes**: Returns non-zero exit code when issues found (useful for CI/CD)

## Usage

### Basic Validation
```bash
python3 mvValidator.py /path/to/music/videos
```

### Verbose Output
```bash
python3 mvValidator.py /path/to/music/videos --verbose
```

### Export Report
```bash
python3 mvValidator.py /path/to/music/videos --export-report validation_report.txt
```

### Check for Duplicates
```bash
python3 mvValidator.py /path/to/music/videos --check-duplicates
```

### Skip Empty Directory Check
```bash
python3 mvValidator.py /path/to/music/videos --no-empty-check
```

## Command Line Options

- `directory` (required): Parent directory to validate
- `-v, --verbose`: Show detailed output with more examples
- `-e, --export-report FILE`: Export results to a text file
- `-d, --check-duplicates`: Enable duplicate video detection
- `--no-empty-check`: Skip empty directory validation

## Example Output

```
Scanning directory: /media/MusicVideos

Scan Summary:
  Video files (.mp4): 523
  NFO files: 518
  Artist NFO files: 42
  Other files: 7
  Artist directories: 45

Running validation rules...

Validation Report
======================================================================

Found 12 total issue(s)

Orphan NFO Files: 2 issue(s)
  1. NFO without video: duran_duran/reflex.nfo
  2. NFO without video: queen/bohemian_rhapsody_live.nfo

Orphan Video Files: 3 issue(s)
  1. Video without NFO: michael_jackson/bad_extended.mp4
  2. Video without NFO: prince/purple_rain_live.mp4
  3. Video without NFO: madonna/vogue_remix.mp4

Missing Artist NFO: 3 issue(s)
  1. Artist directory without artist.nfo: depeche_mode
  2. Artist directory without artist.nfo: new_order
  3. Artist directory without artist.nfo: the_cure

Unexpected Files: 4 issue(s)
  1. Unexpected file (.jpg): duran_duran/album_cover.jpg
  2. Unexpected file (.txt): readme.txt
  3. Unexpected file (.DS_Store): .DS_Store
  ... and 1 more .jpg files

======================================================================

Summary by Rule:
  Orphan NFO Files: ✗ FAIL (2)
  Orphan Video Files: ✗ FAIL (3)
  Missing Artist NFO: ✗ FAIL (3)
  Unexpected Files: ✗ FAIL (4)
  Empty Directories: ✓ PASS
```

## Extending the Validator

The validator uses a modular architecture that makes it easy to add custom validation rules.

### Creating a Custom Rule

Create a new class that inherits from `ValidationRule`:

```python
from mvValidator import ValidationRule

class CustomFilenameRule(ValidationRule):
    """Check that all video files follow naming convention."""
    
    def get_name(self) -> str:
        return "Filename Convention"
    
    def get_description(self) -> str:
        return "Check that video files follow artist_title.mp4 convention"
    
    def validate(self, file_system) -> List[str]:
        issues = []
        
        for video_path in file_system.video_files:
            filename = video_path.stem
            # Check if filename contains underscore
            if '_' not in filename:
                relative_path = video_path.relative_to(file_system.base_path)
                issues.append(f"Non-standard filename: {relative_path}")
        
        return issues
```

### Adding a Rule to the Validator

```python
from mvValidator import MusicVideoValidator
from custom_rules import CustomFilenameRule

validator = MusicVideoValidator("/path/to/videos")
validator.add_rule(CustomFilenameRule())
results = validator.validate()
```

## Integration with mvOrganizer Workflow

This tool complements the other scripts in the mvOrganizer suite:

### Complete Workflow Example

```bash
# 1. Download and organize videos
python3 mvOrganizer.py music_videos.csv /media/MusicVideos

# 2. Validate directory structure
python3 mvValidator.py /media/MusicVideos

# 3. Fix any issues found, then clean NFO files
python3 mvNfoSourceCleaner.py /media/MusicVideos

# 4. Check for duplicates
python3 mvDuplicateFinder.py /media/MusicVideos

# 5. Export collection to CSV
python3 mvNfoExporter.py /media/MusicVideos -o collection.csv

# 6. Final validation
python3 mvValidator.py /media/MusicVideos --export-report final_validation.txt
```

## Use Cases

### Quality Assurance
- Run after batch downloads to ensure completeness
- Verify metadata presence before backup
- Check structure before importing to media server

### Maintenance
- Regular health checks of collection
- Find orphaned files after manual deletions
- Identify incomplete downloads

### Migration
- Validate structure before/after moving collections
- Ensure integrity during server migrations
- Verify cloud sync completeness

## File System Snapshot

The validator creates a snapshot of the file system that categorizes all files:

- **video_files**: All .mp4 files found
- **nfo_files**: All .nfo files (except artist.nfo)
- **artist_nfo_files**: All artist.nfo files
- **artist_directories**: Direct subdirectories of the base path
- **other_files**: Any files that don't match above categories

This snapshot is passed to each validation rule, providing a consistent view of the file system.

## Validation Rules Reference

### OrphanNfoRule
- **Purpose**: Find NFO files without matching video files
- **Common Causes**: Failed downloads, manual video deletion
- **Fix**: Delete orphan NFO or re-download video

### OrphanVideoRule
- **Purpose**: Find video files without NFO metadata
- **Common Causes**: Manual video additions, metadata generation failure
- **Fix**: Generate NFO using mvOrganizer or manually create

### MissingArtistNfoRule
- **Purpose**: Find artist directories without artist.nfo
- **Common Causes**: New artist additions, incomplete organization
- **Fix**: Run mvOrganizer with artist NFO generation enabled

### UnexpectedFilesRule
- **Purpose**: Identify non-standard files in collection
- **Common Causes**: Temporary files, thumbnails, documentation
- **Fix**: Move or delete unnecessary files

### EmptyDirectoriesRule
- **Purpose**: Find directories with no files
- **Common Causes**: Failed downloads, manual cleanup
- **Fix**: Remove empty directories or populate with content

### DuplicateVideosRule (Optional)
- **Purpose**: Detect potential duplicate videos
- **Common Causes**: Multiple downloads, different versions
- **Fix**: Use mvDuplicateFinder for detailed analysis

## Exit Codes

- **0**: No issues found
- **1**: Issues detected

This allows integration with shell scripts and CI/CD pipelines:

```bash
#!/bin/bash
if python3 mvValidator.py /media/MusicVideos; then
    echo "Validation passed!"
else
    echo "Validation failed - check report for details"
    exit 1
fi
```

## Tips

1. **Regular Validation**: Run weekly/monthly to maintain collection health
2. **Post-Download Check**: Always validate after batch downloads
3. **Pre-Backup Validation**: Ensure structure integrity before backups
4. **Custom Rules**: Create rules for your specific naming conventions
5. **Report Archives**: Keep validation reports for audit trail