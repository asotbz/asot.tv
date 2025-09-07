#!/usr/bin/env python3
"""
mvNfoExporter.py - Music Video NFO to CSV Exporter

Recursively searches for .nfo files and exports their metadata to CSV format.
Identifies the most recent successful download URL from the sources element.
"""

import argparse
import csv
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

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


class NfoExporter:
    """Export NFO data to CSV format."""
    
    # Define CSV field names based on PRD
    CSV_FIELDS = [
        'year', 'artist', 'title', 'album', 'label', 
        'genre', 'director', 'tag', 'youtube_url'
    ]
    
    def __init__(self, parent_dir: str, output_file: str):
        """
        Initialize the NFO exporter.
        
        Args:
            parent_dir: Parent directory to search for NFO files
            output_file: Output CSV file path
        """
        self.parent_dir = Path(parent_dir)
        self.output_file = output_file
        self.nfo_files = []
        self.stats = {
            'files_found': 0,
            'files_processed': 0,
            'files_exported': 0,
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
    
    def get_element_text(self, root: ET.Element, tag: str) -> str:
        """Get text content of an element, return empty string if not found."""
        elem = root.find(tag)
        return elem.text.strip() if elem is not None and elem.text else ""
    
    def get_tags_list(self, root: ET.Element) -> str:
        """Get all tag elements and return as comma-separated string."""
        tags = []
        for tag_elem in root.findall('tag'):
            if tag_elem.text and tag_elem.text.strip():
                tags.append(tag_elem.text.strip())
        return ', '.join(tags)
    
    def get_most_recent_successful_url(self, root: ET.Element) -> str:
        """
        Find the most recent successful download URL from sources element.
        
        A successful URL is one that doesn't have failed="true" attribute.
        Returns the URL with the most recent timestamp.
        
        Args:
            root: Root element of the NFO
            
        Returns:
            The most recent successful URL or empty string if none found
        """
        sources_elem = root.find('sources')
        if sources_elem is None:
            return ""
        
        successful_urls = []
        
        # Collect all successful URLs with their timestamps
        for url_elem in sources_elem.findall('url'):
            # Skip failed URLs
            if url_elem.get('failed') == 'true':
                continue
            
            url_text = url_elem.text.strip() if url_elem.text else None
            ts_str = url_elem.get('ts', '')
            
            if url_text and ts_str:
                try:
                    # Parse timestamp
                    ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                    successful_urls.append((ts, url_text))
                except ValueError:
                    # If timestamp parsing fails, include without timestamp
                    successful_urls.append((datetime.min, url_text))
            elif url_text:
                # URL without timestamp
                successful_urls.append((datetime.min, url_text))
        
        # Sort by timestamp (most recent first)
        successful_urls.sort(reverse=True)
        
        # Return the most recent successful URL
        return successful_urls[0][1] if successful_urls else ""
    
    def extract_nfo_data(self, nfo_path: Path) -> Optional[Dict[str, str]]:
        """
        Extract data from NFO file.
        
        Args:
            nfo_path: Path to NFO file
            
        Returns:
            Dictionary with CSV field values or None if extraction fails
        """
        tree = self.parse_nfo(nfo_path)
        if not tree:
            return None
        
        root = tree.getroot()
        
        # Extract all fields from NFO
        # Note: 'label' field comes from <studio> element in NFO
        data = {
            'year': self.get_element_text(root, 'year'),
            'artist': self.get_element_text(root, 'artist'),
            'title': self.get_element_text(root, 'title'),
            'album': self.get_element_text(root, 'album'),
            'label': self.get_element_text(root, 'studio'),  # studio element maps to label field
            'genre': self.get_element_text(root, 'genre'),
            'director': self.get_element_text(root, 'director'),
            'tag': self.get_tags_list(root),  # combine multiple tag elements
            'youtube_url': self.get_most_recent_successful_url(root)
        }
        
        # Only include entries that have at least artist and title
        if data['artist'] and data['title']:
            return data
        else:
            print(f"{Colors.WARNING}Skipping {nfo_path}: Missing artist or title{Colors.ENDC}")
            return None
    
    def write_csv(self, data_list: List[Dict[str, str]]) -> None:
        """
        Write data to CSV file with proper escaping for fields containing commas.
        
        The csv.DictWriter automatically handles quoting fields that contain
        special characters like commas, quotes, or newlines.
        
        Args:
            data_list: List of dictionaries containing NFO data
        """
        print(f"\n{Colors.HEADER}Writing CSV file: {self.output_file}{Colors.ENDC}")
        
        try:
            with open(self.output_file, 'w', newline='', encoding='utf-8') as csvfile:
                # Configure the writer with QUOTE_MINIMAL to quote fields only when necessary
                # This ensures fields with commas, quotes, or newlines are properly quoted
                writer = csv.DictWriter(
                    csvfile,
                    fieldnames=self.CSV_FIELDS,
                    quoting=csv.QUOTE_MINIMAL,
                    quotechar='"',
                    escapechar=None,
                    doublequote=True  # Use double quotes to escape quotes within fields
                )
                writer.writeheader()
                writer.writerows(data_list)
            
            print(f"{Colors.GREEN}✓ Successfully wrote {len(data_list)} entries to CSV{Colors.ENDC}")
        except Exception as e:
            print(f"{Colors.FAIL}Error writing CSV file: {e}{Colors.ENDC}")
            sys.exit(1)
    
    def run(self) -> None:
        """Run the export process."""
        # Find all NFO files
        self.find_nfo_files()
        
        if not self.nfo_files:
            print(f"{Colors.FAIL}No NFO files found in {self.parent_dir}{Colors.ENDC}")
            return
        
        # Process each file and collect data
        print(f"\n{Colors.HEADER}Processing NFO files...{Colors.ENDC}")
        
        data_list = []
        for i, nfo_file in enumerate(self.nfo_files, 1):
            # Show progress
            if i % 10 == 0:
                print(f"Progress: {i}/{len(self.nfo_files)} files processed...")
            
            data = self.extract_nfo_data(nfo_file)
            if data:
                data_list.append(data)
                self.stats['files_exported'] += 1
            
            self.stats['files_processed'] += 1
        
        # Sort data by artist and title
        data_list.sort(key=lambda x: (x['artist'].lower(), x['title'].lower()))
        
        # Write to CSV
        if data_list:
            self.write_csv(data_list)
        else:
            print(f"{Colors.WARNING}No valid data found to export{Colors.ENDC}")
        
        # Print summary
        self.print_summary()
    
    def print_summary(self) -> None:
        """Print processing summary."""
        print(f"\n{Colors.HEADER}{Colors.BOLD}Export Summary:{Colors.ENDC}")
        print("=" * 60)
        print(f"Files found:     {self.stats['files_found']}")
        print(f"Files processed: {self.stats['files_processed']}")
        print(f"Files exported:  {Colors.GREEN if self.stats['files_exported'] > 0 else ''}{self.stats['files_exported']}{Colors.ENDC}")
        print(f"Errors:          {Colors.FAIL if self.stats['errors'] > 0 else ''}{self.stats['errors']}{Colors.ENDC}")
        
        if self.stats['files_exported'] > 0:
            print(f"\n{Colors.GREEN}CSV file created: {self.output_file}{Colors.ENDC}")
        print("=" * 60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Music Video NFO to CSV Exporter - Export NFO metadata to CSV format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This tool exports NFO metadata to CSV format with the following fields:
  year, artist, title, album, label, genre, director, tag, youtube_url

The youtube_url field contains the most recent successful download URL
from the <sources> element (URLs without failed="true" attribute).

Examples:
  %(prog)s /media/MusicVideos
  %(prog)s /media/MusicVideos -o collection.csv
  %(prog)s ./videos --output my_videos.csv
        """
    )
    
    parser.add_argument(
        'directory',
        help='Parent directory to search for NFO files'
    )
    
    parser.add_argument(
        '-o', '--output',
        default='music_videos.csv',
        help='Output CSV file name (default: music_videos.csv)'
    )
    
    args = parser.parse_args()
    
    # Validate directory
    if not os.path.isdir(args.directory):
        print(f"{Colors.FAIL}Error: Directory not found: {args.directory}{Colors.ENDC}")
        sys.exit(1)
    
    # Create exporter instance
    exporter = NfoExporter(args.directory, args.output)
    
    # Run the export
    exporter.run()


if __name__ == '__main__':
    main()