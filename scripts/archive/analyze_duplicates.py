
import json
import os
import glob
from collections import defaultdict

DATA_DIR = 'data/build/profiles_v3'

def analyze():
    print(f"Scanning {DATA_DIR}...")
    files = glob.glob(os.path.join(DATA_DIR, '*.json'))
    
    # 1. Map Name -> List of Files
    # This detects "Critical Collisions" where multiple files claim to be the same character name
    name_collision_map = defaultdict(list)
    
    # 2. Map Alias -> Name
    # This helps detect "Logical Duplicates" (e.g. "Old Scholar" vs "Wen Sheng" if not linked)
    # alias_map = defaultdict(list)

    total_files = 0
    
    for filepath in files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            name = data.get('name')
            if not name:
                continue
            
            # Metrics
            relations = data.get('relations', {})
            rel_count = len(relations)
            bio = data.get('bio', '')
            bio_len = len(bio)
            quotes = data.get('quotes', [])
            quote_count = len(quotes)
            
            info = {
                'path': filepath,
                'filename': os.path.basename(filepath),
                'name': name,
                'rel_count': rel_count,
                'bio_len': bio_len,
                'quote_count': quote_count,
                'size': os.path.getsize(filepath)
            }
            
            name_collision_map[name].append(info)
            total_files += 1
            
        except Exception as e:
            print(f"Error reading {filepath}: {e}")

    print(f"Scanned {total_files} files.")
    
    # Analyze Collisions
    collisions = []
    
    for name, entries in name_collision_map.items():
        if len(entries) > 1:
            # Sort by data quality (approx: relations + bio_len/100)
            entries.sort(key=lambda x: (x['rel_count'] * 100 + x['bio_len']), reverse=True)
            
            collisions.append({
                'name': name,
                'files': entries
            })
            
    # Sort collisions by number of conflicting files
    collisions.sort(key=lambda x: len(x['files']), reverse=True)
    
    print(f"\nFound {len(collisions)} DIRECT NAME COLLISIONS (Critical):\n")
    
    for c in collisions:
        print(f"🔴 Character: {c['name']}")
        for i, f in enumerate(c['files']):
            grade = "WINNER" if i == 0 else "DELETE"
            print(f"   [{grade}] {f['filename']:<30} | Rel: {f['rel_count']:<3} | Bio: {f['bio_len']:<4} | Size: {f['size']}")
        print("-" * 60)

    # Save report
    with open('name_collisions.json', 'w', encoding='utf-8') as f:
        json.dump(collisions, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    analyze()
