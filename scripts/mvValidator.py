#!/usr/bin/env python3
"""
mvValidator.py - Music Video Directory Structure Validator

Recursively validates music video directory structure and reports issues.
Designed to be modular and extensible for adding new validation rules.
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict
from abc import ABC, abstractmethod

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


class ValidationRule(ABC):
    """Abstract base class for validation rules."""
    
    @abstractmethod
    def validate(self, file_system: 'FileSystemSnapshot') -> List[str]:
        """
        Validate the file system and return list of issues found.
        
        Args:
            file_system: Snapshot of the file system to validate
            
        Returns:
            List of issue descriptions
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Return the name of this validation rule."""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """Return a description of what this rule validates."""
        pass


class FileSystemSnapshot:
    """Snapshot of the file system structure for validation."""
    
    def __init__(self, base_path: Path):
        """
        Create a snapshot of the file system.
        
        Args:
            base_path: Base path to scan
        """
        self.base_path = base_path
        self.video_files = []  # List of .mp4 files
        self.nfo_files = []    # List of .nfo files
        self.artist_nfo_files = []  # List of artist.nfo files
        self.artist_directories = set()  # Set of artist directory paths
        self.other_files = []  # List of other files
        self.all_directories = set()  # All directories found
        
        self._scan_directory()
    
    def _scan_directory(self):
        """Scan the directory and categorize files."""
        for root, dirs, files in os.walk(self.base_path):
            root_path = Path(root)
            
            # Track all directories
            self.all_directories.add(root_path)
            
            # Check if this is potentially an artist directory
            # (direct child of base_path)
            if root_path.parent == self.base_path:
                self.artist_directories.add(root_path)
            
            for file in files:
                file_path = root_path / file
                
                if file == 'artist.nfo':
                    self.artist_nfo_files.append(file_path)
                elif file.endswith('.nfo'):
                    self.nfo_files.append(file_path)
                elif file.endswith('.mp4'):
                    self.video_files.append(file_path)
                else:
                    # Any other file type
                    self.other_files.append(file_path)


class OrphanNfoRule(ValidationRule):
    """Check for NFO files without matching MP4 files."""
    
    def get_name(self) -> str:
        return "Orphan NFO Files"
    
    def get_description(self) -> str:
        return "NFO files without matching MP4 video files"
    
    def validate(self, file_system: FileSystemSnapshot) -> List[str]:
        issues = []
        
        # Create a set of video file stems (without extension)
        video_stems = set()
        for video_path in file_system.video_files:
            # Get the full path without extension
            stem_path = video_path.parent / video_path.stem
            video_stems.add(str(stem_path))
        
        # Check each NFO file
        for nfo_path in file_system.nfo_files:
            # Get the full path without extension
            stem_path = nfo_path.parent / nfo_path.stem
            
            # Check if there's a matching video file
            if str(stem_path) not in video_stems:
                relative_path = nfo_path.relative_to(file_system.base_path)
                issues.append(f"NFO without video: {relative_path}")
        
        return issues


class OrphanVideoRule(ValidationRule):
    """Check for MP4 files without matching NFO files."""
    
    def get_name(self) -> str:
        return "Orphan Video Files"
    
    def get_description(self) -> str:
        return "MP4 video files without matching NFO metadata files"
    
    def validate(self, file_system: FileSystemSnapshot) -> List[str]:
        issues = []
        
        # Create a set of NFO file stems (without extension)
        nfo_stems = set()
        for nfo_path in file_system.nfo_files:
            # Get the full path without extension
            stem_path = nfo_path.parent / nfo_path.stem
            nfo_stems.add(str(stem_path))
        
        # Check each video file
        for video_path in file_system.video_files:
            # Get the full path without extension
            stem_path = video_path.parent / video_path.stem
            
            # Check if there's a matching NFO file
            if str(stem_path) not in nfo_stems:
                relative_path = video_path.relative_to(file_system.base_path)
                issues.append(f"Video without NFO: {relative_path}")
        
        return issues


class MissingArtistNfoRule(ValidationRule):
    """Check for artist directories without artist.nfo files."""
    
    def get_name(self) -> str:
        return "Missing Artist NFO"
    
    def get_description(self) -> str:
        return "Artist directories without artist.nfo metadata files"
    
    def validate(self, file_system: FileSystemSnapshot) -> List[str]:
        issues = []
        
        # Get directories that contain artist.nfo files
        artist_nfo_dirs = set()
        for artist_nfo_path in file_system.artist_nfo_files:
            artist_nfo_dirs.add(artist_nfo_path.parent)
        
        # Check each artist directory
        for artist_dir in file_system.artist_directories:
            if artist_dir not in artist_nfo_dirs:
                # Check if this directory has any video files (to avoid false positives)
                has_videos = any(
                    video_path.parent.is_relative_to(artist_dir) or video_path.parent == artist_dir
                    for video_path in file_system.video_files
                )
                
                if has_videos:
                    relative_path = artist_dir.relative_to(file_system.base_path)
                    issues.append(f"Artist directory without artist.nfo: {relative_path}")
        
        return issues


class UnexpectedFilesRule(ValidationRule):
    """Check for unexpected file types in the directory structure."""
    
    def get_name(self) -> str:
        return "Unexpected Files"
    
    def get_description(self) -> str:
        return "Files that are not MP4 videos or NFO metadata files"
    
    def validate(self, file_system: FileSystemSnapshot) -> List[str]:
        issues = []
        
        # Group other files by extension
        files_by_ext = defaultdict(list)
        for file_path in file_system.other_files:
            ext = file_path.suffix.lower()
            files_by_ext[ext].append(file_path)
        
        # Report files grouped by extension
        for ext, files in sorted(files_by_ext.items()):
            # Show first few examples of each type
            examples = files[:3]
            for file_path in examples:
                relative_path = file_path.relative_to(file_system.base_path)
                issues.append(f"Unexpected file ({ext or 'no extension'}): {relative_path}")
            
            # If there are more, add a summary
            if len(files) > 3:
                remaining = len(files) - 3
                issues.append(f"  ... and {remaining} more {ext or 'no extension'} files")
        
        return issues


class EmptyDirectoriesRule(ValidationRule):
    """Check for empty directories."""
    
    def get_name(self) -> str:
        return "Empty Directories"
    
    def get_description(self) -> str:
        return "Directories that contain no files"
    
    def validate(self, file_system: FileSystemSnapshot) -> List[str]:
        issues = []
        
        # Track directories with files
        dirs_with_files = set()
        
        # Add parent directories of all files
        all_files = (file_system.video_files + file_system.nfo_files + 
                    file_system.artist_nfo_files + file_system.other_files)
        
        for file_path in all_files:
            # Add all parent directories up to base_path
            current = file_path.parent
            while current != file_system.base_path.parent:
                dirs_with_files.add(current)
                current = current.parent
        
        # Find empty directories
        for directory in file_system.all_directories:
            if directory not in dirs_with_files and directory != file_system.base_path:
                relative_path = directory.relative_to(file_system.base_path)
                issues.append(f"Empty directory: {relative_path}")
        
        return issues


class DuplicateVideosRule(ValidationRule):
    """Check for potential duplicate video files based on filename similarity."""
    
    def get_name(self) -> str:
        return "Potential Duplicate Videos"
    
    def get_description(self) -> str:
        return "Video files with very similar names that might be duplicates"
    
    def validate(self, file_system: FileSystemSnapshot) -> List[str]:
        issues = []
        
        # Group videos by normalized name
        videos_by_name = defaultdict(list)
        
        for video_path in file_system.video_files:
            # Normalize the filename for comparison
            name = video_path.stem.lower()
            # Remove common variations
            name = name.replace('_', '').replace('-', '').replace(' ', '')
            name = name.replace('remastered', '').replace('hd', '')
            name = name.replace('official', '').replace('video', '')
            
            videos_by_name[name].append(video_path)
        
        # Find groups with multiple videos
        for name, videos in videos_by_name.items():
            if len(videos) > 1:
                for video_path in videos:
                    relative_path = video_path.relative_to(file_system.base_path)
                    issues.append(f"Potential duplicate: {relative_path}")
        
        return issues


class MusicVideoValidator:
    """Main validator class that runs all validation rules."""
    
    def __init__(self, base_path: str, verbose: bool = False):
        """
        Initialize the validator.
        
        Args:
            base_path: Base directory to validate
            verbose: Show verbose output
        """
        self.base_path = Path(base_path)
        self.verbose = verbose
        self.rules = []
        self.stats = defaultdict(int)
        
        # Register default rules
        self._register_default_rules()
    
    def _register_default_rules(self):
        """Register the default validation rules."""
        self.add_rule(OrphanNfoRule())
        self.add_rule(OrphanVideoRule())
        self.add_rule(MissingArtistNfoRule())
        self.add_rule(UnexpectedFilesRule())
        self.add_rule(EmptyDirectoriesRule())
        # DuplicateVideosRule can be added optionally as it might be noisy
    
    def add_rule(self, rule: ValidationRule):
        """
        Add a validation rule.
        
        Args:
            rule: ValidationRule instance to add
        """
        self.rules.append(rule)
    
    def remove_rule(self, rule_name: str):
        """
        Remove a validation rule by name.
        
        Args:
            rule_name: Name of the rule to remove
        """
        self.rules = [r for r in self.rules if r.get_name() != rule_name]
    
    def validate(self) -> Dict[str, List[str]]:
        """
        Run all validation rules and return results.
        
        Returns:
            Dictionary mapping rule names to lists of issues
        """
        print(f"\n{Colors.HEADER}Scanning directory: {self.base_path}{Colors.ENDC}")
        
        # Create file system snapshot
        file_system = FileSystemSnapshot(self.base_path)
        
        # Print scan summary
        print(f"\n{Colors.CYAN}Scan Summary:{Colors.ENDC}")
        print(f"  Video files (.mp4): {len(file_system.video_files)}")
        print(f"  NFO files: {len(file_system.nfo_files)}")
        print(f"  Artist NFO files: {len(file_system.artist_nfo_files)}")
        print(f"  Other files: {len(file_system.other_files)}")
        print(f"  Artist directories: {len(file_system.artist_directories)}")
        
        # Run each validation rule
        results = {}
        print(f"\n{Colors.HEADER}Running validation rules...{Colors.ENDC}")
        
        for rule in self.rules:
            if self.verbose:
                print(f"\nChecking: {rule.get_name()}")
                print(f"  {rule.get_description()}")
            
            issues = rule.validate(file_system)
            results[rule.get_name()] = issues
            self.stats[rule.get_name()] = len(issues)
            
            if self.verbose and issues:
                for issue in issues[:5]:  # Show first 5 issues in verbose mode
                    print(f"    {Colors.WARNING}• {issue}{Colors.ENDC}")
                if len(issues) > 5:
                    print(f"    ... and {len(issues) - 5} more")
        
        return results
    
    def print_report(self, results: Dict[str, List[str]]):
        """
        Print a formatted report of validation results.
        
        Args:
            results: Dictionary of validation results
        """
        print(f"\n{Colors.HEADER}{Colors.BOLD}Validation Report{Colors.ENDC}")
        print("=" * 70)
        
        total_issues = sum(len(issues) for issues in results.values())
        
        if total_issues == 0:
            print(f"\n{Colors.GREEN}✓ No issues found! Directory structure is valid.{Colors.ENDC}")
        else:
            print(f"\n{Colors.WARNING}Found {total_issues} total issue(s){Colors.ENDC}")
            
            for rule_name, issues in results.items():
                if issues:
                    print(f"\n{Colors.CYAN}{rule_name}:{Colors.ENDC} {Colors.FAIL}{len(issues)} issue(s){Colors.ENDC}")
                    
                    # Show all issues (or limit if too many)
                    display_limit = 10 if not self.verbose else len(issues)
                    for i, issue in enumerate(issues[:display_limit], 1):
                        print(f"  {i}. {issue}")
                    
                    if len(issues) > display_limit:
                        remaining = len(issues) - display_limit
                        print(f"  ... and {remaining} more (use --verbose to see all)")
        
        print("\n" + "=" * 70)
        
        # Summary statistics
        print(f"\n{Colors.HEADER}Summary by Rule:{Colors.ENDC}")
        for rule in self.rules:
            rule_name = rule.get_name()
            count = self.stats[rule_name]
            if count == 0:
                status = f"{Colors.GREEN}✓ PASS{Colors.ENDC}"
            else:
                status = f"{Colors.FAIL}✗ FAIL ({count}){Colors.ENDC}"
            print(f"  {rule_name}: {status}")
    
    def export_report(self, results: Dict[str, List[str]], output_file: str):
        """
        Export validation results to a text file.
        
        Args:
            results: Dictionary of validation results
            output_file: Path to output file
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("Music Video Directory Validation Report\n")
            f.write("=" * 70 + "\n")
            f.write(f"Directory: {self.base_path}\n")
            f.write(f"Date: {os.popen('date').read().strip()}\n")
            f.write("=" * 70 + "\n\n")
            
            total_issues = sum(len(issues) for issues in results.values())
            f.write(f"Total Issues Found: {total_issues}\n\n")
            
            for rule_name, issues in results.items():
                if issues:
                    f.write(f"\n{rule_name}: {len(issues)} issue(s)\n")
                    f.write("-" * 40 + "\n")
                    for i, issue in enumerate(issues, 1):
                        f.write(f"{i}. {issue}\n")
            
            f.write("\n" + "=" * 70 + "\n")
            f.write("End of Report\n")
        
        print(f"\n{Colors.GREEN}Report exported to: {output_file}{Colors.ENDC}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Music Video Directory Structure Validator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This tool validates the structure of a music video directory, checking for:
  • NFO files without matching video files
  • Video files without matching NFO metadata
  • Artist directories missing artist.nfo files
  • Unexpected file types in the directory structure
  • Empty directories
  
The tool is modular and extensible - new validation rules can be easily added.

Examples:
  %(prog)s /media/MusicVideos
  %(prog)s /media/MusicVideos --verbose
  %(prog)s ./videos --export-report validation_report.txt
  %(prog)s ./videos --check-duplicates
        """
    )
    
    parser.add_argument(
        'directory',
        help='Parent directory to validate'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show verbose output with more details'
    )
    
    parser.add_argument(
        '-e', '--export-report',
        metavar='FILE',
        help='Export validation report to a text file'
    )
    
    parser.add_argument(
        '-d', '--check-duplicates',
        action='store_true',
        help='Also check for potential duplicate videos'
    )
    
    parser.add_argument(
        '--no-empty-check',
        action='store_true',
        help='Skip checking for empty directories'
    )
    
    args = parser.parse_args()
    
    # Validate directory exists
    if not os.path.isdir(args.directory):
        print(f"{Colors.FAIL}Error: Directory not found: {args.directory}{Colors.ENDC}")
        sys.exit(1)
    
    # Create validator
    validator = MusicVideoValidator(args.directory, verbose=args.verbose)
    
    # Add optional duplicate checking
    if args.check_duplicates:
        validator.add_rule(DuplicateVideosRule())
    
    # Remove empty directory check if requested
    if args.no_empty_check:
        validator.remove_rule("Empty Directories")
    
    # Run validation
    results = validator.validate()
    
    # Print report
    validator.print_report(results)
    
    # Export report if requested
    if args.export_report:
        validator.export_report(results, args.export_report)
    
    # Exit with error code if issues found
    total_issues = sum(len(issues) for issues in results.values())
    sys.exit(1 if total_issues > 0 else 0)


if __name__ == '__main__':
    main()