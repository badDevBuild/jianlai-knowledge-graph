import json
import re
from item_normalizer import normalize_item_type

def run_step3():
    print("Step 3: Merging data...")
    
    # Load inputs
    with open("data/build/items_step1_aggregated.json", "r", encoding="utf-8") as f:
        aggregated_data = json.load(f)
        
    with open("data/build/items_step2_ai_raw.json", "r", encoding="utf-8") as f:
        ai_data = json.load(f)
        
    final_data = {}
    
    for name, fragment_list in aggregated_data.items():
        # Get AI result or Fallback
        ai_item = ai_data.get(name)
        
        # 1. Base Info
        if ai_item:
            final_item = {
                "name": ai_item.get("standard_name", name),
                "original_name": name,
                "type": normalize_item_type(ai_item.get("type", "其他")),
                "grade": ai_item.get("grade", "未知"),
                "status": ai_item.get("status", "未知"),
                "description": ai_item.get("description", ""),
                "aliases": list(set(ai_item.get("aliases", []) + [f["original_name"] for f in fragment_list if f["original_name"] != name])),
            }
        else:
            # Fallback
            final_item = {
                "name": name,
                "type": normalize_item_type(fragment_list[0].get("type", "其他")),
                "grade": "未知",
                "status": "未知",
                "description": fragment_list[0].get("description", ""), # Use first available description
                "aliases": [f["original_name"] for f in fragment_list if f["original_name"] != name],
            }
            
        # 2. Process Ownership Log (Local Logic)
        all_logs = []
        for frag in fragment_list:
             if "ownership_log" in frag:
                all_logs.extend(frag["ownership_log"])
        
        # Deduplicate
        unique_logs = {}
        for log in all_logs:
            key = f"{log.get('chapter', '')}_{log.get('owner', '')}"
            if key not in unique_logs:
                unique_logs[key] = log
        
        # Sort
        def parse_chapter(log):
            c = log.get('chapter', '')
            m = re.search(r"第(\d+)章", c)
            return int(m.group(1)) if m else 99999
            
        final_item["ownership_log"] = sorted(list(unique_logs.values()), key=parse_chapter)
        
        # 3. Deduplication by Standard Name
        std_name = final_item["name"]
        
        if std_name in final_data:
            # Merge into existing
            existing = final_data[std_name]
            
            # Merge Aliases
            new_aliases = set(existing["aliases"] + final_item["aliases"])
            if existing["original_name"] != final_item["original_name"]:
                new_aliases.add(final_item["original_name"])
            existing["aliases"] = list(new_aliases)
            
            # Merge Ownership Log
            combined_logs = existing["ownership_log"] + final_item["ownership_log"]
            # Re-deduplicate logs
            unique_logs_merge = {}
            for log in combined_logs:
                key = f"{log.get('chapter', '')}_{log.get('owner', '')}"
                if key not in unique_logs_merge:
                    unique_logs_merge[key] = log
            existing["ownership_log"] = sorted(list(unique_logs_merge.values()), key=parse_chapter)
            
            # Update Description (Prefer longer one or combine?)
            # Strategy: Keep the existing one usually, or if current is longer?
            # AI descriptions are usually similar. Let's append if significantly different? 
            # For simplicity, keep the first one encountered (usually from the main key), 
            # but maybe update if the new one is "better". 
            # Let's just keep the first one for now to avoid bloating.
            
        else:
            final_data[std_name] = final_item

    # Save Final
    output_file = "data/build/items_cleaned.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(final_data, f, indent=2, ensure_ascii=False)
        
    print(f"Final Step Complete! Saved {len(final_data)} items to {output_file}")

if __name__ == "__main__":
    run_step3()
