
import json
import subprocess
import os
import argparse
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import threading

# Configuration
INPUT_FILE = "data/build/test_cuicheng.json"
OUTPUT_DIR = "data/build/character_images"
# Full path to the skill script
GENERATOR_SCRIPT = os.path.abspath(".agent/skills/image-gen/scripts/generate_image.py")

print_lock = threading.Lock()
processed_count = 0

def generate_task(item):
    global processed_count
    name, prompt_text = item
    
    # Sanitize filename
    safe_name = name.replace("/", "_").replace("\\", "_")
    output_path = os.path.join(OUTPUT_DIR, f"{safe_name}.jpg")
    
    # Resume check
    if os.path.exists(output_path):
        return

    # 1. Try Remote (ModelScope)
    try:
        # Construct command
        cmd_remote = [
            "python3", GENERATOR_SCRIPT, 
            prompt_text, 
            "-o", output_path, 
            "--backend", "modelscope",
            "--aspect-ratio", "3:4"
        ]

        result = subprocess.run(cmd_remote, capture_output=True, text=True)
        
        if result.returncode == 0:
            with print_lock:
                processed_count += 1
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] [DONE #{processed_count}] {name}")
            return
        
        # Check for 429
        if "429" in result.stderr:
             with print_lock:
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] [WARN] {name}: Remote 429. Falling back to LOCAL...")
             
             # Fallback to Local
             cmd_local = [
                "python3", GENERATOR_SCRIPT, 
                prompt_text, 
                "-o", output_path, 
                "--backend", "local",
                "--aspect-ratio", "3:4"
             ]
             
             result_local = subprocess.run(cmd_local, capture_output=True, text=True)
             
             with print_lock:
                timestamp = datetime.now().strftime("%H:%M:%S")
                if result_local.returncode == 0:
                    processed_count += 1
                    print(f"[{timestamp}] [DONE #{processed_count}] {name} (Local)")
                else:
                    # Print short error
                    err = result_local.stderr.strip().split('\n')[-1]
                    print(f"[{timestamp}] [FAIL] {name} (Local): {err[:50]}...")
             return

        # Other remote error
        with print_lock:
             timestamp = datetime.now().strftime("%H:%M:%S")
             err = result.stderr.strip().split('\n')[-1]
             print(f"[{timestamp}] [FAIL] {name} (Remote): {err[:50]}...")

    except Exception as e:
        with print_lock:
            print(f"[ERROR] {name}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Batch generate character images")
    parser.add_argument("--workers", type=int, default=3, help="Number of concurrent threads")
    parser.add_argument("--limit", type=int, default=0, help="Limit items (0 for all)")
    args = parser.parse_args()

    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found.")
        return

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        prompts = json.load(f)

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    items = list(prompts.items())
    if args.limit > 0:
        items = items[:args.limit]

    print(f"Starting generation for {len(items)} characters with {args.workers} threads...")
    print(f"Output: {OUTPUT_DIR}")

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        executor.map(generate_task, items)

    print("\nAll tasks completed.")

if __name__ == "__main__":
    main()
