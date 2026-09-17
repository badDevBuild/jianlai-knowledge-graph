
import json
import os
import subprocess
import re
import time

# Configuration
SOURCE_DATA = 'data/build/characters.json'
PROMPT_TEMPLATE = 'docs/notebooklm_prompt_char_profile.md'
OUTPUT_DIR = 'data/build/profiles_v3'
NOTEBOOK_ID = '3dcbda80-313f-49cc-ab2c-d85833ec202c'
LOG_FILE = 'batch_error.log'
RETRY_LOG = 'retry_error.log'

def load_source_data():
    with open(SOURCE_DATA, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_prompt_template():
    with open(PROMPT_TEMPLATE, 'r', encoding='utf-8') as f:
        return f.read()

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
            
        is_structural = False
        if line[-1] in ',{[]}:':
             is_structural = True
        elif line.endswith('"'):
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
            fixed_text += line + "\\n"
                 
    return fixed_text

def clean_json_response(stdout_text):
    json_str = None
    match = re.search(r'```json\s*(.*?)\s*```', stdout_text, re.DOTALL)
    if match:
        json_str = match.group(1)
    else:
        start = stdout_text.find('{')
        end = stdout_text.rfind('}')
        if start != -1 and end != -1:
            json_str = stdout_text[start:end+1]
    
    if json_str:
        return repair_json_content(json_str) 
    return None

def process_character(name, existing_data, prompt_template):
    print(f"\nRetrying: {name}...")
    output_path = os.path.join(OUTPUT_DIR, f"{name}.json")
    
    if os.path.exists(output_path):
        print(f"  Skipping (Already exists/Fixed): {output_path}")
        return True

    prompt = prompt_template.replace('陈平安', name)
    
    try:
        # Increased timeout for retries as these might be complex characters
        result = subprocess.run(
            ["notebooklm", "ask", prompt, "--notebook", NOTEBOOK_ID],
            capture_output=True,
            text=True,
            timeout=180
        )
        
        if result.returncode != 0:
            error_msg = f"NotebookLM Error: {result.stderr}"
            print(error_msg)
            return False

        json_str = clean_json_response(result.stdout)
        if not json_str:
            print("No JSON found")
            return False

        try:
            ai_data = json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"Still Invalid JSON: {str(e)}")
            # Save raw output for inspection
            with open(os.path.join(OUTPUT_DIR, f"{name}_retry_failed.raw"), 'w') as f:
                f.write(result.stdout)
            with open(os.path.join(OUTPUT_DIR, f"{name}_retry_failed_fixed.raw"), 'w') as f:
                f.write(json_str)
            return False

        if "quotes" in existing_data:
            ai_data["quotes"] = existing_data["quotes"]
        if "relations" in existing_data:
            ai_data["relations"] = existing_data["relations"]
            
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(ai_data, f, ensure_ascii=False, indent=2)
            
        print(f"  Success! Saved to {output_path}")
        return True

    except Exception as e:
        print(f"Retry Exception: {str(e)}")
        return False

def get_failed_list():
    failed_names = set()
    if not os.path.exists(LOG_FILE):
        return []
        
    with open(LOG_FILE, 'r') as f:
        for line in f:
            if "Invalid JSON" in line:
                # Format: "Name: Invalid JSON..."
                if ":" in line:
                    name = line.split(":")[0].strip()
                    failed_names.add(name)
    return list(failed_names)

def main():
    full_data = load_source_data()
    prompt_template = load_prompt_template()
    target_names = get_failed_list()
    
    print(f"Found {len(target_names)} characters marked as 'Invalid JSON' in logs.")
    
    success_count = 0
    for name in target_names:
        if name not in full_data:
            print(f"Skipping {name} (Not in source data??)")
            continue
            
        if process_character(name, full_data[name], prompt_template):
            success_count += 1
            time.sleep(5)
            
    print(f"\nRetry Batch Completed. Success: {success_count}/{len(target_names)}")

if __name__ == "__main__":
    main()
