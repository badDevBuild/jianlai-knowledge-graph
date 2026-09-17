
import json
import os
import subprocess
import re
import sys

# Configuration
SOURCE_DATA = 'data/build/characters.json'
PROMPT_TEMPLATE = 'docs/notebooklm_prompt_char_profile.md'
OUTPUT_DIR = 'data/build/profiles_v3'
NOTEBOOK_ID = '3dcbda80-313f-49cc-ab2c-d85833ec202c'
TARGET_NAME = "陈平安"

def load_source_data():
    with open(SOURCE_DATA, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_prompt_template():
    with open(PROMPT_TEMPLATE, 'r', encoding='utf-8') as f:
        return f.read()

def repair_json_content(text):
    # Same repair logic as batch script
    lines = text.splitlines()
    fixed_text = ""
    for i, line in enumerate(lines):
        line = line.rstrip()
        if not line: continue
        is_structural = False
        if line[-1] in ',{[]}:': is_structural = True
        elif line.endswith('"'):
             is_end_of_value = False
             for next_line in lines[i+1:]:
                 next_line = next_line.strip()
                 if not next_line: continue
                 if next_line.startswith(',') or next_line.startswith('}') or next_line.startswith(']'):
                     is_end_of_value = True
                 break
             if is_end_of_value: is_structural = True
        if is_structural: fixed_text += line + "\n"
        else: fixed_text += line + "\\n"
    return fixed_text

def clean_json_response(stdout_text):
    json_str = None
    match = re.search(r'```json\s*(.*?)\s*```', stdout_text, re.DOTALL)
    if match: json_str = match.group(1)
    else:
        start = stdout_text.find('{')
        end = stdout_text.rfind('}')
        if start != -1 and end != -1: json_str = stdout_text[start:end+1]
    
    if json_str: return repair_json_content(json_str) 
    return None

def main():
    print(f"Regenerating profile for {TARGET_NAME}...")
    
    full_data = load_source_data()
    existing_data = full_data.get(TARGET_NAME, {})
    prompt_tpl = load_prompt_template()
    prompt = prompt_tpl.replace('陈平安', TARGET_NAME)
    
    print("Sending query to NotebookLM...")
    result = subprocess.run(
        ["notebooklm", "ask", prompt, "--notebook", NOTEBOOK_ID],
        capture_output=True, text=True, timeout=180
    )
    
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return

    json_str = clean_json_response(result.stdout)
    if not json_str:
        print("Error: No JSON found in response.")
        print("Raw Output:", result.stdout)
        return

    try:
        ai_data = json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON: {e}")
        print("Fixed Str:", json_str)
        return

    # Merge Data
    if "quotes" in existing_data:
        ai_data["quotes"] = existing_data["quotes"]
    if "relations" in existing_data:
        ai_data["relations"] = existing_data["relations"]
        
    output_path = os.path.join(OUTPUT_DIR, f"{TARGET_NAME}.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(ai_data, f, ensure_ascii=False, indent=2)
        
    print(f"Success! Re-generated profile saved to {output_path}")

if __name__ == "__main__":
    main()
