
import json
import os
import time
import subprocess
import re

# Configuration
SOURCE_DATA = 'data/build/characters.json'
PROMPT_TEMPLATE = 'docs/notebooklm_prompt_char_profile.md'
OUTPUT_DIR = 'data/build/profiles_v3'
NOTEBOOK_ID = '3dcbda80-313f-49cc-ab2c-d85833ec202c'
LOG_FILE = 'batch_error.log'

def load_source_data():
    with open(SOURCE_DATA, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_prompt_template():
    with open(PROMPT_TEMPLATE, 'r', encoding='utf-8') as f:
        return f.read()

def get_sorted_characters(data):
    # Sort by importance: len(quotes) + len(relations)
    char_list = []
    for name, details in data.items():
        score = len(details.get('quotes', [])) + len(details.get('relations', []))
        char_list.append((name, score))
    
    # Sort descending
    char_list.sort(key=lambda x: x[1], reverse=True)
    return [c[0] for c in char_list]





def repair_json_content(text):
    """
    Heuristic to repair JSON with unescaped newlines inside strings.
    We rebuild the string line by line. If a line is a 'continuation' (inside a string),
    we append it with an escaped newline \\n and NO real newline.
    If it is structural, we keep the real newline.
    """
    lines = text.splitlines()
    fixed_text = ""
    
    for i, line in enumerate(lines):
        line = line.rstrip()
        if not line:
            continue
            
        # Determine if this line ends a structural unit
        is_structural = False
        if line[-1] in ',{[]}:':
             is_structural = True
        elif line.endswith('"'):
             # Check if this quote likely ends a value
             # Look ahead for structural chars
             is_end_of_value = False
             for next_line in lines[i+1:]:
                 next_line = next_line.strip()
                 if not next_line: continue
                 if next_line.startswith(',') or next_line.startswith('}') or next_line.startswith(']'):
                     is_end_of_value = True
                 break
             
             if is_end_of_value:
                 is_structural = True

        if is_structural:
            fixed_text += line + "\n"
        else:
            # Inside a string: escape the newline and DO NOT add a real newline
            # This merges this line with the next one effectively
            fixed_text += line + "\\n"
                 
    return fixed_text

def clean_json_response(stdout_text):
    json_str = None
    # Try to find JSON block
    match = re.search(r'```json\s*(.*?)\s*```', stdout_text, re.DOTALL)
    if match:
        json_str = match.group(1)
    else:
        # Fallback: find outer braces
        start = stdout_text.find('{')
        end = stdout_text.rfind('}')
        if start != -1 and end != -1:
            json_str = stdout_text[start:end+1]
    
    if json_str:
        return repair_json_content(json_str) 
        
    return None

def process_character(name, existing_data, prompt_template):
    print(f"\nProcessing: {name}...")
    
    output_path = os.path.join(OUTPUT_DIR, f"{name}.json")
    if os.path.exists(output_path):
        print(f"  Skipping (Already exists): {output_path}")
        return True

    prompt = prompt_template.replace('陈平安', name)
    
    try:
        # Use simpler unique delimiter for clarity if debugging needed, but standard should be fine
        result = subprocess.run(
            ["notebooklm", "ask", prompt, "--notebook", NOTEBOOK_ID],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode != 0:
            error_msg = f"NotebookLM Error for {name}: {result.stderr}"
            print(error_msg)
            with open(LOG_FILE, 'a') as log:
                log.write(f"{name}: {error_msg}\n")
            return False

        json_str = clean_json_response(result.stdout)
        if not json_str:
            error_msg = f"No JSON found for {name}"
            print(error_msg)
            with open(LOG_FILE, 'a') as log:
                log.write(f"{name}: {error_msg}\n")
            # Save raw output
            with open(os.path.join(OUTPUT_DIR, f"{name}_failed.raw"), 'w') as f:
                f.write(result.stdout)
            return False

        try:
            ai_data = json.loads(json_str)
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON for {name}: {str(e)}"
            print(error_msg)
            with open(LOG_FILE, 'a') as log:
                log.write(f"{name}: {error_msg}\n")
            with open(os.path.join(OUTPUT_DIR, f"{name}_failed.raw"), 'w') as f:
                f.write(result.stdout)
            with open(os.path.join(OUTPUT_DIR, f"{name}_failed_fixed.raw"), 'w') as f:
                f.write(json_str) # Save the 'fixed' string to see what went wrong
            return False

        # Merge Data
        if "quotes" in existing_data:
            ai_data["quotes"] = existing_data["quotes"]
        if "relations" in existing_data:
            ai_data["relations"] = existing_data["relations"]
            
        # Clean citations (optional simple regex)
        # Recurse through string values? For now basic cleaning
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(ai_data, f, ensure_ascii=False, indent=2)
            
        print(f"  Success! Saved to {output_path}")
        return True

    except Exception as e:
        error_msg = f"System Error for {name}: {str(e)}"
        print(error_msg)
        with open(LOG_FILE, 'a') as log:
            log.write(f"{name}: {error_msg}\n")
        return False

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    full_data = load_source_data()
    prompt_template = load_prompt_template()
    sorted_names = get_sorted_characters(full_data)
    
    print(f"Found {len(sorted_names)} characters.")
    
    # Pre-filter existing profiles to avoid slow checks
    existing_files = set(os.listdir(OUTPUT_DIR))
    
    # Load Blocklist
    blocklist_files = set()
    blocklist_path = "data/build/profile_generation_blocklist.txt"
    if os.path.exists(blocklist_path):
        with open(blocklist_path, 'r', encoding='utf-8') as f:
            blocklist = [line.strip() for line in f if line.strip()]
            blocklist_files = set(blocklist)
            print(f"Loaded blocklist with {len(blocklist_files)} names (Will Skip).")
            
    missing_names = []
    skipped_count = 0
    blocked_count = 0
    
    for name in sorted_names:
        if name in blocklist_files:
            blocked_count += 1
            continue
        if f"{name}.json" in existing_files:
            skipped_count += 1
            continue
        missing_names.append(name)
    
    print(f"Skipping {skipped_count} existing profiles.")
    print(f"Skipping {blocked_count} blocked generic profiles.")
    print(f"Starting generation for {len(missing_names)} pending characters...")
    print(f"Top 5 priority: {missing_names[:5]}")
    
    # Iterate only over missing names
    sorted_names = missing_names
    
    # Limit removed for full run
    count = 0
    # limit = 5 
    
    for name in sorted_names:
        if name == "陈平安":
            continue # Skip as already manually done/special case
            
        # if count >= limit:
        #    print("Dry run limit reached (5 characters). Stopping.")
        #    break
            
        success = process_character(name, full_data[name], prompt_template)
        if success:
            count += 1
            time.sleep(5)  # Sleep between requests

if __name__ == "__main__":
    main()
