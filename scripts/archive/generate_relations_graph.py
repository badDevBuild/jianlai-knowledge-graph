import json
import os
import sys
import glob
from pathlib import Path

# 添加项目根目录到 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from relation_normalizer import normalize_relation_type

# Paths
PROFILES_DIR = 'data/build/profiles_v3'
OUTPUT_FILE = 'data/dist/relations.json'
SRC_OUTPUT_FILE = 'taro-app/src/data/relations.json'

def generate_graph():
    print(f"Scanning profiles in {PROFILES_DIR}...")
    profiles = glob.glob(os.path.join(PROFILES_DIR, '*.json'))
    print(f"Found {len(profiles)} profiles.")
    
    edges = []
    
    for profile_path in profiles:
        try:
            with open(profile_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            source = data.get('name')
            relations = data.get('relations', {})
            
            if not source or not relations:
                continue
                
            for target, details in relations.items():
                # Extract clean relation type
                # 'details' is like { "type": ["师徒"], "strength": 10, ... }
                
                relation_list = details.get('type', [])
                
                # Check for self-loops or empty taragets
                if source == target or not target:
                    continue

                edge = {
                    "source": source,
                    "target": target,
                    "relation": relation_list,
                    "category": normalize_relation_type(relation_list),
                    "strength": details.get('strength', 1),
                    "weight": details.get('strength', 1)
                }
                edges.append(edge)
                
        except Exception as e:
            print(f"Error reading {profile_path}: {e}")

    # Deduplicate edges
    unique_edges = []
    seen = set()
    
    for edge in edges:
        # Signature: Source|Target
        # We perform a rough check to avoid exact duplicates
        sig = f"{edge['source']}|{edge['target']}"
        if sig in seen:
            continue
        seen.add(sig)
        unique_edges.append(edge)
    
    print(f"Generated {len(unique_edges)} unique edges.")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    os.makedirs(os.path.dirname(SRC_OUTPUT_FILE), exist_ok=True)
    
    # Write to dist (Minified)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(unique_edges, f, ensure_ascii=False, indent=None, separators=(',', ':'))
    
    # Write to src (Minified)
    with open(SRC_OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(unique_edges, f, ensure_ascii=False, indent=None, separators=(',', ':'))

        
    print(f"Saved to {OUTPUT_FILE} and {SRC_OUTPUT_FILE}")

if __name__ == "__main__":
    generate_graph()
