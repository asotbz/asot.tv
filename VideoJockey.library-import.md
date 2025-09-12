# Video Jockey - Existing Library Management Extension

## Overview
This document extends the Video Jockey PRD to include comprehensive support for managing existing music video libraries and source verification features.

## 1. Existing Library Management

### 1.1 Library Scanning & Import

#### Directory Scanner
**Functionality:**
- Recursive directory scanning with progress indication
- Support for multiple video formats: MP4, MKV, AVI, WEBM, MOV, FLV
- Configurable file size filters (min/max)
- Ignore patterns for excluding directories/files
- Resume capability for interrupted scans

**File Analysis:**
- Extract metadata from files using ffprobe
- Parse filenames for artist/title hints using patterns:
  - `{artist} - {title}.mp4`
  - `{artist}/{title}.mp4`
  - `{title} by {artist}.mp4`
- Read existing NFO files if present
- Calculate video fingerprints for duplicate detection
- Extract video quality/resolution information

#### Import Workflow
```
1. Select directories to scan
2. Configure import settings (naming patterns, matching rules)
3. Start scan → Progress display
4. Review detected videos
5. Auto-match to IMVDb (with confidence scores)
6. Manual review/correction for low-confidence matches
7. Apply metadata and organize files
8. Generate missing NFO files
```

### 1.2 Metadata Matching Engine

#### Automatic Matching
**Strategies:**
1. **Exact Match**: Artist + Title to IMVDb
2. **Fuzzy Match**: Levenshtein distance with threshold
3. **YouTube ID**: Extract from filename/NFO, match to IMVDb
4. **Audio Fingerprinting**: AcoustID or similar for content matching
5. **Visual Fingerprinting**: Frame sampling for video identification

**Confidence Scoring:**
```python
confidence_levels = {
    "exact": 100,      # Perfect artist + title match
    "high": 80-99,     # Fuzzy match with minor differences
    "medium": 60-79,   # Partial matches, year differences
    "low": 40-59,      # Significant differences, manual review needed
    "none": 0-39       # No reliable match found
}
```

#### Manual Matching Interface
- Side-by-side comparison view
- Video preview player
- IMVDb search within matching dialog
- Bulk actions for similar videos
- "Not a music video" classification option

### 1.3 File Organization Options

#### Non-Destructive Mode
- Create symbolic links in organized structure
- Preserve original file locations
- Maintain source directory watching
- Virtual library view without moving files

#### Migration Mode
- Move files to Video Jockey structure
- Preserve original timestamps
- Create backup manifest of original locations
- Rollback capability within 30 days

#### Hybrid Mode
- Copy to organized structure
- Mark originals for later deletion
- Verify successful copy before cleanup
- Maintain reference to original location

### 1.4 Duplicate Management

#### Detection Methods
- File hash comparison (MD5/SHA256)
- Video fingerprinting
- Metadata similarity scoring
- Resolution/quality comparison

#### Resolution Strategies
- Keep highest quality version
- Prefer specific formats (MP4 > MKV > AVI)
- Manual selection interface
- Merge metadata from duplicates

## 2. Source Verification & UI Indicators

### 2.1 Source Tracking Architecture

#### Extended Video Model
```sql
ALTER TABLE videos ADD COLUMN actual_source TEXT;
ALTER TABLE videos ADD COLUMN source_verified BOOLEAN DEFAULT 0;
ALTER TABLE videos ADD COLUMN source_mismatch_type TEXT;
-- mismatch_type: 'different_url', 'different_platform', 'unofficial', 'not_found'

CREATE TABLE source_verifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id INTEGER REFERENCES videos(id),
    imvdb_source TEXT,
    actual_source TEXT,
    platform TEXT, -- 'youtube', 'vimeo', 'dailymotion', etc.
    is_official BOOLEAN,
    channel_name TEXT,
    channel_verified BOOLEAN,
    verification_date TIMESTAMP,
    confidence_score INTEGER
);
```

### 2.2 UI/UX Source Indicators

#### Visual Indicators System

**Icon Legend:**
- ✅ **Verified Match**: Source matches IMVDb exactly
- ⚠️ **Different Source**: Downloaded from alternate source
- 🔄 **Platform Mismatch**: Different platform than IMVDb indicates
- ❌ **Unofficial Source**: Non-VEVO/non-official channel
- ❓ **Unverified**: Source not yet verified
- 🚫 **Source Unavailable**: IMVDb source no longer accessible

**Color Coding:**
```css
.source-verified { 
    border-left: 4px solid #28a745;  /* Green */
}
.source-mismatch { 
    border-left: 4px solid #ffc107;  /* Amber */
}
.source-unofficial { 
    border-left: 4px solid #dc3545;  /* Red */
}
.source-unknown { 
    border-left: 4px solid #6c757d;  /* Gray */
}
```

#### Library View Enhancements
```
┌─────────────────────────────────────────┐
│ [Thumbnail]                             │
│ Artist - Title                          │
│ ⚠️ Different Source | YouTube (Official)│
│ IMVDb: Vimeo | Actual: YouTube         │
└─────────────────────────────────────────┘
```

#### Video Details Page
```
Source Information Panel:
┌──────────────────────────────────────────┐
│ Source Verification Status               │
├──────────────────────────────────────────┤
│ IMVDb Listed Source:                     │
│   Platform: Vimeo                        │
│   URL: vimeo.com/123456                  │
│   Status: ❌ No longer available         │
│                                          │
│ Actual Download Source:                  │
│   Platform: YouTube                      │
│   Channel: ArtistVEVO ✓                  │
│   URL: youtube.com/watch?v=abc123        │
│   Status: ✅ Verified Official           │
│                                          │
│ [🔄 Re-verify] [📥 Find Better Source]   │
└──────────────────────────────────────────┘
```

### 2.3 Source Verification Features

#### Automatic Verification
- Periodic source availability checks
- Channel verification (VEVO, official artist channels)
- Video quality comparison with IMVDb listing
- Copyright claim detection

#### Manual Tools
- "Find Better Source" search function
- Source replacement workflow
- Report incorrect IMVDb information
- Community source suggestions

#### Filtering & Sorting
- Filter by source verification status
- Sort by source confidence
- Bulk verify sources action
- Export source discrepancy report

## 3. Database Schema Updates

### 3.1 Library Import Tables

```sql
CREATE TABLE import_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    status TEXT,
    total_files INTEGER,
    matched_files INTEGER,
    imported_files INTEGER,
    error_count INTEGER,
    settings_json TEXT
);

CREATE TABLE import_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER REFERENCES import_sessions(id),
    file_path TEXT,
    file_size BIGINT,
    file_hash TEXT,
    detected_artist TEXT,
    detected_title TEXT,
    match_confidence INTEGER,
    matched_video_id INTEGER REFERENCES videos(id),
    status TEXT,
    error_message TEXT
);

CREATE TABLE watched_folders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    folder_path TEXT,
    scan_interval_minutes INTEGER DEFAULT 60,
    auto_import BOOLEAN DEFAULT 0,
    last_scan TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
);
```

## 4. API Endpoints Additions

### Library Import Endpoints
- `POST /api/library/scan` - Initiate directory scan
- `GET /api/library/scan/{session_id}` - Get scan progress
- `POST /api/library/import` - Import scanned videos
- `GET /api/library/import/preview` - Preview import changes
- `POST /api/library/match/{file_id}` - Manual video matching
- `GET /api/library/duplicates` - Find duplicate videos
- `POST /api/library/organize` - Reorganize existing files

### Source Verification Endpoints
- `GET /api/videos/{id}/verify-source` - Verify video source
- `POST /api/videos/{id}/update-source` - Update video source
- `GET /api/videos/source-discrepancies` - List all mismatches
- `POST /api/videos/bulk-verify` - Verify multiple sources
- `GET /api/sources/alternatives/{video_id}` - Find alternative sources

## 5. UI Wireframe Additions

### Library Import Wizard

#### Step 1: Directory Selection
```
┌────────────────────────────────────────────────────┐
│ Import Existing Library                            │
├────────────────────────────────────────────────────┤
│                                                    │
│ Select Directories to Scan:                       │
│ ┌────────────────────────────────────────────┐   │
│ │ 📁 /media/music_videos/        [Remove]     │   │
│ │ 📁 /downloads/videos/          [Remove]     │   │
│ └────────────────────────────────────────────┘   │
│                                                    │
│ [+ Add Directory]                                  │
│                                                    │
│ Options:                                          │
│ ☑ Include subdirectories                          │
│ ☑ Skip files under 10MB                          │
│ ☐ Import NFO metadata if present                  │
│                                                    │
│ Filename Pattern:                                 │
│ [Artist - Title_____________] [Test Pattern]      │
│                                                    │
│                          [Cancel] [Start Scan →]  │
└────────────────────────────────────────────────────┘
```

#### Step 2: Scan Progress
```
┌────────────────────────────────────────────────────┐
│ Scanning Files...                                  │
├────────────────────────────────────────────────────┤
│                                                    │
│ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░  72%                   │
│                                                    │
│ Found: 1,247 video files                          │
│ Processed: 897 / 1,247                            │
│ Matched: 742 (83%)                                │
│ Duplicates: 23                                    │
│                                                    │
│ Current: Parsing "Queen - Bohemian Rhapsody.mp4"  │
│                                                    │
│ Recent Matches:                                    │
│ ✅ The Beatles - Hey Jude (98% confidence)        │
│ ⚠️ Led Zeppelin - Stairway to Heaven (67%)       │
│ ❌ Unknown - video_123.mp4 (No match)             │
│                                                    │
│                              [Pause] [Cancel]     │
└────────────────────────────────────────────────────┘
```

#### Step 3: Review & Match
```
┌────────────────────────────────────────────────────┐
│ Review Import Results                              │
├────────────────────────────────────────────────────┤
│ Filters: [All ▼] [Unmatched ▼] [Low Confidence ▼]│
├────────────────────────────────────────────────────┤
│ ┌──────────────────────────────────────────────┐ │
│ │ 📹 video_123.mp4                              │ │
│ │ Detected: Unknown Artist - Unknown Title      │ │
│ │ Confidence: 0% - No match found               │ │
│ │                                               │ │
│ │ [🔍 Search IMVDb] [⏭️ Skip] [🗑️ Ignore]      │ │
│ └──────────────────────────────────────────────┘ │
│                                                    │
│ ┌──────────────────────────────────────────────┐ │
│ │ 📹 Beatles-HeyJude.mp4                        │ │
│ │ Matched: The Beatles - Hey Jude               │ │
│ │ Confidence: 98% - Exact match                 │ │
│ │ ⚠️ Different source than IMVDb listing        │ │
│ │                                               │ │
│ │ [✅ Confirm] [🔍 Different Match] [⏭️ Skip]   │ │
│ └──────────────────────────────────────────────┘ │
│                                                    │
│           [← Back] [Skip All] [Import Selected →] │
└────────────────────────────────────────────────────┘
```

### Source Verification Badge Component

```typescript
interface SourceBadgeProps {
    video: Video;
    size: 'small' | 'medium' | 'large';
    showDetails: boolean;
}

// Rendered output examples:
<SourceBadge video={video} size="small" />
// → ⚠️ Alt Source

<SourceBadge video={video} size="medium" showDetails={true} />
// → ⚠️ Different Source: YouTube instead of Vimeo

<SourceBadge video={video} size="large" showDetails={true} />
// → ⚠️ Source Mismatch
//   Expected: vimeo.com/123456
//   Actual: youtube.com/watch?v=abc123
//   [Verify Now]
```

## 6. Implementation Priorities

### Phase 1: Core Import (Sprint 3-4)
1. Basic directory scanning
2. Simple filename parsing
3. Manual matching interface
4. NFO reading support

### Phase 2: Advanced Matching (Sprint 5-6)
1. IMVDb auto-matching
2. Confidence scoring
3. Duplicate detection
4. Bulk operations

### Phase 3: Source Verification (Sprint 7-8)
1. Source comparison logic
2. UI indicators
3. Verification workflows
4. Reporting tools

### Phase 4: Optimization (Post-Launch)
1. Audio/video fingerprinting
2. Machine learning matching
3. Community database
4. Advanced organization options

## 7. Success Metrics

### Import Performance
- Scan speed: >100 files/second
- Auto-match rate: >80% for well-named files
- Import completion: <5 minutes for 1000 files

### User Satisfaction
- Successful library migrations: >90%
- Manual matching required: <20% of files
- Source verification accuracy: >95%

### System Impact
- Database growth: <100KB per 1000 videos
- CPU usage during scan: <50%
- Memory usage: <500MB for large imports