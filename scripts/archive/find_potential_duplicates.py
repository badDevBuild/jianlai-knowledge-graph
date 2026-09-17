
import json
import os
import difflib


import glob

DATA_DIR = 'data/build/profiles_v3'

def load_v3_data():
    data = {}
    files = glob.glob(os.path.join(DATA_DIR, '*.json'))
    print(f"Loading {len(files)} profile files from {DATA_DIR}...")
    
    for filepath in files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                profile = json.load(f)
                name = profile.get('name')
                if name:
                    data[name] = profile
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
            
    return data

def find_duplicates():
    print("Loading V3 data...")
    data = load_v3_data()
    
    names = list(data.keys())
    # Pre-process: Create a map of Alias -> List of Names who have this alias
    alias_map = {}
    for name, info in data.items():
        aliases = info.get('aliases', [])
        # Also treat the name itself as an alias for matching purposes
        all_identifiers = set(aliases)
        all_identifiers.add(name)
        
        for alias in all_identifiers:
            if not alias or len(alias) < 2: continue # distinct chars only
            if alias not in alias_map:
                alias_map[alias] = []
            alias_map[alias].append(name)

    potential_dupes = []
    processed_pairs = set()

    print(f"Scanning {len(names)} characters for duplicates...")

    # Strategy 1: Shared Identifiers (Name/Alias Overlap)
    # If two characters share an alias, or one's name is the other's alias
    for identifier, char_list in alias_map.items():
        if len(char_list) > 1:
            # We found multiple characters sharing the same identifier
            # e.g. identifier="白泽", chars=["白泽", "白老爷"] (assuming "白泽" is in "白老爷"'s aliases or vice versa)
            
            # Add all pairs in this list
            for i in range(len(char_list)):
                for j in range(i + 1, len(char_list)):
                    c1, c2 = char_list[i], char_list[j]
                    if c1 > c2: c1, c2 = c2, c1 # normalize order
                    
                    if (c1, c2) not in processed_pairs:
                        # Calculate confidence
                        reason = f"Shared identifier: '{identifier}'"
                        # Refine reason
                        info1 = data[c1]
                        info2 = data[c2]
                        
                        # Strict check: Is strict name match?
                        is_strong = False
                        if c1 in info2.get('aliases', []) or c2 in info1.get('aliases', []):
                            reason = f"Direct Match: One's name is in other's aliases ('{identifier}')"
                            is_strong = True
                        
                        potential_dupes.append({
                            "char_a": c1,
                            "char_b": c2,
                            "reason": reason,
                            "score": 100 if is_strong else 80
                        })
                        processed_pairs.add((c1, c2))

    # Strategy 2: Substring Matching (e.g. 搬山老猿 vs 搬山猿)
    # Only if not already found. This is O(N^2) so we need to be careful. 2200^2 is ~5M, ok for simple string op.
    # To optimize, we only compare if they share at least one character? No.
    # Let's simple nested loop but fast reject.
    
    # Sort names by length to optimize
    sorted_names = sorted(names, key=len, reverse=True)
    
    for i, name_long in enumerate(sorted_names):
        for j in range(i + 1, len(sorted_names)):
            name_short = sorted_names[j]
            
            # If already processed, skip
            p1, p2 = (name_long, name_short) if name_long < name_short else (name_short, name_long)
            if (p1, p2) in processed_pairs:
                continue
                
            # Check for inclusion
            if name_short in name_long and len(name_short) >= 2:
                # Potential match: "搬山猿" inside "搬山老猿"
                # But prevent "书生" matching "楚姓书生" (too generic).
                # Heuristic: Length ratio > 0.6 or absolute diff <= 2 chars
                if len(name_short) / len(name_long) > 0.6:
                     potential_dupes.append({
                        "char_a": name_short,
                        "char_b": name_long,
                        "reason": f"Substring Match: '{name_short}' inside '{name_long}'",
                        "score": 60
                    })
                     processed_pairs.add((p1, p2))

    # Sort duplicates by score
    potential_dupes.sort(key=lambda x: x['score'], reverse=True)

    # Output
    print(f"\nFound {len(potential_dupes)} potential duplicate pairs.\n")
    
    # Save to file for review
    with open('duplicate_report.json', 'w', encoding='utf-8') as f:
        json.dump(potential_dupes, f, ensure_ascii=False, indent=2)
        
    # Print Top 20 for CLI
    for item in potential_dupes[:30]:
        print(f"[{item['score']}] {item['char_a']} <--> {item['char_b']} ({item['reason']})")

if __name__ == "__main__":
    find_duplicates()
