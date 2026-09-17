
import os
import re

CHAPTERS_DIR = "/Users/shushu/剑来/chapters"

def check_chapters():
    files = sorted(os.listdir(CHAPTERS_DIR))
    chapter_map = {}
    
    print(f"Checking {len(files)} files in {CHAPTERS_DIR}...")
    
    # Regex to extract chapter number from filename like "006_第1章 惊蛰.txt"
    # Note: The '006' is just a file sequence index from split_demo.py, not the actual chapter num.
    # We care about the "第X章" part.
    pattern = re.compile(r"第(\d+)章")
    
    for f in files:
        if not f.endswith(".txt"): continue
        match = pattern.search(f)
        if match:
            num = int(match.group(1))
            if num in chapter_map:
                print(f"Duplicate Chapter {num}: {f} AND {chapter_map[num]}")
            chapter_map[num] = f
        else:
            print(f"Warning: No chapter number found in {f}")

    if not chapter_map:
        print("No chapters found.")
        return

    max_chap = max(chapter_map.keys())
    print(f"Max Chapter found: {max_chap}")
    
    missing = []
    for i in range(1, max_chap + 1):
        if i not in chapter_map:
            missing.append(i)
            
    if missing:
        print(f"MISSING {len(missing)} chapters:")
        # Print ranges of missing chapters
        # e.g. 1-5, 10, 20-25
        i = 0
        while i < len(missing):
            start = missing[i]
            end = start
            while i + 1 < len(missing) and missing[i+1] == end + 1:
                end += 1
                i += 1
            if start == end:
                print(f"  - Chapter {start}")
            else:
                print(f"  - Chapters {start} to {end}")
            i += 1
    else:
        print("✅ No missing chapters detected in the sequence (1 to matches max).")

if __name__ == "__main__":
    check_chapters()
