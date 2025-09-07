#!/usr/bin/env python3
"""
mvTagManager - Add or remove tags from music video NFO files for specified artists

This script reads a list of artist names from a file and adds or removes
a specified tag from all NFO files found under each artist's directory.
"""

import argparse
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Set, Tuple
import unicodedata
import re

# ANSI color codes for terminal output
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def normalize_name(name: str) -> str:
    """
    Normalize artist/file names to match mvOrganizer.py conventions.
    - Convert to lowercase
    - Remove special characters (including hyphens)
    - Normalize diacritics (ä → a)
    - Replace spaces with underscores
    """
    # Convert to lowercase
    name = name.lower()
    
    # Normalize unicode characters (remove diacritics)
    name = ''.join(
        c for c in unicodedata.normalize('NFD', name)
        if unicodedata.category(c) != 'Mn'
    )
    
    # Remove special characters (keep only alphanumeric and spaces)
    name = re.sub(r'[^a-z0-9\s]', '', name)
    
    # Replace spaces with underscores
    name = name.replace(' ', '_')
    
    # Remove multiple underscores
    name = re.sub(r'_+', '_', name)
    
    # Strip leading/trailing underscores
    name = name.strip('_')
    
    return name

class TagManager:
    def __init__(self, base_dir: Path, artists_file: Path, tag: str, action: str, verbose: bool = False):
        """
        Initialize the tag manager.
        
        Args:
            base_dir: Parent directory containing artist directories
            artists_file: File containing artist names (one per line)
            tag: Tag to add or remove
            action: 'add' or 'remove'
            verbose: Enable verbose output
        """
        self.base_dir = base_dir
        self.artists_file = artists_file
        self.tag = tag
        self.action = action
        self.verbose = verbose
        
        # Statistics
        self.stats = {
            'artists_processed': 0,
            'nfo_files_found': 0,
            'nfo_files_modified': 0,
            'tags_added': 0,
            'tags_removed': 0,
            'already_present': 0,
            'not_present': 0,
            'errors': 0
        }
        
    def load_artists(self) -> List[str]:
        """Load artist names from file."""
        artists = []
        
        try:
            with open(self.artists_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):  # Skip empty lines and comments
                        artists.append(line)
        except FileNotFoundError:
            print(f"{Colors.RED}✗ Artists file not found: {self.artists_file}{Colors.RESET}")
            sys.exit(1)
        except Exception as e:
            print(f"{Colors.RED}✗ Error reading artists file: {e}{Colors.RESET}")
            sys.exit(1)
            
        return artists
    
    def find_artist_directory(self, artist: str) -> Path:
        """
        Find the artist directory using normalized name.
        
        Args:
            artist: Original artist name
            
        Returns:
            Path to artist directory or None if not found
        """
        normalized_artist = normalize_name(artist)
        artist_dir = self.base_dir / normalized_artist
        
        if artist_dir.exists() and artist_dir.is_dir():
            return artist_dir
        
        return None
    
    def find_nfo_files(self, artist_dir: Path) -> List[Path]:
        """
        Find all NFO files under an artist directory.
        Excludes artist.nfo files.
        
        Args:
            artist_dir: Path to artist directory
            
        Returns:
            List of NFO file paths
        """
        nfo_files = []
        
        for root, dirs, files in os.walk(artist_dir):
            for file in files:
                if file.endswith('.nfo') and file != 'artist.nfo':
                    nfo_files.append(Path(root) / file)
                    
        return nfo_files
    
    def process_nfo_file(self, nfo_path: Path) -> Tuple[bool, str]:
        """
        Process a single NFO file to add or remove tag.
        
        Args:
            nfo_path: Path to NFO file
            
        Returns:
            Tuple of (modified, message)
        """
        try:
            # Parse the XML file
            tree = ET.parse(nfo_path)
            root = tree.getroot()
            
            # Find existing tags
            existing_tags = set()
            tag_elements = root.findall('tag')
            for elem in tag_elements:
                if elem.text:
                    existing_tags.add(elem.text.strip())
            
            modified = False
            message = ""
            
            if self.action == 'add':
                if self.tag in existing_tags:
                    self.stats['already_present'] += 1
                    message = f"Tag '{self.tag}' already present"
                else:
                    # Add new tag element
                    new_tag = ET.SubElement(root, 'tag')
                    new_tag.text = self.tag
                    modified = True
                    self.stats['tags_added'] += 1
                    message = f"Added tag '{self.tag}'"
                    
            elif self.action == 'remove':
                if self.tag not in existing_tags:
                    self.stats['not_present'] += 1
                    message = f"Tag '{self.tag}' not present"
                else:
                    # Remove matching tag elements
                    for elem in tag_elements:
                        if elem.text and elem.text.strip() == self.tag:
                            root.remove(elem)
                            modified = True
                    self.stats['tags_removed'] += 1
                    message = f"Removed tag '{self.tag}'"
            
            # Save the file if modified
            if modified:
                # Pretty print the XML
                self.indent_xml(root)
                tree.write(nfo_path, encoding='UTF-8', xml_declaration=True)
                self.stats['nfo_files_modified'] += 1
                
            return modified, message
            
        except ET.ParseError as e:
            self.stats['errors'] += 1
            return False, f"XML parse error: {e}"
        except Exception as e:
            self.stats['errors'] += 1
            return False, f"Error: {e}"
    
    def indent_xml(self, elem, level=0):
        """
        Recursively add indentation to XML elements for pretty printing.
        
        Args:
            elem: XML element
            level: Current indentation level
        """
        i = "\n" + level * "    "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "    "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for elem in elem:
                self.indent_xml(elem, level + 1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i
    
    def process_artist(self, artist: str) -> int:
        """
        Process all NFO files for a single artist.
        
        Args:
            artist: Artist name
            
        Returns:
            Number of files modified
        """
        # Find artist directory
        artist_dir = self.find_artist_directory(artist)
        
        if not artist_dir:
            print(f"{Colors.YELLOW}  ⚠ Artist directory not found for: {artist}{Colors.RESET}")
            if self.verbose:
                normalized = normalize_name(artist)
                expected_path = self.base_dir / normalized
                print(f"    Expected path: {expected_path}")
            return 0
        
        # Find NFO files
        nfo_files = self.find_nfo_files(artist_dir)
        
        if not nfo_files:
            print(f"{Colors.YELLOW}  ⚠ No NFO files found for: {artist}{Colors.RESET}")
            return 0
        
        self.stats['nfo_files_found'] += len(nfo_files)
        
        if self.verbose:
            print(f"  Found {len(nfo_files)} NFO file(s) in {artist_dir}")
        
        # Process each NFO file
        modified_count = 0
        for nfo_path in nfo_files:
            relative_path = nfo_path.relative_to(self.base_dir)
            modified, message = self.process_nfo_file(nfo_path)
            
            if modified:
                modified_count += 1
                if self.verbose:
                    print(f"    {Colors.GREEN}✓{Colors.RESET} {relative_path}: {message}")
            elif self.verbose:
                print(f"    {Colors.CYAN}○{Colors.RESET} {relative_path}: {message}")
        
        return modified_count
    
    def run(self):
        """Execute the tag management operation."""
        # Load artists
        artists = self.load_artists()
        
        if not artists:
            print(f"{Colors.RED}✗ No artists found in file{Colors.RESET}")
            sys.exit(1)
        
        # Print header
        action_text = "Adding" if self.action == 'add' else "Removing"
        print(f"\n{Colors.BOLD}{action_text} tag '{self.tag}' for {len(artists)} artist(s){Colors.RESET}")
        print(f"Base directory: {self.base_dir}\n")
        
        # Process each artist
        for artist in artists:
            print(f"{Colors.BLUE}Processing: {artist}{Colors.RESET}")
            modified_count = self.process_artist(artist)
            
            if modified_count > 0:
                print(f"  {Colors.GREEN}✓ Modified {modified_count} file(s){Colors.RESET}")
            
            self.stats['artists_processed'] += 1
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print operation summary."""
        print(f"\n{Colors.BOLD}{'=' * 70}{Colors.RESET}")
        print(f"{Colors.BOLD}Summary{Colors.RESET}")
        print(f"{'=' * 70}")
        
        print(f"Artists processed: {self.stats['artists_processed']}")
        print(f"NFO files found: {self.stats['nfo_files_found']}")
        print(f"NFO files modified: {Colors.GREEN}{self.stats['nfo_files_modified']}{Colors.RESET}")
        
        if self.action == 'add':
            print(f"Tags added: {Colors.GREEN}{self.stats['tags_added']}{Colors.RESET}")
            print(f"Already present: {Colors.YELLOW}{self.stats['already_present']}{Colors.RESET}")
        else:
            print(f"Tags removed: {Colors.GREEN}{self.stats['tags_removed']}{Colors.RESET}")
            print(f"Not present: {Colors.YELLOW}{self.stats['not_present']}{Colors.RESET}")
        
        if self.stats['errors'] > 0:
            print(f"Errors: {Colors.RED}{self.stats['errors']}{Colors.RESET}")
        
        print(f"{'=' * 70}")
        
        # Exit with error code if there were errors
        if self.stats['errors'] > 0:
            sys.exit(1)

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Add or remove tags from music video NFO files for specified artists',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Add a tag to all videos for artists in list:
    python3 mvTagManager.py /media/MusicVideos artists.txt --add "80s"
    
  Remove a tag from all videos for artists in list:
    python3 mvTagManager.py /media/MusicVideos artists.txt --remove "draft"
    
  Add tag with verbose output:
    python3 mvTagManager.py /media/MusicVideos artists.txt --add "featured" --verbose

Artist File Format:
  One artist name per line. Lines starting with # are treated as comments.
  Empty lines are ignored.
  
  Example artists.txt:
    # 80s Artists
    Duran Duran
    Depeche Mode
    The Cure
    
    # 90s Artists  
    Nirvana
    Pearl Jam
        """
    )
    
    parser.add_argument('directory',
                       help='Parent directory containing artist subdirectories')
    parser.add_argument('artists_file',
                       help='File containing artist names (one per line)')
    
    # Action group (mutually exclusive)
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument('--add',
                            metavar='TAG',
                            help='Tag to add to NFO files')
    action_group.add_argument('--remove',
                            metavar='TAG',
                            help='Tag to remove from NFO files')
    
    parser.add_argument('-v', '--verbose',
                       action='store_true',
                       help='Show detailed output for each file')
    
    args = parser.parse_args()
    
    # Validate directory
    base_dir = Path(args.directory)
    if not base_dir.exists():
        print(f"{Colors.RED}✗ Directory not found: {base_dir}{Colors.RESET}")
        sys.exit(1)
    if not base_dir.is_dir():
        print(f"{Colors.RED}✗ Not a directory: {base_dir}{Colors.RESET}")
        sys.exit(1)
    
    # Validate artists file
    artists_file = Path(args.artists_file)
    if not artists_file.exists():
        print(f"{Colors.RED}✗ Artists file not found: {artists_file}{Colors.RESET}")
        sys.exit(1)
    
    # Determine action and tag
    if args.add:
        action = 'add'
        tag = args.add
    else:
        action = 'remove'
        tag = args.remove
    
    # Create and run tag manager
    manager = TagManager(
        base_dir=base_dir,
        artists_file=artists_file,
        tag=tag,
        action=action,
        verbose=args.verbose
    )
    
    try:
        manager.run()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠ Operation cancelled by user{Colors.RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}✗ Unexpected error: {e}{Colors.RESET}")
        sys.exit(1)

if __name__ == '__main__':
    main()