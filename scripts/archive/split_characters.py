import json
import os
import shutil

# Paths
INPUT_FILE = 'data/build/characters.json'
OUTPUT_DIR = 'frontend/public/data'
CHARS_DIR = os.path.join(OUTPUT_DIR, 'chars')

def optimize_data():
    if not os.path.exists(INPUT_FILE):
        print(f"File not found: {INPUT_FILE}")
        return

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if not os.path.exists(CHARS_DIR):
        os.makedirs(CHARS_DIR)

    lite_data = {}
    graph_data = {} # For relationship graph
    
    print(f"Processing {len(data)} characters...")
    
    for name, char in data.items():
        # 1. Detail File (Full Data)
        char_file = os.path.join(CHARS_DIR, f"{name}.json")
        with open(char_file, 'w', encoding='utf-8') as f:
            json.dump(char, f, ensure_ascii=False)

        # 2. Lite Data (For List & Home)
        # Stripped down heavily
        lite_char = {
            "name": char.get("name"),
            "aliases": char.get("aliases", []),
            "factions": char.get("factions", []),
            "tags": char.get("tags", []),
            "avatar": char.get("avatar"),
            "quotes": char.get("quotes", []), # Keep quotes for Home page
            # Relations: only keep count
            "relationCount": len(char.get("relations", {})),
            "relations": {} # Empty map to satisfy type check if needed, or modify type
        }
        lite_data[name] = lite_char

        # 3. Graph Data (For Relationship Graph Page)
        # Needs name, factions (for color), relations (type & strength)
        # But we only need this for 'Core' characters usually?
        # Let's keep all for now but stripped.
        graph_char = {
            "name": char.get("name"),
            "factions": char.get("factions", []),
            "tags": char.get("tags", []),
            "avatar": char.get("avatar"),
            "relations": {}
        }
        if "relations" in char:
            for target, rel in char["relations"].items():
                graph_char["relations"][target] = {
                    "type": rel.get("type", []),
                    "strength": rel.get("strength", 0)
                }
        graph_data[name] = graph_char

    # Save Lite Data
    lite_file = os.path.join(OUTPUT_DIR, 'characters_lite.json')
    with open(lite_file, 'w', encoding='utf-8') as f:
        json.dump(lite_data, f, ensure_ascii=False)
    
    # Save Graph Data
    graph_file = os.path.join(OUTPUT_DIR, 'characters_graph.json')
    with open(graph_file, 'w', encoding='utf-8') as f:
        json.dump(graph_data, f, ensure_ascii=False)
    
    # Check sizes
    orig_size = os.path.getsize(INPUT_FILE) / (1024*1024)
    lite_size = os.path.getsize(lite_file) / (1024*1024)
    graph_size = os.path.getsize(graph_file) / (1024*1024)
    
    print(f"Original Size: {orig_size:.2f} MB")
    print(f"Lite Size:     {lite_size:.2f} MB (-{(1 - lite_size/orig_size)*100:.1f}%)")
    print(f"Graph Size:    {graph_size:.2f} MB")

if __name__ == "__main__":
    optimize_data()
