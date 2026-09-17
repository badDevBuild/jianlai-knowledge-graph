
import json
import subprocess
import os
import argparse
import sys
import time
from concurrent.futures import ThreadPoolExecutor
import threading
from datetime import datetime

# Configuration
INPUT_FILE = "items_prompts.json"
OUTPUT_DIR = "item_images"
GENERATOR_SCRIPT = "/Users/shushu/剑来/.agent/skills/image-gen/scripts/generate_image.py"

print_lock = threading.Lock()
processed_count = 0

def generate_task(item):
    global processed_count
    item_name, prompt_text = item
    safe_name = item_name.replace("/", "_").replace("\\", "_")
    output_path = os.path.join(OUTPUT_DIR, f"{safe_name}.jpg")
    
    # Resume check
    # Note: Check handled here to save thread overhead, but also good inside thread
    if os.path.exists(output_path):
        with print_lock:
            # print(f"[Skip] {item_name} (Image exists)") 
            # Commented out to avoid spamming 2000 lines of skips
            pass
        return

    # Strategy: Try Remote (ModelScope) first. If 429, fallback to Local.
    # We won't loop retries for 429 on remote, we just switch to local immediately to keep moving.
    
    # 1. Try Remote
    try:
        with print_lock:
             timestamp = datetime.now().strftime("%H:%M:%S")
             print(f"[{timestamp}] [START] {item_name} (Remote)")
             
        cmd_remote = ["python3", GENERATOR_SCRIPT, prompt_text, "-o", output_path, "--backend", "modelscope"]
        if args.aspect_ratio:
            cmd_remote.extend(["--aspect-ratio", args.aspect_ratio])
        elif args.width and args.height:
            cmd_remote.extend(["--width", str(args.width), "--height", str(args.height)])
        else:
            # Default to explicit 1024x1024 as requested
            cmd_remote.extend(["--width", "1024", "--height", "1024"])

        result = subprocess.run(cmd_remote, capture_output=True, text=True)
        
        if result.returncode == 0:
            with print_lock:
                processed_count += 1
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] [DONE #{processed_count}] {item_name} (Remote)")
            return
        
        # Check for 429
        if "429" in result.stderr:
             with print_lock:
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] [WARN] {item_name}: Remote 429. Falling back to LOCAL...")
                print(f"[{timestamp}] [START] {item_name} (Local)")
             
             # Fallback to Local
             cmd_local = ["python3", GENERATOR_SCRIPT, prompt_text, "-o", output_path, "--backend", "local"]
             # Reserving specific arguments for local if needed, but assuming same basic aspect ratio args work
             if args.aspect_ratio:
                cmd_local.extend(["--aspect-ratio", args.aspect_ratio])
             elif args.width and args.height:
                cmd_local.extend(["--width", str(args.width), "--height", str(args.height)])
             else:
                 # Default to explicit 1024x1024 as requested
                 cmd_local.extend(["--width", "1024", "--height", "1024"])

             result_local = subprocess.run(cmd_local, capture_output=True, text=True)
             
             with print_lock:
                timestamp = datetime.now().strftime("%H:%M:%S")
                if result_local.returncode == 0:
                    processed_count += 1
                    print(f"[{timestamp}] [DONE #{processed_count}] {item_name} (Local)")
                else:
                    print(f"[{timestamp}] [FAIL] {item_name} (Local): {result_local.stderr.strip()[:100]}...")
             return

        # If remote failed but NOT 429, log it
        with print_lock:
             timestamp = datetime.now().strftime("%H:%M:%S")
             print(f"[{timestamp}] [FAIL] {item_name} (Remote): {result.stderr.strip()[:100]}...")

    except Exception as e:
        with print_lock:
            print(f"[ERROR] {item_name}: {e}")



def main():
    parser = argparse.ArgumentParser(description="Batch generate images (Concurrent)")
    parser.add_argument("--workers", type=int, default=3, help="Number of concurrent threads")
    parser.add_argument("--limit", type=int, default=0, help="Limit items (0 for all)")
    parser.add_argument("--aspect-ratio", default="1:1", help="Aspect ratio (e.g. 1:1, 16:9, 4:3)")
    parser.add_argument("--width", type=int, help="Custom width (overrides aspect-ratio if paired with height)")
    parser.add_argument("--height", type=int, help="Custom height")
    
    global args
    args = parser.parse_args()

    # 1. Load prompts
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found.")
        return

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        prompts = json.load(f)

    # 2. Ensure output dir
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    items = list(prompts.items())
    if args.limit > 0:
        items = items[:args.limit]

    print(f"Starting generation for {len(items)} items with {args.workers} threads...")
    print(f"Output Directory: {OUTPUT_DIR}")

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        executor.map(generate_task, items)

    print("\nAll tasks completed.")

if __name__ == "__main__":
    main()
