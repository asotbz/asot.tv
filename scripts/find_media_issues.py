import os
import argparse
from collections import defaultdict

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

if __name__ == "__main__":
    main()