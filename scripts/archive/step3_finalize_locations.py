import json
from location_normalizer import normalize_location_type

def run_step3():
    print("Step 3: Merging location data...")
    
    try:
        with open("data/build/locations_step1_aggregated.json", "r", encoding="utf-8") as f:
            aggregated_data = json.load(f)
        with open("data/build/locations_step2_ai_raw.json", "r", encoding="utf-8") as f:
            ai_data = json.load(f)
    except FileNotFoundError:
        print("Input files not found.")
        return
        
    final_data = {}
    
    # helper to find canonical names
    # First pass: map all keys to their canonical names according to AI or Fallback
    key_to_canonical = {}
    for name in aggregated_data.keys():
        ai_item = ai_data.get(name)
        if ai_item:
            key_to_canonical[name] = ai_item.get("canonical_name", name)
        else:
            key_to_canonical[name] = name
            
    for name, fragment_list in aggregated_data.items():
        ai_item = ai_data.get(name)
        
        # Determine canonical name for this node
        canonical_name = key_to_canonical[name]
        
        if canonical_name in final_data:
            final_item = final_data[canonical_name]
        else:
            final_item = {
                "name": canonical_name,
                "type": "地点",
                "description": "",
                "parent": "未知",
                "aliases": [],
                "hierarchy": []
            }
            
        # Update with new data (Strategy: AI > Existing)
        if ai_item:
            final_item["type"] = normalize_location_type(ai_item.get("type", final_item["type"]))
            
            # Description: prefer longer/newer
            new_desc = ai_item.get("description", "")
            if len(new_desc) > len(final_item["description"]):
                final_item["description"] = new_desc
                
            # Aliases
            new_aliases = set(final_item["aliases"] + ai_item.get("aliases", []))
            if name != canonical_name:
                new_aliases.add(name)
            final_item["aliases"] = list(new_aliases)
            
            # Hierarchy & Parent
            hierarchy = ai_item.get("hierarchy", [])
            if hierarchy and len(hierarchy) > len(final_item["hierarchy"]):
                final_item["hierarchy"] = hierarchy
                # Immediate parent is the one before the last one (which should be self)
                # But hierarchy usually includes self at the end? Or path to self?
                # Prompt said: [World, Continent, ..., Node]
                # So parent is [-2] if len >= 2
                if len(hierarchy) >= 2:
                    raw_parent = hierarchy[-2]
                    # Try to normalize parent name? 
                    # Ideally we should point to another key in our DB.
                    # For now just store the string.
                    final_item["parent"] = raw_parent
                    
        else:
            # Fallback
            final_item["description"] = fragment_list[0].get("description", "")
            if name != canonical_name:
                final_item["aliases"].append(name)
            
        final_data[canonical_name] = final_item

    # Save Final
    output_file = "data/build/locations_cleaned.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(final_data, f, indent=2, ensure_ascii=False)
        
    print(f"Final Step Complete! Saved {len(final_data)} locations to {output_file}")

if __name__ == "__main__":
    run_step3()
