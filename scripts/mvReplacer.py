#!/usr/bin/env python3
"""
mvReplacer.py - Music Video Replacer for Kodi

Searches for and downloads alternative sources for existing music videos.
Takes an NFO file path as input, searches for a new video source, downloads
if a unique source is found, and updates the NFO metadata.
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple
from urllib.parse import urlparse

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


class MusicVideoReplacer:
    """Main class for replacing music videos from existing NFO files."""
    
    def __init__(self, cookies: Optional[str] = None, dry_run: bool = False):
        self.cookies = cookies
        self.dry_run = dry_run
        self.stats = {
            'processed': 0,
            'replaced': 0,
            'skipped': 0,
            'failed': 0
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
    
    def is_valid_youtube_url(self, url: str) -> bool:
        """Check if URL is a valid YouTube URL."""
        if not url:
            return False
            
        parsed = urlparse(url)
        return parsed.netloc in ['www.youtube.com', 'youtube.com', 'youtu.be', 'm.youtube.com']
    
    def extract_video_info_from_nfo(self, root: ET.Element) -> Tuple[Optional[str], Optional[str]]:
        """Extract artist and title from NFO."""
        artist_elem = root.find('artist')
        title_elem = root.find('title')
        
        artist = artist_elem.text if artist_elem is not None and artist_elem.text else None
        title = title_elem.text if title_elem is not None and title_elem.text else None
        
        return artist, title
    
    def get_existing_sources(self, root: ET.Element) -> List[str]:
        """Extract existing source URLs from NFO."""
        sources = []
        sources_elem = root.find('sources')
        if sources_elem is not None:
            for url_elem in sources_elem.findall('url'):
                if url_elem.text:
                    sources.append(url_elem.text)
        return sources
    
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
    
    def download_video(self, url: str, output_path: Path) -> bool:
        """
        Download video from YouTube URL.
        
        Args:
            url: YouTube URL
            output_path: Output file path
            
        Returns:
            True if successful, False otherwise
        """
        if self.dry_run:
            print(f"  {Colors.CYAN}[DRY RUN] Would download from: {url}{Colors.ENDC}")
            print(f"  {Colors.CYAN}[DRY RUN] Output: {output_path}{Colors.ENDC}")
            return True
            
        print(f"  {Colors.BLUE}Downloading from: {url}{Colors.ENDC}")
        
        cmd = [
            'yt-dlp',
            url,
            '-o', str(output_path),
            '--format', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            '--merge-output-format', 'mp4',
            '--remux-video', 'mp4',
            '-S', 'vcodec:h264,lang,quality,res,fps,hdr:12,acodec:aac',
            '--no-playlist',
            '--sleep-requests', '1',
            '--sleep-interval', '1',
            '--retry-sleep', 'fragment:300',
            '--quiet',
            '--no-warnings',
            '--progress',
            '--force-overwrites'  # Always force overwrite when replacing
        ]

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
    
    def add_source_to_nfo(self, root: ET.Element, url: str, 
                         failed: bool = False, search: bool = True) -> None:
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
        if self.dry_run:
            print(f"  {Colors.CYAN}[DRY RUN] Would update NFO: {nfo_path}{Colors.ENDC}")
            return
            
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
        
        print(f"  {Colors.GREEN}✓ NFO updated{Colors.ENDC}")
    
    def process_nfo(self, nfo_path: Path) -> None:
        """
        Process a single NFO file to find and download alternative source.
        
        Args:
            nfo_path: Path to NFO file
        """
        print(f"\n{Colors.HEADER}{Colors.BOLD}Processing: {nfo_path}{Colors.ENDC}")
        
        # Check if NFO exists
        if not nfo_path.exists():
            print(f"{Colors.FAIL}Error: NFO file not found{Colors.ENDC}")
            self.stats['failed'] += 1
            return
        
        # Parse NFO
        try:
            tree = ET.parse(nfo_path)
            root = tree.getroot()
        except ET.ParseError as e:
            print(f"{Colors.FAIL}Error parsing NFO: {e}{Colors.ENDC}")
            self.stats['failed'] += 1
            return
        
        # Extract artist and title
        artist, title = self.extract_video_info_from_nfo(root)
        
        if not artist or not title:
            print(f"{Colors.FAIL}Error: Missing artist or title in NFO{Colors.ENDC}")
            self.stats['failed'] += 1
            return
        
        print(f"  Artist: {artist}")
        print(f"  Title: {title}")
        
        # Get existing sources
        existing_sources = self.get_existing_sources(root)
        
        if existing_sources:
            print(f"  {Colors.CYAN}Existing sources: {len(existing_sources)}{Colors.ENDC}")
            for i, source in enumerate(existing_sources, 1):
                print(f"    {i}. {source}")
        else:
            print(f"  {Colors.WARNING}No existing sources found{Colors.ENDC}")
        
        # Determine video path from NFO path
        video_path = nfo_path.with_suffix('.mp4')
        
        # Check if video exists
        video_exists = video_path.exists()
        if video_exists:
            print(f"  {Colors.CYAN}Video file exists: {video_path.name}{Colors.ENDC}")
        else:
            print(f"  {Colors.WARNING}Video file missing: {video_path.name}{Colors.ENDC}")
        
        # Search for new source
        search_url = self.search_youtube(artist, title)
        
        if not search_url:
            print(f"  {Colors.FAIL}No new source found{Colors.ENDC}")
            self.stats['skipped'] += 1
            return
        
        # Check if URL is already in sources
        if search_url in existing_sources:
            print(f"  {Colors.WARNING}Source already exists in NFO, skipping{Colors.ENDC}")
            self.stats['skipped'] += 1
            return
        
        # Download from new source
        print(f"  {Colors.BLUE}Found new unique source, attempting download{Colors.ENDC}")
        
        download_success = self.download_video(search_url, video_path)
        
        # Update NFO with new source
        self.add_source_to_nfo(root, search_url, failed=not download_success, search=True)
        self.write_nfo(nfo_path, root)
        
        if download_success:
            self.stats['replaced'] += 1
            print(f"  {Colors.GREEN}✓ Video replaced successfully{Colors.ENDC}")
        else:
            self.stats['failed'] += 1
            print(f"  {Colors.FAIL}✗ Failed to replace video{Colors.ENDC}")
        
        self.stats['processed'] += 1
    
    def process_batch(self, nfo_files: List[Path]) -> None:
        """
        Process multiple NFO files.
        
        Args:
            nfo_files: List of NFO file paths
        """
        print(f"{Colors.HEADER}{Colors.BOLD}Music Video Replacer - Batch Mode{Colors.ENDC}")
        print(f"Processing {len(nfo_files)} NFO file(s)")
        print("-" * 60)
        
        for nfo_path in nfo_files:
            try:
                self.process_nfo(nfo_path)
            except KeyboardInterrupt:
                print(f"\n{Colors.WARNING}Process interrupted by user{Colors.ENDC}")
                break
            except Exception as e:
                print(f"{Colors.FAIL}Error processing {nfo_path}: {e}{Colors.ENDC}")
                self.stats['failed'] += 1
        
        # Print summary
        self.print_summary()
    
    def print_summary(self) -> None:
        """Print processing summary."""
        print("\n" + "=" * 60)
        print(f"{Colors.HEADER}{Colors.BOLD}Processing Summary{Colors.ENDC}")
        print("-" * 60)
        print(f"Total processed: {self.stats['processed']}")
        print(f"{Colors.GREEN}Replaced: {self.stats['replaced']}{Colors.ENDC}")
        print(f"{Colors.CYAN}Skipped: {self.stats['skipped']}{Colors.ENDC}")
        print(f"{Colors.FAIL}Failed: {self.stats['failed']}{Colors.ENDC}")
        print("=" * 60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Music Video Replacer - Search and replace music videos from NFO files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s /path/to/video.nfo
  %(prog)s /path/to/video1.nfo /path/to/video2.nfo
  %(prog)s /music_videos/artist/song.nfo --cookies cookies.txt
  %(prog)s *.nfo --dry-run
        """
    )
    
    parser.add_argument(
        'nfo_files',
        nargs='+',
        type=Path,
        help='NFO file(s) to process'
    )
    
    parser.add_argument(
        '--cookies',
        help='Cookie file for YouTube authentication'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )
    
    args = parser.parse_args()
    
    # Initialize replacer
    replacer = MusicVideoReplacer(
        cookies=args.cookies,
        dry_run=args.dry_run
    )
    
    # Check dependencies
    if not replacer.check_dependencies():
        sys.exit(1)
    
    # Process NFO files
    if len(args.nfo_files) == 1:
        replacer.process_nfo(args.nfo_files[0])
        if replacer.stats['processed'] > 0:
            replacer.print_summary()
    else:
        replacer.process_batch(args.nfo_files)


if __name__ == '__main__':
    main()