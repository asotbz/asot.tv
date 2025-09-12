# Video Jockey - UI/UX Design Document

## Design Philosophy

### Core Principles
- **Clarity First**: Every interface element should have a clear purpose
- **Progressive Disclosure**: Show essential information first, details on demand
- **Visual Hierarchy**: Use size, color, and spacing to guide user attention
- **Responsive Design**: Adapt seamlessly from mobile to desktop
- **Accessibility**: WCAG 2.1 AA compliance

### Visual Language
- **Modern & Clean**: Minimalist design with purposeful use of space
- **Media-Focused**: Large thumbnails and visual previews
- **Dark Mode First**: Optimized for extended viewing sessions
- **Smooth Animations**: Subtle transitions that enhance UX

## Color Palette

### Primary Colors
```
Brand Primary:    #6366F1  (Indigo-500)    - Primary actions, links
Brand Secondary:  #8B5CF6  (Purple-500)    - Accents, highlights
Success:          #10B981  (Emerald-500)   - Success states, completed
Warning:          #F59E0B  (Amber-500)     - Warnings, pending
Error:            #EF4444  (Red-500)       - Errors, failures
Info:             #3B82F6  (Blue-500)      - Information, tips
```

### Neutral Colors (Dark Theme)
```
Background:       #0F0F0F  - Main background
Surface:          #1A1A1A  - Cards, panels
Surface Raised:   #262626  - Elevated elements
Border:           #404040  - Dividers, borders
Text Primary:     #F5F5F5  - Main text
Text Secondary:   #A1A1A1  - Secondary text
Text Disabled:    #666666  - Disabled state
```

### Neutral Colors (Light Theme)
```
Background:       #FFFFFF  - Main background
Surface:          #F9FAFB  - Cards, panels
Surface Raised:   #FFFFFF  - Elevated elements
Border:           #E5E7EB  - Dividers, borders
Text Primary:     #111827  - Main text
Text Secondary:   #6B7280  - Secondary text
Text Disabled:    #9CA3AF  - Disabled state
```

## Typography

```
Font Family:      Inter, system-ui, -apple-system, sans-serif
Heading 1:        32px / 40px / 700 (2rem / 2.5rem / bold)
Heading 2:        24px / 32px / 600 (1.5rem / 2rem / semibold)
Heading 3:        20px / 28px / 600 (1.25rem / 1.75rem / semibold)
Body Large:       16px / 24px / 400 (1rem / 1.5rem / normal)
Body:             14px / 20px / 400 (0.875rem / 1.25rem / normal)
Caption:          12px / 16px / 400 (0.75rem / 1rem / normal)
Button:           14px / 20px / 500 (0.875rem / 1.25rem / medium)
```

## Component Specifications

### Navigation Bar
```
Height:           64px
Background:       Surface color with backdrop blur
Logo:             24px height
Nav Items:        14px medium weight, 16px spacing
User Avatar:      32px diameter
Shadow:           0 1px 3px rgba(0,0,0,0.1)
```

### Cards
```
Border Radius:    12px
Padding:          16px (compact) / 24px (standard)
Shadow:           0 1px 3px rgba(0,0,0,0.12)
Hover Shadow:     0 4px 6px rgba(0,0,0,0.15)
Transition:       all 200ms ease
```

### Buttons
```
Height:           32px (small) / 40px (medium) / 48px (large)
Padding:          8px 16px (small) / 12px 24px (medium) / 16px 32px (large)
Border Radius:    6px (small) / 8px (medium) / 10px (large)
Font Size:        13px (small) / 14px (medium) / 16px (large)
```

### Form Inputs
```
Height:           40px (standard) / 48px (large)
Padding:          12px
Border:           1px solid Border color
Border Radius:    8px
Focus Ring:       2px Primary color with 4px offset
Label:            12px, Text Secondary color
Helper Text:      12px, Text Secondary color
Error Text:       12px, Error color
```

### Data Tables
```
Row Height:       48px (compact) / 56px (standard) / 64px (comfortable)
Header Height:    48px
Header Font:      12px uppercase, 600 weight
Cell Padding:     16px horizontal
Border:           1px solid Border color (bottom only)
Hover Background: Surface Raised color
```

---

## Screen Wireframes

## 1. Login Screen

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│                                                                     │
│                          [Video Jockey Logo]                       │
│                                                                     │
│                    ┌─────────────────────────────┐                │
│                    │                             │                 │
│                    │  Welcome Back               │                 │
│                    │  Sign in to your account    │                 │
│                    │                             │                 │
│                    │  Email                      │                 │
│                    │  ┌─────────────────────┐   │                 │
│                    │  │ user@example.com    │   │                 │
│                    │  └─────────────────────┘   │                 │
│                    │                             │                 │
│                    │  Password                   │                 │
│                    │  ┌─────────────────────┐   │                 │
│                    │  │ ••••••••            │   │                 │
│                    │  └─────────────────────┘   │                 │
│                    │                             │                 │
│                    │  □ Remember me              │                 │
│                    │                             │                 │
│                    │  ┌─────────────────────┐   │                 │
│                    │  │     Sign In         │   │                 │
│                    │  └─────────────────────┘   │                 │
│                    │                             │                 │
│                    │  Forgot password?           │                 │
│                    │                             │                 │
│                    │  ─────────────────────────  │                 │
│                    │                             │                 │
│                    │  New to Video Jockey?       │                 │
│                    │  Create an account          │                 │
│                    │                             │                 │
│                    └─────────────────────────────┘                │
│                                                                     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Design Notes:**
- Centered card layout (400px wide)
- Logo at top (120px height)
- Form fields with floating labels
- Primary button for Sign In
- Links for password reset and registration
- Clean, minimal design focusing on the form

---

## 2. Dashboard

```
┌─────────────────────────────────────────────────────────────────────┐
│ [≡] Video Jockey    [Search...]              [🔔] [Settings] [User] │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Welcome back, John!                                              │
│  Here's what's happening with your music video library            │
│                                                                     │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────┐ │
│  │ Total Videos │ │   Artists    │ │  This Month  │ │  Storage  │ │
│  │              │ │              │ │              │ │           │ │
│  │    1,247     │ │     342      │ │      47      │ │  124 GB   │ │
│  │   +12 today  │ │  +3 today    │ │  downloads   │ │  of 500GB │ │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────┘ │
│                                                                     │
│  Quick Actions                                                     │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐     │
│  │    [+]     │ │    [↓]     │ │    [📁]    │ │    [🔍]    │     │
│  │ Add Video  │ │Import CSV  │ │  Library   │ │   Search   │     │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘     │
│                                                                     │
│  Download Queue (3 active)                            [View All >] │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ ▶ Downloading: The Weeknd - Blinding Lights                 │  │
│  │   [████████████████░░░░░░░░░░] 76% • 2.3 MB/s • 00:45 left │  │
│  ├─────────────────────────────────────────────────────────────┤  │
│  │ ⏸ Paused: Dua Lipa - Levitating                            │  │
│  │   [██████░░░░░░░░░░░░░░░░░░░░] 31% • Paused by user       │  │
│  ├─────────────────────────────────────────────────────────────┤  │
│  │ ⏳ Queued: Olivia Rodrigo - good 4 u                        │  │
│  │   Waiting • Priority: High • Est. start: 2 min             │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  Recent Downloads                                     [View All >] │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ [🎬] BTS - Dynamite                              2 hours ago│  │
│  │      Pop • 2020 • 1080p • 267 MB                            │  │
│  ├─────────────────────────────────────────────────────────────┤  │
│  │ [🎬] Taylor Swift - Anti-Hero                    5 hours ago│  │
│  │      Pop • 2022 • 4K • 423 MB                               │  │
│  ├─────────────────────────────────────────────────────────────┤  │
│  │ [🎬] Post Malone - Circles                       Yesterday  │  │
│  │      Hip Hop/R&B • 2019 • 1080p • 198 MB                    │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  Trending on IMVDb                                    [View All >] │
│  ┌────┬────┬────┬────┬────┐                                       │
│  │[IMG]│[IMG]│[IMG]│[IMG]│[IMG]│                                   │
│  │ #1  │ #2  │ #3  │ #4  │ #5  │                                   │
│  └────┴────┴────┴────┴────┘                                       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Design Notes:**
- Statistics cards with trend indicators
- Quick action buttons with icons
- Live download queue with progress bars
- Recent downloads with metadata
- Trending videos carousel from IMVDb
- Clean card-based layout with consistent spacing

---

## 3. Library View (Grid)

```
┌─────────────────────────────────────────────────────────────────────┐
│ [≡] Video Jockey    [Search library...]      [🔔] [Settings] [User] │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  My Library (1,247 videos)                                        │
│                                                                     │
│  [Filter ▼] [Genre ▼] [Year ▼] [Quality ▼]    [⊞ Grid] [☰ List]  │
│                                                                     │
│  Showing 1-24 of 1,247 results                     Sort: [Recent ▼]│
│                                                                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐│
│  │          │ │          │ │          │ │          │ │          ││
│  │  [VIDEO  │ │  [VIDEO  │ │  [VIDEO  │ │  [VIDEO  │ │  [VIDEO  ││
│  │   THUMB] │ │   THUMB] │ │   THUMB] │ │   THUMB] │ │   THUMB] ││
│  │          │ │          │ │          │ │          │ │          ││
│  │  ● 3:45  │ │  ● 4:12  │ │  ● 3:28  │ │  ● 5:01  │ │  ● 3:33  ││
│  ├──────────┤ ├──────────┤ ├──────────┤ ├──────────┤ ├──────────┤│
│  │The Weeknd│ │Dua Lipa  │ │  BTS     │ │T. Swift  │ │Post Malone││
│  │Blinding  │ │Levitating│ │ Dynamite │ │Anti-Hero │ │ Circles  ││
│  │Lights    │ │          │ │          │ │          │ │          ││
│  │2020•1080p│ │2021•4K   │ │2020•1080p│ │2022•4K   │ │2019•1080p││
│  │[★][↓][⋮]│ │[★][↓][⋮]│ │[★][↓][⋮]│ │[★][↓][⋮]│ │[★][↓][⋮]││
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘│
│                                                                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐│
│  │          │ │          │ │          │ │          │ │          ││
│  │  [VIDEO  │ │  [VIDEO  │ │  [VIDEO  │ │  [VIDEO  │ │  [VIDEO  ││
│  │   THUMB] │ │   THUMB] │ │   THUMB] │ │   THUMB] │ │   THUMB] ││
│  │          │ │          │ │          │ │          │ │          ││
│  │  ● 4:02  │ │  ● 3:51  │ │  ● 3:15  │ │  ● 4:23  │ │  ● 3:47  ││
│  ├──────────┤ ├──────────┤ ├──────────┤ ├──────────┤ ├──────────┤│
│  │Billie E. │ │Ariana G. │ │ Drake    │ │ Rihanna  │ │ Ed Sheeran││
│  │Bad Guy   │ │7 rings   │ │Hotline   │ │Diamonds  │ │Shape of  ││
│  │          │ │          │ │ Bling    │ │          │ │You       ││
│  │2019•1080p│ │2019•4K   │ │2015•720p │ │2012•1080p│ │2017•4K   ││
│  │[★][↓][⋮]│ │[★][↓][⋮]│ │[★][↓][⋮]│ │[★][↓][⋮]│ │[★][↓][⋮]││
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘│
│                                                                     │
│  [Previous] [1] 2 3 4 ... 52 [Next]              [Show 24 ▼] items │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Design Notes:**
- Video thumbnail cards (240px x 180px)
- Duration overlay on thumbnails
- Quick actions on hover (favorite, download, menu)
- Metadata below thumbnail (artist, title, year, quality)
- Filter bar with dropdown selections
- Toggle between grid and list views
- Pagination controls at bottom

---

## 4. Library View (List)

```
┌─────────────────────────────────────────────────────────────────────┐
│ [≡] Video Jockey    [Search library...]      [🔔] [Settings] [User] │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  My Library (1,247 videos)                                        │
│                                                                     │
│  [Filter ▼] [Genre ▼] [Year ▼] [Quality ▼]    [⊞ Grid] [☰ List]  │
│                                                                     │
│  □ Select All                                      Sort: [Recent ▼]│
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────────┐
│  │ □ │ Thumb │ Artist/Title        │ Album    │Year│Genre  │Actions│
│  ├───┼───────┼────────────────────┼──────────┼────┼───────┼───────┤
│  │ □ │ [IMG] │ The Weeknd         │After Hours│2020│Pop    │[↓][⋮]│
│  │   │       │ Blinding Lights    │          │    │       │       │
│  │   │       │ 3:45 • 1080p • 267MB           │    │       │       │
│  ├───┼───────┼────────────────────┼──────────┼────┼───────┼───────┤
│  │ □ │ [IMG] │ Dua Lipa           │Future    │2021│Pop    │[↓][⋮]│
│  │   │       │ Levitating         │Nostalgia │    │       │       │
│  │   │       │ 4:12 • 4K • 512MB              │    │       │       │
│  ├───┼───────┼────────────────────┼──────────┼────┼───────┼───────┤
│  │ □ │ [IMG] │ BTS                │BE        │2020│Pop    │[↓][⋮]│
│  │   │       │ Dynamite           │          │    │       │       │
│  │   │       │ 3:28 • 1080p • 298MB           │    │       │       │
│  ├───┼───────┼────────────────────┼──────────┼────┼───────┼───────┤
│  │ □ │ [IMG] │ Taylor Swift       │Midnights │2022│Pop    │[↓][⋮]│
│  │   │       │ Anti-Hero          │          │    │       │       │
│  │   │       │ 5:01 • 4K • 623MB              │    │       │       │
│  ├───┼───────┼────────────────────┼──────────┼────┼───────┼───────┤
│  │ □ │ [IMG] │ Post Malone        │Hollywood's│2019│Hip Hop│[↓][⋮]│
│  │   │       │ Circles            │Bleeding  │    │/R&B   │       │
│  │   │       │ 3:33 • 1080p • 312MB           │    │       │       │
│  └───┴───────┴────────────────────┴──────────┴────┴───────┴───────┘
│                                                                     │
│  [Previous] [1] 2 3 4 ... 52 [Next]              [Show 25 ▼] items │
│                                                                     │
│  With 3 selected: [Download] [Edit Metadata] [Delete]             │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Design Notes:**
- Compact list with 60px row height
- Small thumbnails (80px x 45px)
- Checkbox selection for bulk operations
- Sortable columns
- Inline metadata display
- Quick action buttons per row
- Bulk action bar appears when items selected

---

## 5. Video Details Page

```
┌─────────────────────────────────────────────────────────────────────┐
│ [≡] Video Jockey    [Search...]              [🔔] [Settings] [User] │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  [← Back to Library]                                              │
│                                                                     │
│  ┌─────────────────────────────────────────────┐                  │
│  │                                               │ The Weeknd      │
│  │                                               │ Blinding Lights │
│  │              [VIDEO PLAYER]                   │                 │
│  │                                               │ [Edit] [Delete] │
│  │                 ▶ 1:23 / 3:45                │ [Download] [⋮]  │
│  │     [▶] [──────────────────] [🔊] [⚙] [⛶]   │                 │
│  └─────────────────────────────────────────────┘                  │
│                                                                     │
│  ┌──────────────────────┬──────────────────────────────────────┐  │
│  │ Metadata             │ Download Information                 │  │
│  ├──────────────────────┼──────────────────────────────────────┤  │
│  │ Artist:              │ Status:        ✓ Downloaded          │  │
│  │ The Weeknd           │ Source:        YouTube               │  │
│  │                      │ Downloaded:    2024-01-15 10:30 AM  │  │
│  │ Title:               │ File Size:     267 MB                │  │
│  │ Blinding Lights      │ Resolution:    1920x1080 (1080p)    │  │
│  │                      │ Format:        MP4 (H.264/AAC)      │  │
│  │ Album:               │ Duration:      3:45                  │  │
│  │ After Hours          │ Bitrate:       10 Mbps               │  │
│  │                      │                                      │  │
│  │ Year: 2020           │ File Location:                       │  │
│  │ Genre: Pop           │ /media/the_weeknd/blinding_lights/  │  │
│  │ Director: Anton Tammi│ blinding_lights.mp4                  │  │
│  │ Label: Republic      │                                      │  │
│  │                      │ [View NFO] [Open Folder]            │  │
│  │ Tags:                │                                      │  │
│  │ [synthwave] [80s]    │                                      │  │
│  │ [official] [4K]      │                                      │  │
│  │                      │                                      │  │
│  │ IMVDb ID: 12345      │                                      │  │
│  │ YouTube ID: 4NRXx6U8│                                      │  │
│  └──────────────────────┴──────────────────────────────────────┘  │
│                                                                     │
│  Description (from IMVDb)                                         │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ "Blinding Lights" is a synth-pop masterpiece that pays    │  │
│  │ homage to 1980s music and aesthetics. The video features  │  │
│  │ The Weeknd in a blood-soaked suit racing through the      │  │
│  │ neon-lit streets of Las Vegas...                          │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  Related Videos                                     [View All >]  │
│  ┌────────┬────────┬────────┬────────┬────────┐                 │
│  │ [IMG]  │ [IMG]  │ [IMG]  │ [IMG]  │ [IMG]  │                 │
│  │Save    │In Your │Can't   │Starboy │Die For │                 │
│  │Your    │Eyes    │Feel My │        │You     │                 │
│  │Tears   │        │Face    │        │        │                 │
│  └────────┴────────┴────────┴────────┴────────┘                 │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Design Notes:**
- Large video player (16:9 aspect ratio)
- Playback controls with scrubber
- Two-column metadata layout
- Editable metadata fields
- Download information panel
- IMVDb description
- Related videos carousel
- Action buttons for edit/delete/download

---

## 6. Search & Discovery

```
┌─────────────────────────────────────────────────────────────────────┐
│ [≡] Video Jockey    [Search IMVDb...]        [🔔] [Settings] [User] │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Search Music Videos                                              │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────┐     │
│  │ 🔍 Search for artist, song, director...                  │     │
│  └──────────────────────────────────────────────────────────┘     │
│                                                                     │
│  [All Sources ▼] [All Genres ▼] [All Years ▼] [All Quality ▼]    │
│                                                                     │
│  Search Results (showing 1-20 of 342 results)                     │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ [THUMB] │ The Weeknd - Blinding Lights                     │  │
│  │  60x45  │ 2020 • Pop • Anton Tammi • 3:45                  │  │
│  │         │ ⚡ Available on YouTube                           │  │
│  │         │ [+ Add to Library] [Add to Queue] [Preview]      │  │
│  ├─────────┼───────────────────────────────────────────────────┤  │
│  │ [THUMB] │ Dua Lipa - Levitating                            │  │
│  │  60x45  │ 2021 • Pop • Warren Fu • 4:12                   │  │
│  │         │ ⚡ Available on YouTube                           │  │
│  │         │ ✓ Already in library                             │  │
│  ├─────────┼───────────────────────────────────────────────────┤  │
│  │ [THUMB] │ BTS - Dynamite                                   │  │
│  │  60x45  │ 2020 • Pop • Yong Seok Choi • 3:28              │  │
│  │         │ ⚡ Available on YouTube & Vimeo                   │  │
│  │         │ [+ Add to Library] [Add to Queue] [Preview]      │  │
│  └─────────┴───────────────────────────────────────────────────┘  │
│                                                                     │
│  Featured Collections                                             │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐   │
│  │              │              │              │              │   │
│  │ [COLLECTION] │ [COLLECTION] │ [COLLECTION] │ [COLLECTION] │   │
│  │              │              │              │              │   │
│  │ Top 100      │ New Releases │ 90s Classics │ Director's   │   │
│  │ This Month   │ This Week    │              │ Spotlight    │   │
│  └──────────────┴──────────────┴──────────────┴──────────────┘   │
│                                                                     │
│  Trending Artists                                                 │
│  [The Weeknd] [Taylor Swift] [BTS] [Dua Lipa] [Drake] [+more]   │
│                                                                     │
│  Popular Directors                                                │
│  [David Fincher] [Spike Jonze] [Michel Gondry] [Hype Williams]   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Design Notes:**
- Large search bar with autocomplete
- Filter dropdowns for refinement
- Search results with inline actions
- Availability indicators
- Library status (already added)
- Featured collections grid
- Trending tags for quick access

---

## 7. Download Queue Management

```
┌─────────────────────────────────────────────────────────────────────┐
│ [≡] Video Jockey    [Search...]              [🔔] [Settings] [User] │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Download Queue                                                   │
│                                                                     │
│  [⏸ Pause All] [▶ Resume All] [🗑 Clear Completed] [⚙ Settings]  │
│                                                                     │
│  Active Downloads (2)                                             │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ ▶ The Weeknd - Blinding Lights                    Priority: ↑│  │
│  │   YouTube • 1080p • 267 MB                                   │  │
│  │   [████████████████░░░░░░░░░░░░░░░░░░] 76%                 │  │
│  │   Speed: 2.3 MB/s • Time left: 00:45 • Downloaded: 203 MB   │  │
│  │   [⏸ Pause] [✖ Cancel]                                      │  │
│  ├─────────────────────────────────────────────────────────────┤  │
│  │ ▶ Dua Lipa - Physical                              Priority: ↔│  │
│  │   YouTube • 4K • 512 MB                                      │  │
│  │   [██████░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 24%                 │  │
│  │   Speed: 1.8 MB/s • Time left: 03:22 • Downloaded: 123 MB   │  │
│  │   [⏸ Pause] [✖ Cancel]                                      │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  Queued (5)                                        [Clear Queue]  │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ ⏳ 1. Olivia Rodrigo - good 4 u                   Priority: ↑│  │
│  │      YouTube • 1080p • Est. 298 MB • Starts in ~4 min       │  │
│  │      [↑ Move Up] [↓ Move Down] [✖ Remove]                  │  │
│  ├─────────────────────────────────────────────────────────────┤  │
│  │ ⏳ 2. BTS - Butter                                Priority: ↔│  │
│  │      YouTube • 4K • Est. 456 MB • Starts in ~7 min          │  │
│  │      [↑ Move Up] [↓ Move Down] [✖ Remove]                  │  │
│  ├─────────────────────────────────────────────────────────────┤  │
│  │ ⏳ 3. Ed Sheeran - Bad Habits                     Priority: ↓│  │
│  │      YouTube • 1080p • Est. 276 MB • Starts in ~10 min      │  │
│  │      [↑ Move Up] [↓ Move Down] [✖ Remove]                  │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  Failed (2)                                        [Retry All]    │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ ✖ Drake - Hotline Bling                                     │  │
│  │   Error: Video unavailable (regional restriction)            │  │
│  │   Failed at: 2024-01-15 09:45 AM                           │  │
│  │   [🔄 Retry] [🔍 Find Alternative] [✖ Remove]              │  │
│  ├─────────────────────────────────────────────────────────────┤  │
│  │ ✖ Rihanna - Umbrella                                        │  │
│  │   Error: Connection timeout                                  │  │
│  │   Failed at: 2024-01-15 08:30 AM • Retries: 2              │  │
│  │   [🔄 Retry] [🔍 Find Alternative] [✖ Remove]              │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  Completed Today (12)                              [View History] │
│  ✓ Taylor Swift - Shake It Off • 4K • 423 MB • 10:15 AM        │
│  ✓ Post Malone - Circles • 1080p • 312 MB • 10:03 AM           │
│  [Show More...]                                                   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Design Notes:**
- Real-time progress bars
- Download speed and time estimates
- Priority indicators (High ↑, Normal ↔, Low ↓)
- Queue reordering controls
- Failed downloads with error details
- Retry and alternative source options
- Completed downloads summary

---

## 8. Settings Page

```
┌─────────────────────────────────────────────────────────────────────┐
│ [≡] Video Jockey    [Search...]              [🔔] [Settings] [User] │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Settings                                                         │
│                                                                     │
│  [Profile] [API Keys] [Downloads] [Library] [Notifications]       │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ Profile Settings                                             │ │
│  ├──────────────────────────────────────────────────────────────┤ │
│  │                                                              │ │
│  │ Display Name                                                 │ │
│  │ ┌──────────────────────────────────────┐                    │ │
│  │ │ John Doe                              │                    │ │
│  │ └──────────────────────────────────────┘                    │ │
│  │                                                              │ │
│  │ Email                                                        │ │
│  │ ┌──────────────────────────────────────┐                    │ │
│  │ │ john.doe@example.com                 │                    │ │
│  │ └──────────────────────────────────────┘                    │ │
│  │                                                              │ │
│  │ Password                                                     │ │
│  │ [Change Password]                                            │ │
│  │                                                              │ │
│  │ Theme                                                        │ │
│  │ ○ Light  ● Dark  ○ Auto                                     │ │
│  │                                                              │ │
│  │ Language                                                     │ │
│  │ [English (US) ▼]                                            │ │
│  │                                                              │ │
│  │ Storage Usage                                                │ │
│  │ [████████████░░░░░░░] 124 GB of 500 GB (24.8%)             │ │
│  │                                                              │ │
│  │ Account Created: January 1, 2023                            │ │
│  │ Last Login: January 15, 2024 10:30 AM                       │ │
│  │                                                              │ │
│  │ [Save Changes] [Cancel]                                      │ │
│  │                                                              │ │
│  │ Danger Zone                                                  │ │
│  │ [Export All Data] [Delete Account]                          │ │
│  │                                                              │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Settings - API Keys Tab:**
```
┌──────────────────────────────────────────────────────────────┐
│ API Keys Configuration                                        │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ IMVDb API Key                                                │
│ ┌──────────────────────────────────────┐ [Test] [Save]      │
│ │ ••••••••••••••••••••••abc123        │                    │
│ └──────────────────────────────────────┘                    │
│ Status: ✓ Active • Last used: 2 hours ago                   │
│ Rate Limit: 892/1000 requests today                         │
│                                                              │
│ YouTube Data API Key                                         │
│ ┌──────────────────────────────────────┐ [Test] [Save]      │
│ │ ••••••••••••••••••••••xyz789        │                    │
│ └──────────────────────────────────────┘                    │
│ Status: ✓ Active • Last used: 1 hour ago                    │
│ Quota: 8,234/10,000 units today                            │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**Settings - Downloads Tab:**
```
┌──────────────────────────────────────────────────────────────┐
│ Download Settings                                             │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ Default Quality                                              │
│ ○ Best Available  ● 1080p  ○ 720p  ○ 480p                  │
│                                                              │
│ Concurrent Downloads                                         │
│ [1] [2] [3] [4] [5]                                         │
│                                                              │
│ Download Speed Limit                                         │
│ ○ No Limit  ● Limited to: [10 ▼] MB/s                      │
│                                                              │
│ Retry Failed Downloads                                       │
│ ☑ Automatically retry failed downloads                       │
│ Maximum retries: [3 ▼]                                      │
│                                                              │
│ Source Preference                                            │
│ 1. YouTube (Official/VEVO channels)                         │
│ 2. YouTube (Artist channels)                                │
│ 3. Vimeo                                                    │
│ 4. Direct URLs                                              │
│ [↑] [↓] Reorder                                            │
│                                                              │
│ Schedule Downloads                                           │
│ ☐ Only download during specific hours                       │
│ From: [10:00 PM ▼] To: [6:00 AM ▼]                        │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**Design Notes:**
- Tabbed interface for settings categories
- Form inputs with labels and help text
- Visual feedback for API status
- Storage usage visualization
- Save/Cancel actions
- Danger zone for destructive actions
- Responsive form layout

---

## 9. Add Video Modal

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Add Music Video                          [✖]  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  How would you like to add videos?                               │
│                                                                     │
│  [Search IMVDb] [Enter Manually] [Import CSV] [Paste URL]         │
│                                                                     │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │ Manual Entry                                               │   │
│  ├────────────────────────────────────────────────────────────┤   │
│  │                                                            │   │
│  │ Artist *                                                   │   │
│  │ ┌────────────────────────────────────────┐                │   │
│  │ │ The Weeknd                             │                │   │
│  │ └────────────────────────────────────────┘                │   │
│  │                                                            │   │
│  │ Title *                                                    │   │
│  │ ┌────────────────────────────────────────┐                │   │
│  │ │ Blinding Lights                         │                │   │
│  │ └────────────────────────────────────────┘                │   │
│  │                                                            │   │
│  │ Album                          Year                        │   │
│  │ ┌──────────────────┐          ┌──────────────────┐       │   │
│  │ │ After Hours      │          │ 2020             │       │   │
│  │ └──────────────────┘          └──────────────────┘       │   │
│  │                                                            │   │
│  │ Genre                          Director                    │   │
│  │ [Pop ▼]                       ┌──────────────────┐       │   │
│  │                               │ Anton Tammi      │       │   │
│  │                               └──────────────────┘       │   │
│  │                                                            │   │
│  │ Video URL (YouTube/Vimeo)                                 │   │
│  │ ┌────────────────────────────────────────┐                │   │
│  │ │ https://youtube.com/watch?v=...         │                │   │
│  │ └────────────────────────────────────────┘                │   │
│  │ [Check Availability]                                       │   │
│  │                                                            │   │
│  │ Tags (comma separated)                                     │   │
│  │ ┌────────────────────────────────────────┐                │   │
│  │ │ synthwave, 80s, official                │                │   │
│  │ └────────────────────────────────────────┘                │   │
│  │                                                            │   │
│  │ ☑ Download immediately                                     │   │
│  │ ☐ Add to queue only                                       │   │
│  │                                                            │   │
│  └────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  [Cancel]                               [Add to Library]          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Design Notes:**
- Modal overlay (600px wide)
- Tab navigation for different add methods
- Form validation with required fields (*)
- Auto-complete for artist/album fields
- URL validation with availability check
- Options for immediate download or queue
- Clear cancel/submit actions

---

## 10. Mobile Responsive Views

### Mobile Dashboard (375px width)
```
┌─────────────────────────┐
│ [≡] Video Jockey   [🔔] │
├─────────────────────────┤
│                         │
│ Welcome back!           │
│                         │
│ ┌─────────┬───────────┐ │
│ │ Videos  │ Artists   │ │
│ │ 1,247   │ 342       │ │
│ └─────────┴───────────┘ │
│                         │
│ ┌─────────┬───────────┐ │
│ │This Month│ Storage   │ │
│ │ 47       │ 124/500GB │ │
│ └─────────┴───────────┘ │
│                         │
│ Quick Actions           │
│ ┌───┬───┬───┬───┐      │
│ │ + │ ↓ │ 📁│ 🔍│      │
│ └───┴───┴───┴───┘      │
│                         │
│ Download Queue (2)      │
│ ┌─────────────────────┐ │
│ │ The Weeknd          │ │
│ │ Blinding Lights     │ │
│ │ [████████░░] 76%    │ │
│ ├─────────────────────┤ │
│ │ Dua Lipa            │ │
│ │ Levitating          │ │
│ │ [███░░░░░░░] 31%    │ │
│ └─────────────────────┘ │
│                         │
│ [⏸] [▶] [View All]     │
│                         │
└─────────────────────────┘
```

### Mobile Library Grid (375px width)
```
┌─────────────────────────┐
│ [≡] Video Jockey   [🔔] │
├─────────────────────────┤
│ [Search...]             │
│ [Filters ▼] [Sort ▼]   │
│                         │
│ My Library (1,247)      │
│                         │
│ ┌──────────┬──────────┐ │
│ │  [VIDEO] │  [VIDEO] │ │
│ │          │          │ │
│ │ The      │ Dua      │ │
│ │ Weeknd   │ Lipa     │ │
│ │ Blinding │Levitating│ │
│ │ 2020     │ 2021     │ │
│ └──────────┴──────────┘ │
│                         │
│ ┌──────────┬──────────┐ │
│ │  [VIDEO] │  [VIDEO] │ │
│ │          │          │ │
│ │ BTS      │ Taylor   │ │
│ │ Dynamite │ Swift    │ │
│ │ 2020     │ Anti-Hero│ │
│ │          │ 2022     │ │
│ └──────────┴──────────┘ │
│                         │
│ [< Prev] 1/52 [Next >] │
│                         │
│ ┌─────────────────────┐ │
│ │   Navigation Bar    │ │
│ │ [Home][Lib][+][Queue]│ │
│ └─────────────────────┘ │
└─────────────────────────┘
```

**Mobile Design Notes:**
- Stack elements vertically
- 2-column grid for videos
- Condensed information display
- Bottom navigation bar
- Swipe gestures for navigation
- Collapsible filters
- Touch-optimized controls (44px minimum)

---

## Interaction Patterns

### Loading States
- Skeleton screens for content loading
- Inline spinners for actions
- Progress bars for long operations
- Optimistic UI updates

### Error Handling
- Toast notifications for minor errors
- Inline error messages for forms
- Modal dialogs for critical errors
- Retry options for failed operations

### Animations
- Fade in/out: 200ms ease
- Slide transitions: 300ms ease-out
- Hover effects: 150ms ease
- Progress bars: smooth linear
- Modal overlays: 250ms ease

### Keyboard Shortcuts
- `/` - Focus search
- `a` - Add video
- `l` - Go to library
- `q` - View queue
- `s` - Settings
- `Space` - Play/pause video
- `Esc` - Close modal/cancel

### Accessibility
- Focus indicators on all interactive elements
- ARIA labels for icons and buttons
- Semantic HTML structure
- Keyboard navigation support
- Screen reader announcements
- High contrast mode support

---

## Implementation Notes

### Responsive Breakpoints
```css
Mobile:  320px - 767px
Tablet:  768px - 1023px
Desktop: 1024px - 1439px
Wide:    1440px+
```

### Component Library Recommendations
- **React**: Material-UI, Ant Design, or Chakra UI
- **Vue**: Vuetify, Element Plus, or Quasar
- **Icons**: Heroicons, Feather Icons, or Material Icons
- **Charts**: Recharts or Chart.js
- **Video Player**: Video.js or Plyr

### Performance Targets
- First Contentful Paint: < 1.5s
- Time to Interactive: < 3.5s
- Largest Contentful Paint: < 2.5s
- Cumulative Layout Shift: < 0.1
- Bundle size: < 200KB (initial)

### Browser Support
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+
- Mobile Safari iOS 14+
- Chrome Android 90+

---

## Summary

This comprehensive design document provides:
1. Complete visual design system with colors and typography
2. Detailed wireframes for all major screens
3. Mobile-responsive layouts
4. Component specifications
5. Interaction patterns and animations
6. Accessibility considerations
7. Implementation guidelines

The design emphasizes a clean, modern interface optimized for media management with a focus on user efficiency and visual clarity. The dark theme default reduces eye strain during extended use, while the responsive design ensures functionality across all devices.