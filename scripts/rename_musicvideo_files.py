import argparse
import os
import sys
import shutil
import unicodedata
import xml.etree.ElementTree as ET

def log(msg):
    print(msg)

def error(msg):
    print(f"ERROR: {msg}", file=sys.stderr)

def normalize(text):
    # Replace spaces with underscores
    text = text.replace(' ', '_')
    # Convert to lowercase
    text = text.lower()
    # Remove diacritics
    text = unicodedata.normalize('NFKD', text)
    text = ''.join(c for c in text if not unicodedata.combining(c))
    # Remove non-alphanumeric (keep underscores)
    text = ''.join(c for c in text if c.isalnum() or c == '_')
    return text

def find_nfo_files(parent_dir):
    nfo_files = []
    for root, dirs, files in os.walk(parent_dir):
        for file in files:
            if file.lower().endswith('.nfo'):
                nfo_files.append(os.path.join(root, file))
    return nfo_files

def remove_empty_dirs(parent_dir):
    for root, dirs, files in os.walk(parent_dir, topdown=False):
        for d in dirs:
            dir_path = os.path.join(root, d)
            if not os.listdir(dir_path):
                log(f"Removing empty directory: {dir_path}")
                os.rmdir(dir_path)

def main():
    parser = argparse.ArgumentParser(description="Rename musicvideo files based on NFO metadata.")
    parser.add_argument('--dir', required=True, help='Parent directory to search')
    parser.add_argument('--dry-run', action='store_true', help='Only print changes, do not perform them')
    args = parser.parse_args()

    parent_dir = args.dir
    dry_run = args.dry_run

    nfo_files = find_nfo_files(parent_dir)
    if not nfo_files:
        log("No .nfo files found.")
        sys.exit(0)

    for nfo_path in nfo_files:
        base_dir = os.path.dirname(nfo_path)
        base_name = os.path.splitext(os.path.basename(nfo_path))[0]

        try:
            tree = ET.parse(nfo_path)
            root = tree.getroot()
        except Exception as e:
            error(f"Failed to parse XML in {nfo_path}: {e}")
            sys.exit(1)

        if root.tag != 'musicvideo':
            error(f"<musicvideo> element missing in {nfo_path}")
            sys.exit(1)

        artist = root.findtext('artist')
        title = root.findtext('title')

        if not artist or not title:
            error(f"<artist> or <title> missing/null in {nfo_path}")
            sys.exit(1)

        norm_artist = normalize(artist)
        norm_title = normalize(title)
        new_dir = os.path.join(parent_dir, norm_artist)
        new_base = os.path.join(new_dir, norm_title)

        # Find .mp4 file with same base name
        mp4_path = os.path.join(base_dir, base_name + '.mp4')
        if not os.path.isfile(mp4_path):
            error(f".mp4 file not found for {nfo_path}, expected: {mp4_path}")
            sys.exit(1)

        new_mp4_path = new_base + '.mp4'
        new_nfo_path = new_base + '.nfo'

        # Check for collisions
        if os.path.exists(new_mp4_path):
            error(f"File collision: {new_mp4_path} already exists.")
            sys.exit(1)
        if os.path.exists(new_nfo_path):
            error(f"File collision: {new_nfo_path} already exists.")
            sys.exit(1)

        log(f"Moving {mp4_path} -> {new_mp4_path}")
        log(f"Moving {nfo_path} -> {new_nfo_path}")

        if not dry_run:
            os.makedirs(new_dir, exist_ok=True)
            shutil.move(mp4_path, new_mp4_path)
            shutil.move(nfo_path, new_nfo_path)

    remove_empty_dirs(parent_dir)

if __name__ == '__main__':
    main()