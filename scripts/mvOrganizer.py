#!/usr/bin/env python3
"""
mvOrganizer.py - Music Video Downloader and Organizer for Kodi

Automates downloading, organizing, and metadata generation for music videos 
using CSV input. Output is structured for Kodi media center compatibility.
"""

import argparse
import csv
import json
import os
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse, parse_qs

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class MusicVideoOrganizer:
    """Main class for organizing music videos from CSV input."""
    
    def __init__(self, output_dir: str, overwrite: bool = False,
                 no_search: bool = False, cookies: Optional[str] = None,
                 force_download: bool = False):
        self.output_dir = Path(output_dir)
        self.overwrite = overwrite
        self.no_search = no_search
        self.cookies = cookies
        self.force_download = force_download
        self.stats = {
            'processed': 0,
            'downloaded': 0,
            'skipped': 0,
            'failed': 0,
            'nfo_created': 0
        }
        
    def check_dependencies(self) -> bool:
        """Check if required dependencies are installed."""
        dependencies = ['yt-dlp', 'ffmpeg']
        missing = []
        
        for dep in dependencies:
            if shutil.which(dep) is None:
                missing.append(dep)
                
        if missing:
            print(f"{Colors.FAIL}Missing required dependencies: {', '.join(missing)}{Colors.ENDC}")
            print("Please install them before running this script.")
            return False
            
        return True
    
    def normalize_filename(self, text: str) -> str:
        """
        Normalize filename by converting to lowercase, removing special characters (including hyphens) and replacing spaces.
        
        Args:
            text: Input text to normalize
            
        Returns:
            Normalized filename safe for filesystem (lowercase, no special chars)
        """
        # Convert to lowercase
        text = text.lower()
        
        # Normalize unicode characters (e.g., ä -> a)
        import unicodedata
        text = unicodedata.normalize('NFKD', text)
        text = ''.join([c for c in text if not unicodedata.combining(c)])
        
        # Remove special characters except alphanumeric, spaces, and underscores
        # Note: hyphens are now removed as well
        text = re.sub(r'[^\w\s]', '', text)
        
        # Replace spaces with underscores
        text = text.replace(' ', '_')
        
        # Remove multiple underscores
        text = re.sub(r'_+', '_', text)
        
        return text.strip('_')
    
    def validate_year(self, year_str: str) -> Optional[str]:
        """
        Validate year format (YYYY).
        
        Args:
            year_str: Year string to validate
            
        Returns:
            Validated year or None if invalid
        """
        if not year_str:
            return None
            
        year_str = year_str.strip()
        if re.match(r'^\d{4}$', year_str):
            year = int(year_str)
            if 1900 <= year <= datetime.now().year + 1:
                return year_str
                
        return None
    
    def is_valid_youtube_url(self, url: str) -> bool:
        """Check if URL is a valid YouTube URL."""
        if not url:
            return False
            
        parsed = urlparse(url)
        return parsed.netloc in ['www.youtube.com', 'youtube.com', 'youtu.be', 'm.youtube.com']
    
    def extract_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from YouTube URL."""
        parsed = urlparse(url)
        
        if parsed.netloc == 'youtu.be':
            return parsed.path[1:]
        elif parsed.netloc in ['www.youtube.com', 'youtube.com', 'm.youtube.com']:
            if parsed.path == '/watch':
                params = parse_qs(parsed.query)
                return params.get('v', [None])[0]
                
        return None
    
    def search_youtube(self, artist: str, title: str) -> Optional[str]:
        """
        Search YouTube for music video.
        
        Args:
            artist: Artist name
            title: Track title
            
        Returns:
            YouTube URL if found, None otherwise
        """
        query = f"{artist} {title} official music video"
        print(f"  {Colors.CYAN}Searching YouTube: {query}{Colors.ENDC}")
        
        cmd = [
            'yt-dlp',
            f'ytsearch1:{query}',
            '--get-id',
            '--no-warnings',
            '--quiet'
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0 and result.stdout.strip():
                video_id = result.stdout.strip()
                url = f"https://www.youtube.com/watch?v={video_id}"
                print(f"  {Colors.GREEN}Found video: {url}{Colors.ENDC}")
                return url
        except (subprocess.TimeoutExpired, Exception) as e:
            print(f"  {Colors.WARNING}Search failed: {str(e)}{Colors.ENDC}")
            
        return None
    
    def download_video(self, url: str, output_path: Path, force_overwrite: bool = False) -> bool:
        """
        Download video from YouTube URL.
        
        Args:
            url: YouTube URL
            output_path: Output file path
            force_overwrite: Whether to force overwrite existing files
            
        Returns:
            True if successful, False otherwise
        """
        print(f"  {Colors.BLUE}Downloading from: {url}{Colors.ENDC}")
        
        cmd = [
            'yt-dlp',
            url,
            '-o', str(output_path),
            '--format', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            '--merge-output-format', 'mp4',
            '--remux-video', 'mp4',
            '-S vcodec:h264,lang,quality,res,fps,hdr:12,acodec:aac',
            '--no-playlist',
            '--sleep-requests', '1',
            '--sleep-interval', '1',
            '--retry-sleep', 'fragment:300',
            '--quiet',
            '--no-warnings',
            '--progress'
        ]

        # Add force-overwrite flag when replacing existing videos
        if force_overwrite:
            cmd.append('--force-overwrites')
            print(f"  {Colors.WARNING}Force overwriting existing file{Colors.ENDC}")

        if self.cookies:
            cmd.extend(['--cookies', self.cookies])
        
        try:
            result = subprocess.run(cmd, timeout=600)
            if result.returncode == 0 and output_path.exists():
                print(f"  {Colors.GREEN}✓ Download successful{Colors.ENDC}")
                return True
            else:
                print(f"  {Colors.FAIL}✗ Download failed{Colors.ENDC}")
                return False
        except subprocess.TimeoutExpired:
            print(f"  {Colors.FAIL}✗ Download timeout{Colors.ENDC}")
            return False
        except Exception as e:
            print(f"  {Colors.FAIL}✗ Download error: {str(e)}{Colors.ENDC}")
            return False
    
    def create_nfo_element(self, tag: str, text: Optional[str]) -> Optional[ET.Element]:
        """Create XML element if text is not None."""
        if text:
            elem = ET.Element(tag)
            elem.text = str(text)
            return elem
        return None
    
    def read_existing_nfo(self, nfo_path: Path) -> Optional[ET.Element]:
        """Read existing NFO file and return root element."""
        if nfo_path.exists():
            try:
                tree = ET.parse(nfo_path)
                return tree.getroot()
            except ET.ParseError:
                print(f"  {Colors.WARNING}Warning: Could not parse existing NFO{Colors.ENDC}")
        return None
    
    def get_existing_sources(self, root: ET.Element) -> List[str]:
        """Extract existing source URLs from NFO."""
        sources = []
        sources_elem = root.find('sources')
        if sources_elem is not None:
            for url_elem in sources_elem.findall('url'):
                if url_elem.text:
                    sources.append(url_elem.text)
        return sources
    
    def add_source_to_nfo(self, root: ET.Element, url: str, 
                         failed: bool = False, search: bool = False) -> None:
        """Add a source URL to NFO with metadata."""
        sources_elem = root.find('sources')
        if sources_elem is None:
            sources_elem = ET.SubElement(root, 'sources')
        
        url_elem = ET.SubElement(sources_elem, 'url')
        url_elem.text = url
        url_elem.set('ts', datetime.now().isoformat())
        
        if failed:
            url_elem.set('failed', 'true')
        if search:
            url_elem.set('search', 'true')
    
    def write_nfo(self, nfo_path: Path, root: ET.Element) -> None:
        """Write NFO file with pretty printing."""
        # Convert to string with pretty printing
        rough_string = ET.tostring(root, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        
        # Add XML declaration
        xml_str = reparsed.toprettyxml(indent="    ", encoding=None)
        
        # Fix the declaration
        lines = xml_str.split('\n')
        lines[0] = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        
        # Remove empty lines
        lines = [line for line in lines if line.strip()]
        
        with open(nfo_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
    
    def create_nfo_from_csv(self, row: Dict[str, str]) -> ET.Element:
        """Create NFO root element from CSV row."""
        root = ET.Element('musicvideo')
        
        # Add basic metadata
        if self.validate_year(row.get('year', '')):
            elem = self.create_nfo_element('year', row['year'])
            if elem is not None:
                root.append(elem)
        
        for csv_field, nfo_tag in [
            ('artist', 'artist'),
            ('title', 'title'),
            ('album', 'album'),
            ('label', 'studio'),
            ('genre', 'genre'),
            ('director', 'director')
        ]:
            value = row.get(csv_field, '').strip()
            if value:
                elem = self.create_nfo_element(nfo_tag, value)
                if elem is not None:
                    root.append(elem)
        
        # Add tags
        tags = row.get('tag', '').strip()
        if tags:
            for tag in tags.split(','):
                tag = tag.strip()
                if tag:
                    elem = self.create_nfo_element('tag', tag)
                    if elem is not None:
                        root.append(elem)
        
        return root
    
    def create_artist_nfo(self, artist_name: str, artist_nfo_path: Path) -> None:
        """Create artist.nfo file if it doesn't exist."""
        if artist_nfo_path.exists():
            print(f"  {Colors.CYAN}artist.nfo exists{Colors.ENDC}")
            return
        
        # Create artist NFO
        root = ET.Element('artist')
        name_elem = ET.SubElement(root, 'name')
        name_elem.text = artist_name
        
        # Write with pretty printing
        self.write_nfo(artist_nfo_path, root)
        print(f"  {Colors.GREEN}✓ Created artist.nfo{Colors.ENDC}")
    
    def process_video(self, row: Dict[str, str], row_num: int) -> None:
        """
        Process a single video from CSV row.
        
        Args:
            row: CSV row data
            row_num: Row number for logging
        """
        # Validate required fields
        artist = row.get('artist', '').strip()
        title = row.get('title', '').strip()
        
        if not artist or not title:
            print(f"{Colors.FAIL}Row {row_num}: Missing required fields (artist/title){Colors.ENDC}")
            self.stats['failed'] += 1
            return
        
        print(f"\n{Colors.HEADER}[Row {row_num}] {artist} - {title}{Colors.ENDC}")
        
        # Create output directory and paths
        artist_dir = self.normalize_filename(artist)
        title_file = self.normalize_filename(title)
        
        artist_dir_path = self.output_dir / artist_dir
        artist_dir_path.mkdir(parents=True, exist_ok=True)
        
        video_path = artist_dir_path / f"{title_file}.mp4"
        nfo_path = artist_dir_path / f"{title_file}.nfo"
        artist_nfo_path = artist_dir_path / "artist.nfo"
        
        # Check if video exists
        video_exists = video_path.exists()
        
        # Handle existing NFO
        existing_root = self.read_existing_nfo(nfo_path)
        
        # Check if force download is enabled
        if self.force_download:
            print(f"  {Colors.WARNING}Force download enabled - ignoring existing sources{Colors.ENDC}")
            
            # Get URL from CSV
            youtube_url = row.get('youtube_url', '').strip()
            download_success = False
            
            # Use existing NFO or create new one
            if existing_root is not None:
                root = existing_root
                existing_sources = self.get_existing_sources(root)
            else:
                root = self.create_nfo_from_csv(row)
                existing_sources = []
            
            # Try provided URL first
            if youtube_url and self.is_valid_youtube_url(youtube_url):
                print(f"  {Colors.BLUE}Force downloading from provided URL{Colors.ENDC}")
                download_success = self.download_video(youtube_url, video_path, force_overwrite=True)
                
                # Only add source if not already in NFO (avoid duplicates)
                if youtube_url not in existing_sources:
                    self.add_source_to_nfo(root, youtube_url, failed=not download_success, search=False)
            
            # Try search if needed and no URL provided
            if not download_success and not youtube_url and not self.no_search:
                search_url = self.search_youtube(artist, title)
                if search_url:
                    print(f"  {Colors.BLUE}Force downloading from search result{Colors.ENDC}")
                    download_success = self.download_video(search_url, video_path, force_overwrite=True)
                    
                    # Only add source if not already in NFO
                    if search_url not in existing_sources:
                        self.add_source_to_nfo(root, search_url,
                                             failed=not download_success, search=True)
            
            # Write NFO
            self.write_nfo(nfo_path, root)
            if existing_root is None:
                self.stats['nfo_created'] += 1
            
            # Create artist.nfo
            self.create_artist_nfo(artist, artist_nfo_path)
            
            if download_success:
                self.stats['downloaded'] += 1
                print(f"  {Colors.GREEN}✓ Video downloaded successfully (force){Colors.ENDC}")
            else:
                self.stats['failed'] += 1
                print(f"  {Colors.FAIL}✗ Failed to download video (force){Colors.ENDC}")
                
        elif video_exists:
            print(f"  {Colors.CYAN}Video already exists{Colors.ENDC}")

            # Check and create artist.nfo if missing
            self.create_artist_nfo(artist, artist_nfo_path)

            # Create NFO if missing
            if existing_root is None:
                print(f"  {Colors.WARNING}Creating missing NFO file{Colors.ENDC}")
                root = self.create_nfo_from_csv(row)
                
                # Add source if provided
                youtube_url = row.get('youtube_url', '').strip()
                if youtube_url and self.is_valid_youtube_url(youtube_url):
                    self.add_source_to_nfo(root, youtube_url, failed=False, search=False)
                
                self.write_nfo(nfo_path, root)
                self.stats['nfo_created'] += 1
                
            else:
                # Check if we should redownload
                youtube_url = row.get('youtube_url', '').strip()
                if youtube_url and self.is_valid_youtube_url(youtube_url):
                    existing_sources = self.get_existing_sources(existing_root)
                    
                    if youtube_url not in existing_sources and self.overwrite:
                        print(f"  {Colors.BLUE}Attempting redownload from new URL{Colors.ENDC}")
                        
                        # Try download with force overwrite since we're replacing existing video
                        success = self.download_video(youtube_url, video_path, force_overwrite=True)
                        self.add_source_to_nfo(existing_root, youtube_url,
                                             failed=not success, search=False)
                        self.write_nfo(nfo_path, existing_root)
                        
                        if success:
                            self.stats['downloaded'] += 1
                        else:
                            self.stats['failed'] += 1
                    else:
                        print(f"  {Colors.CYAN}Skipping: URL already in sources or overwrite disabled{Colors.ENDC}")
                        self.stats['skipped'] += 1
                else:
                    print(f"  {Colors.CYAN}Skipping: No new URL provided{Colors.ENDC}")
                    self.stats['skipped'] += 1
        else:
            # Video doesn't exist - download it
            print(f"  {Colors.BLUE}Downloading new video{Colors.ENDC}")
            
            # Create NFO
            root = self.create_nfo_from_csv(row)
            
            # Try provided URL first
            youtube_url = row.get('youtube_url', '').strip()
            download_success = False
            
            if youtube_url and self.is_valid_youtube_url(youtube_url):
                download_success = self.download_video(youtube_url, video_path)
                self.add_source_to_nfo(root, youtube_url, failed=not download_success, search=False)
            
            # Try search if needed
            if not download_success and not self.no_search:
                search_url = self.search_youtube(artist, title)
                if search_url:
                    download_success = self.download_video(search_url, video_path)
                    self.add_source_to_nfo(root, search_url, 
                                         failed=not download_success, search=True)
            
            # Write NFO
            self.write_nfo(nfo_path, root)
            self.stats['nfo_created'] += 1
            
            # Create artist.nfo
            self.create_artist_nfo(artist, artist_nfo_path)
            
            if download_success:
                self.stats['downloaded'] += 1
                print(f"  {Colors.GREEN}✓ Video downloaded successfully{Colors.ENDC}")
            else:
                self.stats['failed'] += 1
                print(f"  {Colors.FAIL}✗ Failed to download video{Colors.ENDC}")
        
        self.stats['processed'] += 1
    
    def process_csv(self, csv_path: str) -> None:
        """
        Process CSV file containing music video metadata.
        
        Args:
            csv_path: Path to CSV file
        """
        print(f"{Colors.HEADER}{Colors.BOLD}Music Video Organizer{Colors.ENDC}")
        print(f"{Colors.CYAN}Processing: {csv_path}{Colors.ENDC}")
        print(f"{Colors.CYAN}Output directory: {self.output_dir}{Colors.ENDC}")
        print("-" * 60)
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                # Detect delimiter
                sample = f.readline()
                sniffer = csv.Sniffer()
                delimiter = sniffer.sniff(sample).delimiter
                
                # Be kind, rewind
                f.seek(0)
                
                reader = csv.DictReader(f, delimiter=delimiter)
                
                # Normalize field names (handle variations)
                field_mappings = {
                    'artists': 'artist',
                    'song': 'title',
                    'track': 'title',
                    'record_label': 'label',
                    'youtube': 'youtube_url',
                    'url': 'youtube_url',
                    'tags': 'tag'
                }
                
                for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is 1)
                    # Normalize field names
                    normalized_row = {}
                    for key, value in row.items():
                        if key:
                            key_lower = key.lower().strip()
                            mapped_key = field_mappings.get(key_lower, key_lower)
                            normalized_row[mapped_key] = value
                    
                    self.process_video(normalized_row, row_num)
                    
        except FileNotFoundError:
            print(f"{Colors.FAIL}Error: CSV file not found: {csv_path}{Colors.ENDC}")
            sys.exit(1)
        except csv.Error as e:
            print(f"{Colors.FAIL}Error reading CSV: {e}{Colors.ENDC}")
            sys.exit(1)
        except KeyboardInterrupt:
            print(f"\n{Colors.WARNING}Process interrupted by user{Colors.ENDC}")
        
        # Print summary
        self.print_summary()
    
    def print_summary(self) -> None:
        """Print processing summary."""
        print("\n" + "=" * 60)
        print(f"{Colors.HEADER}{Colors.BOLD}Processing Summary{Colors.ENDC}")
        print("-" * 60)
        print(f"Total processed: {self.stats['processed']}")
        print(f"{Colors.GREEN}Downloaded: {self.stats['downloaded']}{Colors.ENDC}")
        print(f"{Colors.CYAN}Skipped: {self.stats['skipped']}{Colors.ENDC}")
        print(f"{Colors.FAIL}Failed: {self.stats['failed']}{Colors.ENDC}")
        print(f"NFO files created: {self.stats['nfo_created']}")
        print("=" * 60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Music Video Organizer - Download and organize music videos for Kodi',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s videos.csv -o /media/MusicVideos
  %(prog)s videos.csv -o ./output --overwrite
  %(prog)s videos.csv -o ./output --no-search --cookies cookies.txt
        """
    )
    
    parser.add_argument(
        'csv_file',
        help='CSV file containing music video metadata'
    )
    
    parser.add_argument(
        '-o', '--output-dir',
        required=True,
        help='Base output directory for organized videos'
    )
    
    parser.add_argument(
        '--overwrite',
        action='store_true',
        help='Re-download existing videos from new URLs'
    )
    
    parser.add_argument(
        '--force-download',
        action='store_true',
        help='Force download videos, ignoring previous sources and replacing existing files'
    )
    
    parser.add_argument(
        '--no-search',
        action='store_true',
        help='Disable YouTube search fallback'
    )
    
    parser.add_argument(
        '--cookies',
        help='Cookie file for YouTube authentication'
    )
    
    args = parser.parse_args()
    
    # Initialize organizer
    organizer = MusicVideoOrganizer(
        output_dir=args.output_dir,
        overwrite=args.overwrite,
        no_search=args.no_search,
        cookies=args.cookies,
        force_download=args.force_download
    )
    
    # Check dependencies
    if not organizer.check_dependencies():
        sys.exit(1)
    
    # Process CSV
    organizer.process_csv(args.csv_file)


if __name__ == '__main__':
    main()