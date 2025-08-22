import os
import xml.etree.ElementTree as ET

def find_nfo_files(root_dir):
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.lower().endswith('.nfo'):
                yield os.path.join(dirpath, filename)

def move_source_to_sources(tree):
    root = tree.getroot()
    mv = root.find('musicvideo')
    if mv is None:
        return False

    source = mv.find('source')
    if source is None or len(source) == 0:
        return False

    # Move all subelements under <sources>, deduplicate <url> by text only
    sources_elem = ET.Element('sources')
    url_map = {}
    other_elems = []
    for child in list(source):
        if child.tag == 'url':
            url_text = (child.text or '').strip()
            ts = child.attrib.get('ts', '')
            if url_text in url_map:
                # Keep the one with the most recent ts
                prev_ts = url_map[url_text].attrib.get('ts', '')
                if ts > prev_ts:
                    url_map[url_text] = child
            else:
                url_map[url_text] = child
        else:
            other_elems.append(child)

    # Sort <url> elements by ts ascending and assign index
    url_elems_sorted = sorted(
        url_map.values(),
        key=lambda e: e.attrib.get('ts', '')
    )
    for idx, url_elem in enumerate(url_elems_sorted):
        url_elem.attrib['index'] = str(idx)
        sources_elem.append(url_elem)
        source.remove(url_elem)
    # Add other subelements
    for elem in other_elems:
        sources_elem.append(elem)
        source.remove(elem)

    # Remove <source> and add <sources>
    if source in mv:
        mv.remove(source)
    mv.append(sources_elem)
    return True

def process_nfo_file(path):
    try:
        tree = ET.parse(path)
        changed = move_source_to_sources(tree)

        # Handle <premiered> -> <year>
        root = tree.getroot()
        mv = root.find('musicvideo')
        if mv is not None:
            premiered = mv.find('premiered')
            if premiered is not None and premiered.text:
                year_text = premiered.text.strip().split('-')[0]
                year_elem = ET.Element('year')
                year_elem.text = year_text
                mv.remove(premiered)
                mv.append(year_elem)
                changed = True

        if changed:
            tree.write(path, encoding='utf-8', xml_declaration=True)
            print(f"Updated: {path}")
        else:
            print(f"No changes: {path}")
    except Exception as e:
        print(f"Error processing {path}: {e}")

def main():
    import sys
    if len(sys.argv) != 2:
        print("Usage: python convert_nfo_sources.py <parent_directory>")
        return
    parent_dir = sys.argv[1]
    for nfo_path in find_nfo_files(parent_dir):
        process_nfo_file(nfo_path)

if __name__ == "__main__":
    main()