import re
import os

source_file = "/Users/shushu/剑来/剑来 (烽火戏诸侯).md"
output_dir = "/Users/shushu/剑来/chapters"
max_chapters = 10000  # Process all chapters

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

def clean_filename(title):
    # Remove invalid characters for filenames
    return re.sub(r'[\\/*?:"<>|]', "", title).strip()

def split_novel():
    current_file = None
    chapter_count = 0
    
    with open(source_file, 'r', encoding='utf-8') as f:
        for line in f:
            # Check for chapter title (e.g., "## 第1章 惊蛰")
            # We also want to avoid the "Preface" chapters if possible, generally they are distinct?
            # Based on grep, real chapters seem to follow volumes.
            # But simple regex "## " is a good start.
            if line.startswith("## ") and "第" in line and "章" in line:
                if chapter_count >= max_chapters:
                    print(f"Reached limit of {max_chapters} chapters. Stopping.")
                    break
                
                if current_file:
                    current_file.close()
                
                title = line.strip().replace("## ", "")
                safe_title = clean_filename(title)
                filename = f"{output_dir}/{str(chapter_count+1).zfill(3)}_{safe_title}.txt"
                print(f"Creating: {filename}")
                
                current_file = open(filename, 'w', encoding='utf-8')
                current_file.write(line)
                chapter_count += 1
            else:
                if current_file:
                    current_file.write(line)

    if current_file:
        current_file.close()

if __name__ == "__main__":
    split_novel()
