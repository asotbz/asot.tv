#!/usr/bin/env python3
"""
mvNfoSourceCleaner.py - Music Video NFO Source Cleaner

Recursively searches for .nfo files and cleans up their <sources> elements by:
- Removing duplicate URLs (keeping failed versions when duplicates exist)
- Removing 'index' and 'channel' attributes
- Retaining unique URLs with 'search=true' attribute
"""

import argparse
import os
import sys
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from collections import defaultdict

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


class NfoSourceCleaner:
    """Clean up sources in NFO files."""
    
    def __init__(self, parent_dir: str, dry_run: bool = False):
        """
        Initialize the NFO source cleaner.
        
        Args:
            parent_dir: Parent directory to search for NFO files
            dry_run: If True, show what would be done without making changes
        """
        self.parent_dir = Path(parent_dir)
        self.dry_run = dry_run
        self.nfo_files = []
        self.stats = {
            'files_found': 0,
            'files_processed': 0,
            'files_modified': 0,
            'sources_removed': 0,
            'attributes_removed': 0,
            'errors': 0
        }
        
    def find_nfo_files(self) -> None:
        """Find all NFO files recursively in parent directory."""
        print(f"\n{Colors.HEADER}Searching for NFO files in: {self.parent_dir}{Colors.ENDC}")
        
        for root, _, files in os.walk(self.parent_dir):
            for file in files:
                if file.endswith('.nfo') and file != 'artist.nfo':
                    self.nfo_files.append(Path(root) / file)
        
        self.stats['files_found'] = len(self.nfo_files)
        print(f"Found {Colors.GREEN}{len(self.nfo_files)}{Colors.ENDC} NFO files")
    
    def parse_nfo(self, nfo_path: Path) -> Optional[ET.ElementTree]:
        """
        Parse NFO file and return the tree.
        
        Args:
            nfo_path: Path to NFO file
            
        Returns:
            ElementTree or None if parse fails
        """
        try:
            tree = ET.parse(nfo_path)
            return tree
        except ET.ParseError as e:
            print(f"{Colors.WARNING}Warning: Could not parse {nfo_path}: {e}{Colors.ENDC}")
            self.stats['errors'] += 1
            return None
        except Exception as e:
            print(f"{Colors.WARNING}Warning: Error reading {nfo_path}: {e}{Colors.ENDC}")
            self.stats['errors'] += 1
            return None
    
    def clean_sources(self, root: ET.Element) -> Tuple[bool, int, int]:
        """
        Clean up sources element in the NFO.
        
        Args:
            root: Root element of the NFO
            
        Returns:
            Tuple of (was_modified, sources_removed_count, attributes_removed_count)
        """
        sources_elem = root.find('sources')
        if sources_elem is None:
            return False, 0, 0
        
        was_modified = False
        sources_removed = 0
        attributes_removed = 0
        
        # Track URLs and their properties
        url_data = defaultdict(list)
        
        # Collect all URL elements
        url_elements = sources_elem.findall('url')
        
        # Group URLs by their text content
        for url_elem in url_elements:
            if url_elem.text:
                url_text = url_elem.text.strip()
                url_data[url_text].append(url_elem)
        
        # Process each unique URL
        for url_text, elements in url_data.items():
            if len(elements) > 1:
                # Handle duplicates
                # Check if any have failed=true
                failed_elem = None
                search_elem = None
                other_elem = None
                
                for elem in elements:
                    if elem.get('failed') == 'true':
                        failed_elem = elem
                    elif elem.get('search') == 'true':
                        search_elem = elem
                    else:
                        other_elem = elem
                
                # Keep the most informative version
                # Priority: failed > search > other
                if failed_elem is not None:
                    keep_elem = failed_elem
                elif search_elem is not None:
                    keep_elem = search_elem
                else:
                    keep_elem = other_elem or elements[0]
                
                # Remove duplicates
                for elem in elements:
                    if elem != keep_elem:
                        sources_elem.remove(elem)
                        sources_removed += 1
                        was_modified = True
                
                # Clean attributes from the kept element
                for attr in ['index', 'channel']:
                    if attr in keep_elem.attrib:
                        del keep_elem.attrib[attr]
                        attributes_removed += 1
                        was_modified = True
            else:
                # Single URL - just clean attributes
                elem = elements[0]
                for attr in ['index', 'channel']:
                    if attr in elem.attrib:
                        del elem.attrib[attr]
                        attributes_removed += 1
                        was_modified = True
        
        return was_modified, sources_removed, attributes_removed
    
    def write_nfo(self, nfo_path: Path, tree: ET.ElementTree) -> None:
        """Write NFO file with pretty printing."""
        root = tree.getroot()
        
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
    
    def process_nfo(self, nfo_path: Path) -> None:
        """
        Process a single NFO file.
        
        Args:
            nfo_path: Path to NFO file
        """
        tree = self.parse_nfo(nfo_path)
        if not tree:
            return
        
        root = tree.getroot()
        was_modified, sources_removed, attributes_removed = self.clean_sources(root)
        
        if was_modified:
            relative_path = nfo_path.relative_to(self.parent_dir)
            
            if sources_removed > 0 or attributes_removed > 0:
                print(f"\n{Colors.CYAN}Processing: {relative_path}{Colors.ENDC}")
                
                if sources_removed > 0:
                    print(f"  {Colors.WARNING}Removed {sources_removed} duplicate source(s){Colors.ENDC}")
                    self.stats['sources_removed'] += sources_removed
                
                if attributes_removed > 0:
                    print(f"  {Colors.WARNING}Removed {attributes_removed} attribute(s){Colors.ENDC}")
                    self.stats['attributes_removed'] += attributes_removed
            
            if not self.dry_run:
                # Write the modified file
                self.write_nfo(nfo_path, tree)
                print(f"  {Colors.GREEN}✓ File updated{Colors.ENDC}")
            else:
                print(f"  {Colors.BLUE}[DRY RUN] Would update file{Colors.ENDC}")
            
            self.stats['files_modified'] += 1
        
        self.stats['files_processed'] += 1
    
    def show_example_before_after(self) -> None:
        """Show an example of what the cleaning does."""
        print(f"\n{Colors.HEADER}Example of cleaning:{Colors.ENDC}")
        print(f"\n{Colors.WARNING}BEFORE:{Colors.ENDC}")
        print("""<sources>
    <url ts="2024-01-15T10:30:00" index="1">https://youtube.com/watch?v=abc123</url>
    <url ts="2024-01-15T10:35:00" failed="true">https://youtube.com/watch?v=abc123</url>
    <url ts="2024-01-15T10:40:00" search="true" channel="UC123">https://youtube.com/watch?v=xyz789</url>
    <url ts="2024-01-15T10:45:00" index="2">https://youtube.com/watch?v=xyz789</url>
</sources>""")
        
        print(f"\n{Colors.GREEN}AFTER:{Colors.ENDC}")
        print("""<sources>
    <url ts="2024-01-15T10:35:00" failed="true">https://youtube.com/watch?v=abc123</url>
    <url ts="2024-01-15T10:40:00" search="true">https://youtube.com/watch?v=xyz789</url>
</sources>""")
        print("\nChanges:")
        print("- Kept failed version of abc123 (removed duplicate)")
        print("- Kept search version of xyz789 (removed duplicate)")
        print("- Removed 'index' and 'channel' attributes")
    
    def run(self) -> None:
        """Run the cleaning process."""
        # Show example if requested
        if self.dry_run:
            self.show_example_before_after()
        
        # Find all NFO files
        self.find_nfo_files()
        
        if not self.nfo_files:
            print(f"{Colors.FAIL}No NFO files found in {self.parent_dir}{Colors.ENDC}")
            return
        
        # Process each file
        print(f"\n{Colors.HEADER}Processing NFO files...{Colors.ENDC}")
        
        for nfo_file in self.nfo_files:
            self.process_nfo(nfo_file)
        
        # Print summary
        self.print_summary()
    
    def print_summary(self) -> None:
        """Print processing summary."""
        print(f"\n{Colors.HEADER}{Colors.BOLD}Processing Summary:{Colors.ENDC}")
        print("=" * 60)
        print(f"Files found:        {self.stats['files_found']}")
        print(f"Files processed:    {self.stats['files_processed']}")
        print(f"Files modified:     {Colors.GREEN if self.stats['files_modified'] > 0 else ''}{self.stats['files_modified']}{Colors.ENDC}")
        print(f"Sources removed:    {Colors.WARNING if self.stats['sources_removed'] > 0 else ''}{self.stats['sources_removed']}{Colors.ENDC}")
        print(f"Attributes removed: {Colors.WARNING if self.stats['attributes_removed'] > 0 else ''}{self.stats['attributes_removed']}{Colors.ENDC}")
        print(f"Errors:            {Colors.FAIL if self.stats['errors'] > 0 else ''}{self.stats['errors']}{Colors.ENDC}")
        
        if self.dry_run:
            print(f"\n{Colors.BLUE}This was a DRY RUN - no files were actually modified{Colors.ENDC}")
            print(f"Run without --dry-run to apply changes")
        print("=" * 60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Music Video NFO Source Cleaner - Clean duplicate sources and unwanted attributes',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This tool cleans up <sources> elements in NFO files by:
  • Removing duplicate URLs (keeping failed versions when present)
  • Removing 'index' and 'channel' attributes
  • Preserving unique URLs with 'search=true' attribute

Examples:
  %(prog)s /media/MusicVideos
  %(prog)s /media/MusicVideos --dry-run
  %(prog)s ./videos --verbose
        """
    )
    
    parser.add_argument(
        'directory',
        help='Parent directory to search for NFO files'
    )
    
    parser.add_argument(
        '-d', '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show detailed processing information'
    )
    
    args = parser.parse_args()
    
    # Validate directory
    if not os.path.isdir(args.directory):
        print(f"{Colors.FAIL}Error: Directory not found: {args.directory}{Colors.ENDC}")
        sys.exit(1)
    
    # Create cleaner instance
    cleaner = NfoSourceCleaner(args.directory, args.dry_run)
    
    # Run the process
    cleaner.run()


if __name__ == '__main__':
    main()