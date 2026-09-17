
import json
import os
from collections import defaultdict

INPUT_FILE = "/Users/shushu/剑来/relations_full.json"
OUTPUT_FILE = "/Users/shushu/剑来/relations_clean.json"

# Manually defined aliases map (Canonical -> [List of aliases])
# We can expand this list over time or use LLM to generate it.
ALIAS_MAP = {
    "陈平安": ["草鞋少年", "陈姓少年", "泥瓶巷少年", "姓陈的"],
    "刘羡阳": ["高大少年", "刘姓少年"],
    "姚老头": ["老姚头", "老师傅", "姚师傅"],
    "宋集薪": ["青衫少年", "邻居少年"],
    "稚圭": ["王朱", "少女", "婢女"],
    "齐静春": ["齐先生", "教书先生", "中年儒士"],
    "李槐": ["鼻涕虫", "鼻涕虫男孩"],
    "李柳": ["李姑娘"],
    "阮邛": ["阮师傅", "阮姓铁匠", "铁匠"],
    "宁姚": ["锦衣少年", "头戴古怪高冠的年轻人"] # Early chapters disguise
}

# Reverse map for easy lookup
REVERSE_ALIAS_MAP = {}
for canonical, aliases in ALIAS_MAP.items():
    REVERSE_ALIAS_MAP[canonical] = canonical
    for alias in aliases:
        REVERSE_ALIAS_MAP[alias] = canonical

def normalize_name(name):
    """Normalize a name to its canonical form if it exists in the map."""
    name = name.strip()
    return REVERSE_ALIAS_MAP.get(name, name)

def process_data():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found.")
        return

    print(f"Reading {INPUT_FILE}...")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    # Dictionary to store aggregated relationships
    # Key: tuple(sorted(source, target)) -> to handle undirected nature
    # But wait, some relations are directed (Master -> Disciple).
    # However, for a force-directed graph, we usually treat edges as undirected visually,
    # or we keep direction. Let's keep direction for specific types, but generally aggregating
    # Source-Target and Target-Source might be better for a clean overview graph.
    # CONSTANT DECISION: We will normalize Source/Target alphabetically to merge A->B and B->A 
    # into a single connection with combined info.
    
    aggregated = {}

    for item in raw_data:
        s_raw = item.get('source', '').strip()
        t_raw = item.get('target', '').strip()
        
        if not s_raw or not t_raw: continue
        
        s = normalize_name(s_raw)
        t = normalize_name(t_raw)
        
        if s == t: continue # Self-loops usually not needed
        
        # PREVIOUSLY: key = tuple(sorted([s, t]))
        # FIX: Do not sort. Keep direction A->B distinct from B->A
        key = (s, t)
        
        if key not in aggregated:
            aggregated[key] = {
                "source": s,
                "target": t,
                "relations": set(),
                "strength": 0,
                "evidence_list": [],
                "occurrences": 0
            }
            
        entry = aggregated[key]
        
        # Merge Relations
        rels = item.get('relation', [])
        if isinstance(rels, str): rels = [rels]
        for r in rels:
            entry["relations"].add(r)
            
        # Max Strength
        entry["strength"] = max(entry["strength"], item.get("strength", 0))
        
        # Append Evidence
        evidence = item.get("evidence", "")
        if evidence:
            entry["evidence_list"].append(evidence)
            
        entry["occurrences"] += 1

    # Convert to list for JSON output
    clean_data = []
    
    print(f"Aggregating {len(raw_data)} raw entries into {len(aggregated)} unique relationships...")
    
    for key, val in aggregated.items():
        # Sort evidence to be nice
        # We can limit evidence to top 5 to save space if needed, strictly generic for now.
        
        final_obj = {
            "source": val["source"],
            "target": val["target"],
            "relation": list(val["relations"]), # Convert set to list
            "strength": val["strength"],
            "evidence": val["evidence_list"], # Keep as list for frontend to render nicely
            "weight": val["occurrences"] # useful for graph line thickness
        }
        clean_data.append(final_obj)

    # Sort by strength descending for interest
    clean_data.sort(key=lambda x: x["strength"], reverse=True)

    print(f"Writing {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(clean_data, f, ensure_ascii=False, indent=2)
        
    print("Done!")

if __name__ == "__main__":
    process_data()
