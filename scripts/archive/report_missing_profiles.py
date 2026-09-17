
import json
import os
import glob

SOURCE_DATA = 'data/build/characters.json'
OUTPUT_DIR = 'data/build/profiles_v3'

def load_source_data():
    with open(SOURCE_DATA, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_sorted_characters(data):
    # Sort by importance: len(quotes) + len(relations)
    char_list = []
    for name, details in data.items():
        score = len(details.get('quotes', [])) + len(details.get('relations', []))
        char_list.append((name, score))
    
    # Sort descending
    char_list.sort(key=lambda x: x[1], reverse=True)
    return char_list # Return tuples (name, score)

def main():
    if not os.path.exists(SOURCE_DATA):
        print(f"Error: {SOURCE_DATA} not found.")
        return

    full_data = load_source_data()
    sorted_chars = get_sorted_characters(full_data)
    
    existing_files = set(glob.glob(os.path.join(OUTPUT_DIR, "*.json")))
    existing_names = {os.path.splitext(os.path.basename(f))[0] for f in existing_files}
    
    # Load Blocklist
    blocklist = set()
    blocklist_path = "data/build/profile_generation_blocklist.txt"
    if os.path.exists(blocklist_path):
        with open(blocklist_path, 'r', encoding='utf-8') as f:
            blocklist = {line.strip() for line in f if line.strip()}
    
    missing_chars = []
    blocked_count = 0
    
    for name, score in sorted_chars:
        # If exists, not missing
        if name in existing_names:
            continue
            
        # If blocked, not "missing" (it's ignored)
        if name in blocklist:
            blocked_count += 1
            continue
            
        missing_chars.append((name, score))
            
    total_chars = len(sorted_chars)
    done_chars = len(existing_names)
    missing_count = len(missing_chars)
    
    # Effective total = Total - Blocked
    effective_total = total_chars - blocked_count
    
    print(f"Total Characters: {total_chars}")
    print(f"Blocked (Generic): {blocked_count}")
    print(f"Profiles Generated: {done_chars}")
    print(f"Remaining Missing: {missing_count} (out of {effective_total} valid)")
    print("-" * 30)
    print(f"Top 50 Missing Characters by Priority (Quotes+Relations):")
    
    for i, (name, score) in enumerate(missing_chars[:50], 1):
        print(f"{i}. {name} (Score: {score})")
        
    # Save full list to file
    with open("data/build/missing_profiles_list.txt", "w", encoding='utf-8') as f:
        f.write(f"Missing Profiles Report ({missing_count} total)\n")
        f.write("Format: Name (Importance Score)\n\n")
        for name, score in missing_chars:
            f.write(f"{name} ({score})\n")
    
    print("-" * 30)
    print(f"Full list saved to data/build/missing_profiles_list.txt")

if __name__ == "__main__":
    main()
