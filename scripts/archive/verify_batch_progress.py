
import json
import os
import random
import glob

CHARACTERS_FILE = 'data/build/characters.json'
OUTPUT_DIR = 'data/build/profiles_v3'

def verify_progress():
    # 1. Total Characters
    with open(CHARACTERS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        total_chars = len(data)
        all_names = set(data.keys())

    # 2. Completed Profiles
    json_files = glob.glob(os.path.join(OUTPUT_DIR, '*.json'))
    completed_count = len(json_files)
    completed_names = set(os.path.basename(f).replace('.json', '') for f in json_files)

    # 3. Remaining
    remaining_names = list(all_names - completed_names)
    remaining_count = len(remaining_names)

    print(f"=== Batch Progress Report ===")
    print(f"Total Characters: {total_chars}")
    print(f"Completed: {completed_count}")
    print(f"Remaining: {remaining_count}")
    print(f"Progress: {(completed_count / total_chars) * 100:.2f}%")
    print(f"Sample Remaining: {remaining_names[:5]}...")
    print("=============================\n")

    # 4. Audit 20 Samples
    sample_size = min(20, completed_count)
    if sample_size == 0:
        print("No profiles to audit.")
        return

    samples = random.sample(json_files, sample_size)
    print(f"=== Auditing {sample_size} Random Samples ===")
    
    issues = []
    valid_count = 0

    for file_path in samples:
        name = os.path.basename(file_path).replace('.json', '')
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                profile = json.load(f)
            
            # Simple content checks
            errors = []
            if not profile.get('bio'): errors.append("Missing Bio")
            if not profile.get('appearance'): errors.append("Missing Appearance")
            if not isinstance(profile.get('cultivation'), list): errors.append("Cultivation not list")
            
            if errors:
                issues.append(f"{name}: {', '.join(errors)}")
            else:
                valid_count += 1
                # Print a brief summary of one good profile to show content quality
                if valid_count == 1:
                    print(f"\n--- Detailed View of {name} ---")
                    print(json.dumps(profile, ensure_ascii=False, indent=2)[:500] + "\n... (truncated)\n---------------------------------")
        
        except json.JSONDecodeError:
            issues.append(f"{name}: Invalid JSON Syntax")
        except Exception as e:
            issues.append(f"{name}: Read Error ({str(e)})")

    print(f"\nAudit Result: {valid_count}/{sample_size} valid.")
    if issues:
        print("\nFound Issues:")
        for issue in issues:
            print(f"- {issue}")
    else:
        print("\nAll sampled files passed structure check.")

if __name__ == "__main__":
    verify_progress()
