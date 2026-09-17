import os
import json
from collections import defaultdict

ROOT_DIR = 'data'

def check_all_files():
    print(f"--- Recursive check of {ROOT_DIR} ---")
    name_map = defaultdict(list)
    file_count = 0
    
    for root, dirs, files in os.walk(ROOT_DIR):
        for filename in files:
            if not filename.endswith('.json'):
                continue
                
            filepath = os.path.join(root, filename)
            file_count += 1
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        name = data.get('name')
                        if name:
                            # Store full path or relative path
                            name_map[name].append(filepath)
            except Exception as e:
                # print(f"Error reading {filename}: {e}")
                pass

    print(f"Scanned {file_count} JSON files.")

    # Report duplicates
    intra_dir_duplicates = defaultdict(list)
    
    for name, files in name_map.items():
        # Group by directory
        dir_map = defaultdict(list)
        for f in files:
            d = os.path.dirname(f)
            dir_map[d].append(f)
            
        for d, f_list in dir_map.items():
            if len(f_list) > 1:
                intra_dir_duplicates[d].append((name, f_list))

    print("\n=== INTRA-DIRECTORY DUPLICATES (Action Required) ===")
    if not intra_dir_duplicates:
        print("No intra-directory duplicates found.")
    else:
        for d, items in intra_dir_duplicates.items():
            print(f"\nDirectory: {d}")
            for name, f_list in items:
                print(f"  Name: '{name}'")
                for f in f_list:
                    print(f"    - {os.path.basename(f)}")
                    
if __name__ == "__main__":
    check_all_files()
