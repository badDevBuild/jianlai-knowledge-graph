import json
from collections import defaultdict
from item_normalizer import normalize_item_name, is_valid_item

def run_step1():
    print("Step 1: Loading items.json...")
    with open("data/build/items.json", "r", encoding="utf-8") as f:
        raw_items = json.load(f)

    # 1. 归一化与聚合 (Normalization & Aggregation)
    merged_items = defaultdict(list)
    print("Normalizing and aggregating items...")
    
    for name, data in raw_items.items():
        if not is_valid_item(name):
            continue
            
        norm_name = normalize_item_name(name)
        if not norm_name:
             continue

        data["original_name"] = name # Keep track of original name
        merged_items[norm_name].append(data)

    print(f"Reduced {len(raw_items)} raw items to {len(merged_items)} unique entities.")
    
    # Save intermediate result
    output_file = "data/build/items_step1_aggregated.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(merged_items, f, indent=2, ensure_ascii=False)
    
    print(f"Saved aggregated data to {output_file}")

if __name__ == "__main__":
    run_step1()
