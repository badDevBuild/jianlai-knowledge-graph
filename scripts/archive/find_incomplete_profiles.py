
import os
import json
import glob

DATA_DIR = 'data/build/profiles_v3'

def main():
    if not os.path.exists(DATA_DIR):
        print(f"Directory {DATA_DIR} not found.")
        return

    json_files = glob.glob(os.path.join(DATA_DIR, "*.json"))
    failed_raw_files = glob.glob(os.path.join(DATA_DIR, "*_failed.raw"))
    failed_fixed_files = glob.glob(os.path.join(DATA_DIR, "*_failed_fixed.raw"))

    incomplete_jsons = []
    
    print(f"Scanning {len(json_files)} JSON files...")
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Criteria for incomplete: Missing 'bio' or 'appearance' or 'factions'
            # (Note: keys might vary slightly, but 'bio' is usually a strong indicator of AI generation success)
            if not data.get('bio') and not data.get('appearance'):
                incomplete_jsons.append(json_file)
                
        except json.JSONDecodeError:
            incomplete_jsons.append(json_file) # Invalid JSON is incomplete

    print(f"Found {len(failed_raw_files)} explicit failure logs (*_failed.raw)")
    print(f"Found {len(incomplete_jsons)} incomplete/empty JSON files")
    
    # Generate a report and optionally delete
    all_to_delete = failed_raw_files + failed_fixed_files + incomplete_jsons
    
    print(f"Deleting {len(all_to_delete)} files...")
    for f in all_to_delete:
        try:
            os.remove(f)
        except OSError as e:
            print(f"Error deleting {f}: {e}")
            
    print("Cleanup complete.")
        
if __name__ == "__main__":
    main()
