import json
from collections import defaultdict
from location_normalizer import normalize_location_name, normalize_location_type, is_valid_location

def run_step1():
    print("Step 1: Loading locations.json...")
    try:
        with open("data/build/locations.json", "r", encoding="utf-8") as f:
            raw_locations = json.load(f)
    except FileNotFoundError:
        print("Error: data/build/locations.json not found.")
        return

    # 1. 归一化与聚合
    merged_locations = defaultdict(list)
    print("Normalizing and aggregating locations...")
    
    for name, data in raw_locations.items():
        if not is_valid_location(name):
            continue
            
        norm_name = normalize_location_name(name)
        if not norm_name:
             continue

        data["original_name"] = name
        # Simplify Type
        data["type"] = normalize_location_type(data.get("type", ""))
        
        merged_locations[norm_name].append(data)

    print(f"Reduced {len(raw_locations)} raw locations to {len(merged_locations)} unique entities.")
    
    # Save intermediate result
    output_file = "data/build/locations_step1_aggregated.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(merged_locations, f, indent=2, ensure_ascii=False)
    
    print(f"Saved aggregated data to {output_file}")

if __name__ == "__main__":
    run_step1()
