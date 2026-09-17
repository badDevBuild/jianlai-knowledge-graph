
import json
import os
import glob

INPUT_DIR = 'data/build/profiles_v3'
OUTPUT_FILE = 'data/build/all_appearances.json'

def extract_appearances():
    files = glob.glob(os.path.join(INPUT_DIR, '*.json'))
    print(f"Scanning {len(files)} profiles...")
    
    appearances = {}
    
    # Load Blocklist
    blocklist = set()
    blocklist_path = "data/build/profile_generation_blocklist.txt"
    if os.path.exists(blocklist_path):
        with open(blocklist_path, 'r', encoding='utf-8') as f:
            blocklist = {line.strip() for line in f if line.strip()}
            print(f"Loaded blocklist with {len(blocklist)} names.")

    for filepath in files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            name = data.get('name')
            
            # Skip if no name
            if not name: continue
            
            # Skip if blocked
            if name in blocklist:
                continue
                
            app = data.get('appearance', {})
            
            # Check if appearance has meaningful content
            has_content = False
            full_text = []
            
            if isinstance(app, dict):
                for key in ['facial', 'physique', 'attire', 'aura']:
                    val = app.get(key)
                    if val and isinstance(val, str) and len(val) > 2:
                        has_content = True
                        if key == 'facial': full_text.append(f"Face: {val}")
                        elif key == 'physique': full_text.append(f"Body: {val}")
                        elif key == 'attire': full_text.append(f"Clothing: {val}")
                        elif key == 'aura': full_text.append(f"Aura: {val}")
            
            if has_content:
                # Add a bit of bio for context if available
                bio = data.get('bio', '')
                if bio:
                    # Take first sentence or first 50 chars for context
                    bio_snippet = bio.split('。')[0]
                    full_text.insert(0, f"Context: {bio_snippet}")
                
                appearances[name] = " ".join(full_text)
                
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
            
    print(f"Extracted appearances for {len(appearances)} characters.")
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(appearances, f, ensure_ascii=False, indent=2)
        
    print(f"Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    extract_appearances()
