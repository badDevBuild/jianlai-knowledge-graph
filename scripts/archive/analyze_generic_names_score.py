
import json
import os

GENERIC_LIST = 'data/build/generic_names_list.txt'
SOURCE_DATA = 'data/build/characters.json'

def load_data():
    with open(SOURCE_DATA, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_generic_list():
    with open(GENERIC_LIST, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

def main():
    if not os.path.exists(SOURCE_DATA) or not os.path.exists(GENERIC_LIST):
        print("Data files not found.")
        return

    full_data = load_data()
    generic_names = load_generic_list()
    
    scored_generics = []
    
    for name in generic_names:
        if name in full_data:
            details = full_data[name]
            score = len(details.get('quotes', [])) + len(details.get('relations', []))
            scored_generics.append((name, score))
        else:
            # Should not happen if list came from characters.json
            scored_generics.append((name, 0))
            
    # Sort by score descending
    scored_generics.sort(key=lambda x: x[1], reverse=True)
    
    print(f"Analyzed {len(scored_generics)} generic names.")
    print("-" * 40)
    print("TOP 20 'Generic' Names (High Importance):")
    for name, score in scored_generics[:20]:
        print(f"  {name}: {score}")
        
    print("-" * 40)
    print("BOTTOM 20 'Generic' Names (Low Importance):")
    for name, score in scored_generics[-20:]:
        print(f"  {name}: {score}")
        
    # Stats - User Threshold is 2
    high_score = len([x for x in scored_generics if x[1] >= 2])
    low_score = len([x for x in scored_generics if x[1] < 2])
    
    print("-" * 40)
    print(f"Candidates with Score >= 2 (KEEP): {high_score}")
    print(f"Candidates with Score < 2 (DROP/BLOCK): {low_score}")
    
    # Save BLOCKLIST
    blocklist_path = "data/build/profile_generation_blocklist.txt"
    with open(blocklist_path, "w", encoding='utf-8') as f:
        for name, score in scored_generics:
            if score < 2:
                f.write(f"{name}\n")
            
    print(f"\nBlocklist saved to {blocklist_path} ({low_score} names)")

if __name__ == "__main__":
    main()
