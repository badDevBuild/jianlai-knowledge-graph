
import json
import os

REPORT_FILE = 'name_collisions.json'

def cleanup():
    if not os.path.exists(REPORT_FILE):
        print(f"Error: {REPORT_FILE} not found. Please run analyze_duplicates.py first.")
        return

    with open(REPORT_FILE, 'r', encoding='utf-8') as f:
        collisions = json.load(f)

    deleted_count = 0
    kept_count = 0

        # Prepare backup dir
    backup_dir = 'data/backup/duplicates_v3'
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    print(f"Processing {len(collisions)} collision groups...")

    for group in collisions:
        name = group['name']
        files = group['files']
        
        # User Logic: "Mainly look at who has the most relationships"
        files.sort(key=lambda x: (x['rel_count'], x['bio_len']), reverse=True)

        winner = files[0]
        losers = files[1:]

        print(f"\n🟢 Keeping: {winner['filename']} (Rel: {winner['rel_count']}) for '{name}'")
        kept_count += 1

        for loser in losers:
            path = loser['path']
            if os.path.exists(path):
                try:
                    # Move to backup
                    backup_path = os.path.join(backup_dir, loser['filename'])
                    os.rename(path, backup_path)
                    print(f"   � Moved to backup: {loser['filename']} (Rel: {loser['rel_count']})")
                    deleted_count += 1
                except Exception as e:
                    print(f"   ⚠️ Failed to move {path}: {e}")
            else:
                print(f"   ⚠️ File already gone: {path}")

    print(f"\nCleanup Complete.")
    print(f"Kept (Winner) Files: {kept_count}")
    print(f"Deleted (Duplicate) Files: {deleted_count}")

if __name__ == "__main__":
    cleanup()
