#!/usr/bin/env python3
"""
mvDuplicateFinder.py - Music Video Duplicate Finder

Recursively searches for .nfo files and identifies duplicate tracks
using fuzzy matching on artist and title fields.
"""

import argparse
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
from difflib import SequenceMatcher
import unicodedata
import re

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


class MusicVideoDuplicateFinder:
    """Find duplicate music videos based on NFO metadata."""
    
    def __init__(self, parent_dir: str, threshold: float = 0.85):
        """
        Initialize the duplicate finder.
        
        Args:
            parent_dir: Parent directory to search for NFO files
            threshold: Fuzzy match threshold (0-1, default 0.85)
        """
        self.parent_dir = Path(parent_dir)
        self.threshold = threshold
        self.nfo_files = []
        self.tracks = []
        self.duplicates = defaultdict(list)
        
    def normalize_text(self, text: str) -> str:
        """
        Normalize text for fuzzy matching.
        
        Args:
            text: Input text to normalize
            
        Returns:
            Normalized text for comparison
        """
        if not text:
            return ""
            
        # Convert to lowercase
        text = text.lower()
        
        # Normalize unicode characters
        text = unicodedata.normalize('NFKD', text)
        text = ''.join([c for c in text if not unicodedata.combining(c)])
        
        # Remove special characters and extra whitespace
        text = re.sub(r'[^\w\s]', ' ', text)
        text = ' '.join(text.split())
        
        # Remove common suffixes that indicate versions
        version_patterns = [
            r'\s*\b(remaster|remastered|remix|remixed|live|acoustic|demo|radio\s*edit|extended|original|official)\b\s*',
            r'\s*\(\s*(remaster|remastered|remix|remixed|live|acoustic|demo|radio\s*edit|extended|original|official)\s*\)\s*',
            r'\s*\[\s*(remaster|remastered|remix|remixed|live|acoustic|demo|radio\s*edit|extended|original|official)\s*\]\s*',
        ]
        for pattern in version_patterns:
            text = re.sub(pattern, ' ', text, flags=re.IGNORECASE)
        
        # Common replacements
        replacements = {
            ' and ': ' & ',
            ' feat ': ' ft ',
            ' featuring ': ' ft ',
            ' versus ': ' vs ',
            ' part ': ' pt ',
            ' the ': ' ',  # Remove "the" for better matching
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
            
        return text.strip()
    
    def fuzzy_match(self, text1: str, text2: str) -> float:
        """
        Calculate fuzzy match score between two strings.
        
        Args:
            text1: First string
            text2: Second string
            
        Returns:
            Match score between 0 and 1
        """
        norm1 = self.normalize_text(text1)
        norm2 = self.normalize_text(text2)
        
        return SequenceMatcher(None, norm1, norm2).ratio()
    
    def find_nfo_files(self) -> None:
        """Find all NFO files recursively in parent directory."""
        print(f"\n{Colors.HEADER}Searching for NFO files in: {self.parent_dir}{Colors.ENDC}")
        
        for root, _, files in os.walk(self.parent_dir):
            for file in files:
                if file.endswith('.nfo') and file != 'artist.nfo':
                    self.nfo_files.append(Path(root) / file)
        
        print(f"Found {Colors.GREEN}{len(self.nfo_files)}{Colors.ENDC} NFO files")
    
    def parse_nfo(self, nfo_path: Path) -> Optional[Dict[str, str]]:
        """
        Parse NFO file and extract artist and title.
        
        Args:
            nfo_path: Path to NFO file
            
        Returns:
            Dictionary with metadata or None if parse fails
        """
        try:
            tree = ET.parse(nfo_path)
            root = tree.getroot()
            
            # Extract artist and title
            artist_elem = root.find('artist')
            title_elem = root.find('title')
            
            if artist_elem is not None and title_elem is not None:
                artist = artist_elem.text or ""
                title = title_elem.text or ""
                
                if artist and title:
                    return {
                        'artist': artist,
                        'title': title,
                        'path': str(nfo_path),
                        'video_path': str(nfo_path.with_suffix('.mp4'))
                    }
        except ET.ParseError:
            print(f"{Colors.WARNING}Warning: Could not parse {nfo_path}{Colors.ENDC}")
        except Exception as e:
            print(f"{Colors.WARNING}Warning: Error reading {nfo_path}: {e}{Colors.ENDC}")
            
        return None
    
    def load_tracks(self) -> None:
        """Load all tracks from NFO files."""
        print(f"\n{Colors.HEADER}Loading track information...{Colors.ENDC}")
        
        for nfo_file in self.nfo_files:
            track_info = self.parse_nfo(nfo_file)
            if track_info:
                self.tracks.append(track_info)
        
        print(f"Loaded {Colors.GREEN}{len(self.tracks)}{Colors.ENDC} tracks with metadata")
    
    def find_duplicates(self) -> None:
        """Find duplicate tracks using fuzzy matching."""
        print(f"\n{Colors.HEADER}Analyzing for duplicates (threshold: {self.threshold:.0%})...{Colors.ENDC}")
        
        # Compare each track with all others
        for i, track1 in enumerate(self.tracks):
            for j, track2 in enumerate(self.tracks[i+1:], start=i+1):
                # Calculate match scores
                artist_score = self.fuzzy_match(track1['artist'], track2['artist'])
                title_score = self.fuzzy_match(track1['title'], track2['title'])
                
                # Combined score (weighted average)
                combined_score = (artist_score * 0.4) + (title_score * 0.6)
                
                # Check if it's a duplicate
                if combined_score >= self.threshold:
                    # Find which duplicate group these tracks belong to
                    group_key = None
                    
                    # Check if track1 is already in a group
                    for key, group in self.duplicates.items():
                        if any(t['path'] == track1['path'] for t in group):
                            group_key = key
                            break
                    
                    # If not found, check if track2 is in a group
                    if not group_key:
                        for key, group in self.duplicates.items():
                            if any(t['path'] == track2['path'] for t in group):
                                group_key = key
                                break
                    
                    # If neither is in a group, create a new one
                    if not group_key:
                        group_key = f"group_{len(self.duplicates) + 1}"
                        self.duplicates[group_key].append({
                            **track1,
                            'match_score': 1.0
                        })
                    
                    # Add track1 if not already in the group
                    if not any(t['path'] == track1['path'] for t in self.duplicates[group_key]):
                        self.duplicates[group_key].append({
                            **track1,
                            'match_score': 1.0
                        })
                    
                    # Add track2 if not already in the group
                    if not any(t['path'] == track2['path'] for t in self.duplicates[group_key]):
                        self.duplicates[group_key].append({
                            **track2,
                            'match_score': combined_score
                        })
    
    def print_duplicates(self) -> None:
        """Print found duplicates in a formatted way."""
        if not self.duplicates:
            print(f"\n{Colors.GREEN}No duplicates found!{Colors.ENDC}")
            return
        
        print(f"\n{Colors.HEADER}{Colors.BOLD}Found {len(self.duplicates)} duplicate groups:{Colors.ENDC}")
        print("=" * 80)
        
        for group_num, (key, tracks) in enumerate(self.duplicates.items(), 1):
            print(f"\n{Colors.WARNING}Duplicate Group {group_num}:{Colors.ENDC}")
            
            # Sort by match score (highest first)
            tracks.sort(key=lambda x: x['match_score'], reverse=True)
            
            for i, track in enumerate(tracks):
                status = "ORIGINAL" if i == 0 else f"DUPLICATE ({track['match_score']:.0%} match)"
                color = Colors.GREEN if i == 0 else Colors.FAIL
                
                print(f"\n  {color}[{status}]{Colors.ENDC}")
                print(f"  Artist: {track['artist']}")
                print(f"  Title:  {track['title']}")
                print(f"  NFO:    {track['path']}")
                
                # Check if video file exists
                video_path = Path(track['video_path'])
                if video_path.exists():
                    size_mb = video_path.stat().st_size / (1024 * 1024)
                    print(f"  Video:  {track['video_path']} ({size_mb:.1f} MB)")
                else:
                    print(f"  Video:  {Colors.WARNING}NOT FOUND{Colors.ENDC}")
            
            print("-" * 80)
    
    def export_report(self, output_file: str) -> None:
        """
        Export duplicate report to a file.
        
        Args:
            output_file: Path to output file
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("Music Video Duplicate Report\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Parent Directory: {self.parent_dir}\n")
            f.write(f"Total NFO Files: {len(self.nfo_files)}\n")
            f.write(f"Total Tracks: {len(self.tracks)}\n")
            f.write(f"Duplicate Groups: {len(self.duplicates)}\n")
            f.write(f"Threshold: {self.threshold:.0%}\n")
            f.write("\n" + "=" * 80 + "\n\n")
            
            for group_num, (key, tracks) in enumerate(self.duplicates.items(), 1):
                f.write(f"Duplicate Group {group_num}:\n")
                f.write("-" * 40 + "\n")
                
                tracks.sort(key=lambda x: x['match_score'], reverse=True)
                
                for i, track in enumerate(tracks):
                    status = "ORIGINAL" if i == 0 else f"DUPLICATE ({track['match_score']:.0%})"
                    f.write(f"\n[{status}]\n")
                    f.write(f"Artist: {track['artist']}\n")
                    f.write(f"Title:  {track['title']}\n")
                    f.write(f"Path:   {track['path']}\n")
                    
                    video_path = Path(track['video_path'])
                    if video_path.exists():
                        size_mb = video_path.stat().st_size / (1024 * 1024)
                        f.write(f"Video:  {track['video_path']} ({size_mb:.1f} MB)\n")
                    else:
                        f.write(f"Video:  NOT FOUND\n")
                
                f.write("\n")
        
        print(f"\n{Colors.GREEN}Report exported to: {output_file}{Colors.ENDC}")
    
    def run(self) -> None:
        """Run the duplicate finding process."""
        # Find all NFO files
        self.find_nfo_files()
        
        if not self.nfo_files:
            print(f"{Colors.FAIL}No NFO files found in {self.parent_dir}{Colors.ENDC}")
            return
        
        # Load track information
        self.load_tracks()
        
        if not self.tracks:
            print(f"{Colors.FAIL}No valid tracks found in NFO files{Colors.ENDC}")
            return
        
        # Find duplicates
        self.find_duplicates()
        
        # Print results
        self.print_duplicates()
        
        # Summary
        print(f"\n{Colors.HEADER}Summary:{Colors.ENDC}")
        print(f"  Total tracks analyzed: {len(self.tracks)}")
        print(f"  Duplicate groups found: {len(self.duplicates)}")
        
        if self.duplicates:
            total_duplicates = sum(len(tracks) - 1 for tracks in self.duplicates.values())
            print(f"  Total duplicate files: {total_duplicates}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Music Video Duplicate Finder - Find duplicate tracks using NFO metadata',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s /media/MusicVideos
  %(prog)s /media/MusicVideos --threshold 0.9
  %(prog)s ./videos --export duplicates_report.txt
        """
    )
    
    parser.add_argument(
        'directory',
        help='Parent directory to search for NFO files'
    )
    
    parser.add_argument(
        '-t', '--threshold',
        type=float,
        default=0.85,
        help='Fuzzy match threshold (0-1, default: 0.85)'
    )
    
    parser.add_argument(
        '-e', '--export',
        help='Export results to text file'
    )
    
    args = parser.parse_args()
    
    # Validate threshold
    if not 0 <= args.threshold <= 1:
        print(f"{Colors.FAIL}Error: Threshold must be between 0 and 1{Colors.ENDC}")
        sys.exit(1)
    
    # Validate directory
    if not os.path.isdir(args.directory):
        print(f"{Colors.FAIL}Error: Directory not found: {args.directory}{Colors.ENDC}")
        sys.exit(1)
    
    # Create finder instance
    finder = MusicVideoDuplicateFinder(args.directory, args.threshold)
    
    # Run the process
    finder.run()
    
    # Export if requested
    if args.export and finder.duplicates:
        finder.export_report(args.export)


if __name__ == '__main__':
    main()