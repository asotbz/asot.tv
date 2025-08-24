#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
convert_nfo_format.py

Recursively finds .nfo files in a directory and converts them to the new format:
- Moves sources element to be a child of musicvideo element
- Removes empty director, studio, and genre elements
- Pretty prints the XML output

Usage:
  python3 scripts/convert_nfo_format.py --dir /path/to/music/videos
  python3 scripts/convert_nfo_format.py --dir /path/to/music/videos --backup
  python3 scripts/convert_nfo_format.py --dir /path/to/music/videos --dry-run
"""

import argparse
import xml.etree.ElementTree as ET
from pathlib import Path
import shutil
import sys
from typing import List, Optional


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Convert existing .nfo files to new format with sources as child of musicvideo element"
    )
    parser.add_argument(
        "--dir", 
        required=True, 
        help="Parent directory to search for .nfo files"
    )
    parser.add_argument(
        "--backup", 
        action="store_true", 
        help="Create .bak backup files before conversion"
    )
    parser.add_argument(
        "--dry-run", 
        action="store_true", 
        help="Show what would be converted without making changes"
    )
    return parser.parse_args()


def find_nfo_files(directory: Path) -> List[Path]:
    """Recursively find all .nfo files in the directory."""
    return list(directory.rglob("*.nfo"))


def is_empty_element(element: ET.Element) -> bool:
    """Check if an element is empty (no text content or only whitespace)."""
    return not element.text or not element.text.strip()


def needs_conversion(nfo_path: Path) -> tuple[bool, str]:
    """
    Check if an NFO file needs conversion.
    Returns (needs_conversion, reason).
    """
    try:
        # Read the file content to detect multi-root XML (old format)
        with open(nfo_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for multi-root XML (musicvideo and sources as siblings)
        import re
        musicvideo_matches = re.findall(r'<musicvideo>.*?</musicvideo>', content, re.DOTALL)
        sources_matches = re.findall(r'<sources>.*?</sources>', content, re.DOTALL)
        
        if len(musicvideo_matches) == 1 and len(sources_matches) == 1:
            # Old format detected - sources as sibling
            return True, "Old format detected - sources element as sibling"
        
        # Try to parse as normal XML
        tree = ET.parse(nfo_path)
        root = tree.getroot()
        
        if root.tag != "musicvideo":
            return False, "Not a musicvideo NFO file"
        
        # Check if there are empty elements to clean
        empty_elements = []
        for element in root.findall(".//director"):
            if is_empty_element(element):
                empty_elements.append("director")
        for element in root.findall(".//studio"):
            if is_empty_element(element):
                empty_elements.append("studio")
        for element in root.findall(".//genre"):
            if is_empty_element(element):
                empty_elements.append("genre")
        
        if empty_elements:
            return True, f"Empty elements found: {', '.join(set(empty_elements))}"
        
        # Check if XML needs pretty printing (look for indentation)
        if not re.search(r'\n\s\s+<', content):
            return True, "XML needs pretty printing"
        
        return False, "Already in correct format"
        
    except ET.ParseError as e:
        # Could be multi-root XML, check if it has musicvideo
        try:
            with open(nfo_path, 'r', encoding='utf-8') as f:
                content = f.read()
            if '<musicvideo>' in content and '<sources>' in content:
                return True, "Multi-root XML format detected"
            return False, f"XML parse error: {e}"
        except Exception:
            return False, f"XML parse error: {e}"
    except Exception as e:
        return False, f"Error reading file: {e}"


def convert_nfo_file(nfo_path: Path, backup: bool = False) -> tuple[bool, str]:
    """
    Convert a single NFO file to the new format.
    Returns (success, message).
    """
    try:
        # Read the entire file content to handle multi-root XML
        with open(nfo_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse individual XML elements
        musicvideo_root = None
        sources_element = None
        
        # Find musicvideo element
        try:
            # Try to parse as single root element first
            tree = ET.parse(nfo_path)
            root = tree.getroot()
            
            if root.tag == "musicvideo":
                musicvideo_root = root
                # Check if sources is already a child
                existing_sources = root.find("sources")
                if existing_sources is not None:
                    sources_element = existing_sources
            else:
                return False, f"Root element is '{root.tag}', not 'musicvideo'"
                
        except ET.ParseError:
            # Handle multi-root XML (old format)
            import re
            
            # Extract musicvideo element
            mv_match = re.search(r'<musicvideo>.*?</musicvideo>', content, re.DOTALL)
            if mv_match:
                musicvideo_root = ET.fromstring(mv_match.group(0))
            
            # Extract sources element
            sources_match = re.search(r'<sources>.*?</sources>', content, re.DOTALL)
            if sources_match:
                sources_element = ET.fromstring(sources_match.group(0))
        
        if musicvideo_root is None:
            return False, "No musicvideo element found"
        
        # Remove empty director, studio, and genre elements
        elements_removed = []
        for tag in ["director", "studio", "genre"]:
            for element in musicvideo_root.findall(f".//{tag}"):
                if is_empty_element(element):
                    musicvideo_root.remove(element)
                    elements_removed.append(tag)
        
        # Move sources element under musicvideo if it exists and isn't already there
        if sources_element is not None:
            existing_sources = musicvideo_root.find("sources")
            if existing_sources is None:
                # Add sources as last child of musicvideo
                musicvideo_root.append(sources_element)
        
        # Create backup if requested
        if backup:
            backup_path = nfo_path.with_suffix(nfo_path.suffix + ".bak")
            shutil.copy2(nfo_path, backup_path)
        
        # Pretty print the XML
        ET.indent(musicvideo_root, space="  ", level=0)
        
        # Write the converted file
        with open(nfo_path, 'wb') as f:
            f.write(b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n')
            tree = ET.ElementTree(musicvideo_root)
            tree.write(f, encoding="utf-8", xml_declaration=False)
        
        message_parts = ["Converted successfully"]
        if elements_removed:
            message_parts.append(f"removed empty {', '.join(set(elements_removed))} elements")
        if sources_element is not None and musicvideo_root.find("sources") is not None:
            message_parts.append("moved sources under musicvideo")
        
        return True, "; ".join(message_parts)
        
    except Exception as e:
        return False, f"Conversion failed: {e}"


def main() -> None:
    """Main function."""
    args = parse_args()
    
    directory = Path(args.dir).expanduser().resolve()
    if not directory.exists():
        print(f"Directory not found: {directory}", file=sys.stderr)
        sys.exit(1)
    
    if not directory.is_dir():
        print(f"Path is not a directory: {directory}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Searching for .nfo files in: {directory}")
    nfo_files = find_nfo_files(directory)
    
    if not nfo_files:
        print("No .nfo files found.")
        return
    
    print(f"Found {len(nfo_files)} .nfo files")
    
    files_to_convert = []
    for nfo_path in nfo_files:
        needs_conv, reason = needs_conversion(nfo_path)
        if needs_conv:
            files_to_convert.append((nfo_path, reason))
        else:
            if not args.dry_run:
                print(f"SKIP: {nfo_path.relative_to(directory)} - {reason}")
    
    if not files_to_convert:
        print("All files are already in the correct format.")
        return
    
    print(f"\n{len(files_to_convert)} files need conversion:")
    
    converted = 0
    failed = 0
    
    for nfo_path, reason in files_to_convert:
        rel_path = nfo_path.relative_to(directory)
        
        if args.dry_run:
            print(f"WOULD CONVERT: {rel_path} - {reason}")
            continue
        
        success, message = convert_nfo_file(nfo_path, backup=args.backup)
        if success:
            print(f"CONVERTED: {rel_path} - {message}")
            converted += 1
        else:
            print(f"FAILED: {rel_path} - {message}", file=sys.stderr)
            failed += 1
    
    if not args.dry_run:
        print(f"\nConversion complete:")
        print(f"  Converted: {converted}")
        print(f"  Failed: {failed}")
        print(f"  Skipped: {len(nfo_files) - len(files_to_convert)}")
        if args.backup:
            print(f"  Backup files created with .bak extension")
    else:
        print(f"\nDry run complete - {len(files_to_convert)} files would be converted")


if __name__ == "__main__":
    main()