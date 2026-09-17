import json
import os
import subprocess
import time
import re
import argparse
from typing import List, Dict, Any

# Configuration
NOTEBOOK_ID = "3dcbda80-313f-49cc-ab2c-d85833ec202c"
INPUT_FILE = "items.json"
OUTPUT_FILE = "items_enriched.json"
BATCH_SIZE = 10
MAX_RETRIES = 3

def load_items(filepath: str) -> Dict[str, Any]:
    if not os.path.exists(filepath):
        print(f"Error: {filepath} not found.")
        return {}
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_items(items: Dict[str, Any], filepath: str):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    print(f"Saved progress to {filepath}")

def get_notebooklm_response(items_batch: List[Dict[str, Any]]) -> str:
    item_names = [item['name'] for item in items_batch]
    names_str = ", ".join(item_names)
    
    prompt = f"""
I have a list of items from the novel "Jian Lai" (剑来).
Please provide enriched details for the following items based on the notebook content:
Items: {names_str}

For EACH item, provide a JSON object with these EXACT fields:
- name: Item Name
- is_unique: Boolean.
- is_unique: Boolean. True if it is a specific unique item (e.g. "Chen Ping'an's Flying Sword"). False if it is a generic category (e.g. "Copper Coin").
- original_name: Original/Alternative Name (if any)
- type: One of [本命飞剑, 仙剑, 法宝, 灵器, 重器, 匠器, 方寸物, 丹药, 典籍, 符箓, 货币, 灵物, 材料, 其他]
- subtype: Specific subtype (e.g. "攻伐类", "防御类")
- holder: Current Owner
- holder_relation: One of [大炼, 中炼, 小炼, 持有, 寄托]
- previous_holders: List of objects {{ "name": "...", "relation": "One of [原主, 赠予者, 曾持有, 夺取自, 继承自]" }}
- rank: One of [仙兵, 半仙兵, 法宝, 灵器, 重器, 匠器]
- rank_potential: Growth potential description
- supernatural_ability: Special abilities (本命神通)
- evolution: Object {{ "current_form": "...", "materials_consumed": ["..."], "potential_evolution": "..." }}
- visual: Object {{ "static": "Detailed description of physical appearance when inactive/static.", "active": "Detailed description of visual effects/transformations when active/used." }}
- provenance: Object {{ "origin": "Source/Origin", "karma_link": "Causal connections" }}
- description: Detailed summary of backstory and significance.

Output format:
Return ONLY a valid JSON object where keys are the item names and value is the object above.
Example:
{{
  "UniqueSword": {{ "name": "...", "is_unique": true, ... }},
  "CommonCopperCoin": {{ "name": "...", "is_unique": false, ... }}
}}
Do not include any explanation text outside the JSON.
"""
    
    cmd = [
        "notebooklm", "ask", prompt,
        "--notebook", NOTEBOOK_ID
    ]
    
    for attempt in range(MAX_RETRIES):
        print(f"Querying NotebookLM for: {names_str}... (Attempt {attempt+1}/{MAX_RETRIES})")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                return result.stdout
            else:
                print(f"Error (Attempt {attempt+1}): {result.stderr.strip()}")
        except subprocess.TimeoutExpired:
            print(f"Timeout (Attempt {attempt+1})")
        except Exception as e:
            print(f"Exception (Attempt {attempt+1}): {e}")
        
        # Wait before retry
        if attempt < MAX_RETRIES - 1:
            time.sleep(0)
            
    print(f"Failed to get response after {MAX_RETRIES} attempts.")
    return ""

def sanitize_json_string(s: str) -> str:
    # Remove control characters
    s = re.sub(r'[\x00-\x09\x0b\x0c\x0e-\x1f]', '', s)
    # Remove trailing commas before matching closing braces/brackets
    # Matches , followed by whitespace and } or ]
    s = re.sub(r',\s*([}\]])', r'\1', s)
    return s

def clean_text(text: str) -> str:
    if not isinstance(text, str):
        return text
    # Remove citations like [1], [1, 2], [1, 2, 3]
    text = re.sub(r'\[\d+(?:,\s*\d+)*\]', '', text)
    # Remove literal newline characters or escape sequences if desired
    # User asked to remove "\n", often meaning joining lines
    text = text.replace('\n', ' ').replace('\\n', ' ')
    # Clean up multiple spaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def clean_structure(data: Any) -> Any:
    if isinstance(data, dict):
        return {k: clean_structure(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [clean_structure(v) for v in data]
    elif isinstance(data, str):
        return clean_text(data)
    else:
        return data

def parse_json_response(response: str) -> Dict[str, Any]:
    # Try to find JSON block in markdown
    json_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        # Try to find raw JSON start/end
        json_match = re.search(r'(\{.*\})', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            print("No JSON block found in response.")
            print(f"Raw response preview: {response[:500]}...")
            return {}

    # Sanitize
    json_str = sanitize_json_string(json_str)

    try:
        data = json.loads(json_str, strict=False)
        return clean_structure(data)
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}")
        # print(f"Failed JSON string snippet: {json_str[:100]}...") # Printing just the start isn't helpful for char 881
        # Print the area around the error
        start = max(0, e.pos - 50)
        end = min(len(json_str), e.pos + 50)
        print(f"Error context: ...{json_str[start:end]}...")
        
        return {}

def process_batch(batch: List[Dict[str, Any]], all_items: Dict[str, Any]):
    response = get_notebooklm_response(batch)
    if not response:
        print("Empty response, skipping batch.")
        return

    enriched_data = parse_json_response(response)
    
    for item_name, new_data in enriched_data.items():
        if item_name in all_items:
            # Check for uniqueness first - DEPRECATED: User asked to keep all items
            # if new_data.get('is_unique') is False:
            #     print(f"REMOVED Generic Item: {item_name}")
            #     # Remove from the main dictionary
            #     del all_items[item_name]
            #     continue

            original = all_items[item_name]
            
            # Deep merge strategy: Prefer new data for schema fields
            # We overwrite specific sections that the enrichment provides
            fields_to_update = [
                'original_name', 'type', 'subtype', 'holder', 'holder_relation',
                'previous_holders', 'rank', 'rank_potential', 'supernatural_ability',
                'evolution', 'visual', 'provenance', 'description'
            ]
            
            for field in fields_to_update:
                if new_data.get(field):
                    original[field] = new_data[field]
            
            # Mark as enriched
            original['enriched'] = True
            print(f"Updated: {item_name}")

def main():
    parser = argparse.ArgumentParser(description="Enrich items.json using NotebookLM")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of items to process (0 for all)")
    parser.add_argument("--dry-run", action="store_true", help="Process only one batch to test")
    args = parser.parse_args()

    # Load data: Use enriched file as primary source if it exists (for proper resume)
    # This ensures deleted items (is_unique=False) don't get reprocessed
    if os.path.exists(OUTPUT_FILE):
        print(f"Resuming from {OUTPUT_FILE}...")
        items = load_items(OUTPUT_FILE)
    else:
        print(f"Starting fresh from {INPUT_FILE}...")
        items = load_items(INPUT_FILE)
    
    if not items:
        return
    
    # 2. Prioritization
    # Filter out items that are already enriched
    to_process = []
    
    # Priority groups
    priority_high = [] # 仙兵, 法宝
    priority_med = []  # Others
    
    for key, item in items.items():
        if item.get('enriched'):
            continue
            
        # Check priority
        grade = item.get('grade', '')
        type_ = item.get('type', '')
        
        if '仙兵' in grade or '法宝' in grade or '仙兵' in type_ or '法宝' in type_:
            priority_high.append(item)
        else:
            priority_med.append(item)
            
    to_process = priority_high + priority_med
    
    if args.dry_run:
        to_process = to_process[:BATCH_SIZE]
        print(f"Dry run: Processing {len(to_process)} items")
    elif args.limit > 0:
        to_process = to_process[:args.limit]
        print(f"Limit set: Processing {len(to_process)} items")
    else:
        print(f"Processing ALL {len(to_process)} remaining items")

    # 3. Batching
    total_processed = 0
    for i in range(0, len(to_process), BATCH_SIZE):
        batch = to_process[i : i + BATCH_SIZE]
        print(f"\n--- Batch {i//BATCH_SIZE + 1} ({len(batch)} items) ---")
        
        process_batch(batch, items)
        
        # Save progress
        save_items(items, OUTPUT_FILE)
        total_processed += len(batch)
        
        # Rate limiting / polite delay
        time.sleep(0) 

    print(f"\nDone. Processed {total_processed} items.")

if __name__ == "__main__":
    main()
