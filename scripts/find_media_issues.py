import os
import argparse
from collections import defaultdict
import shutil

def find_mp4_without_nfo(root):
    missing_nfo = []
    for dirpath, _, filenames in os.walk(root):
        mp4_files = [f for f in filenames if f.lower().endswith('.mp4')]
        nfo_files = set(f.lower() for f in filenames if f.lower().endswith('.nfo'))
        for mp4 in mp4_files:
            base = os.path.splitext(mp4)[0].lower()
            nfo_name = base + '.nfo'
            if nfo_name not in nfo_files:
                missing_nfo.append(os.path.join(dirpath, mp4))
    return missing_nfo

def find_nfo_without_mp4(root):
    orphan_nfo = []
    for dirpath, _, filenames in os.walk(root):
        nfo_files = [f for f in filenames if f.lower().endswith('.nfo')]
        mp4_files = set(os.path.splitext(f)[0].lower() for f in filenames if f.lower().endswith('.mp4'))
        for nfo in nfo_files:
            base = os.path.splitext(nfo)[0].lower()
            if base not in mp4_files:
                orphan_nfo.append(os.path.join(dirpath, nfo))
    return orphan_nfo

def find_duplicate_mp4_titles(root):
    title_map = defaultdict(list)
    for dirpath, _, filenames in os.walk(root):
        for fname in filenames:
            if fname.lower().endswith('.mp4'):
                title = os.path.splitext(fname)[0].lower()
                title_map[title].append(os.path.join(dirpath, fname))
    duplicates = {title: files for title, files in title_map.items() if len(files) > 1}
    return duplicates

def main():
    parser = argparse.ArgumentParser(description="Find media issues in a directory tree.")
    parser.add_argument("parent_dir", help="Parent directory to search")
    args = parser.parse_args()

    print("Searching for mp4 files missing .nfo...")
    missing_nfo = find_mp4_without_nfo(args.parent_dir)
    if missing_nfo:
        print("\nMP4 files missing .nfo:")
        for path in missing_nfo:
            print(path)
    else:
        print("\nNo mp4 files missing .nfo found.")

    print("\nSearching for .nfo files without matching .mp4...")
    orphan_nfo = find_nfo_without_mp4(args.parent_dir)
    if orphan_nfo:
        print("\nNFO files without matching .mp4:")
        for path in orphan_nfo:
            print(path)
    else:
        print("\nNo orphan .nfo files found.")

    print("\nSearching for potential duplicate mp4 files (by base name)...")
    duplicates = find_duplicate_mp4_titles(args.parent_dir)
    if duplicates:
        print("\nPotential duplicate mp4 files (by base name):")
        for title, files in duplicates.items():
            print(f"Base name: {title}")
            for f in files:
                print(f"  {f}")
    else:
        print("\nNo duplicate mp4 base names found.")

def remove_album_dirs(parent_dir):
    for artist in os.listdir(parent_dir):
        artist_path = os.path.join(parent_dir, artist)
        if not os.path.isdir(artist_path):
            continue
        for album in os.listdir(artist_path):
            album_path = os.path.join(artist_path, album)
            if not os.path.isdir(album_path):
                continue
            # Move files up to artist directory
            for fname in os.listdir(album_path):
                src = os.path.join(album_path, fname)
                dst = os.path.join(artist_path, fname)
                if os.path.isfile(src):
                    shutil.move(src, dst)
            # Remove album dir if empty
            if not os.listdir(album_path):
                os.rmdir(album_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Find media issues in a directory tree.")
    parser.add_argument("parent_dir", help="Parent directory to search")
    parser.add_argument("--remove-album-dirs", action="store_true", help="Move files out of album dirs and remove empty dirs")
    args = parser.parse_args()

    if args.remove_album_dirs:
        print("Removing album directories and moving files up one level...")
        remove_album_dirs(args.parent_dir)
        print("Album directories processed.\n")

    main()