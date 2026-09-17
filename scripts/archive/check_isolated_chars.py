import json

def main():
    with open('data/build/characters.json', 'r', encoding='utf-8') as f:
        chars = json.load(f)
        
    total_chars = len(chars)
    isolated_chars = []
    
    for name, char in chars.items():
        has_relations = len(char.get('relations', {})) > 0
        has_quotes = len(char.get('quotes', [])) > 0
        
        # 宽容一点，只要有这些中的一个就不算绝对孤立
        has_cultivation = (len(char.get('wudao_log', [])) > 0) or (len(char.get('lianqi_log', [])) > 0) or (len(char.get('cultivation_log_raw', [])) > 0)
        
        # 甚至如果 Bio 很长，也不算孤立（说明是有故事的人，只是没解析出结构化数据）
        bio = char.get('bio_summary', '') or "\n".join(char.get('bio_list', []))
        has_long_bio = len(bio) > 100 
        
        # 严格的“孤立”定义：无关系、无语录、无修为
        if not has_relations and not has_quotes and not has_cultivation:
            isolated_chars.append({
                "name": name,
                "bio_len": len(bio),
                "aliases": char.get('aliases', []),
                "tags": char.get('tags', [])
            })
            
    print(f"Total Characters: {total_chars}")
    print(f"Isolated Characters: {len(isolated_chars)} ({len(isolated_chars)/total_chars*100:.1f}%)")
    
    # Sort by bio length (shortest first are likely the most irrelevant)
    isolated_chars.sort(key=lambda x: x['bio_len'])
    
    print("\nTop 20 Isolated Characters (Shortest Bio):")
    for c in isolated_chars[:20]:
        print(f"  - {c['name']}: BioLen={c['bio_len']}, Tags={c['tags']}")
        
    print("\nTop 20 Isolated Characters (Longest Bio - Potential Missed Info):")
    for c in isolated_chars[-20:]:
        print(f"  - {c['name']}: BioLen={c['bio_len']}, Tags={c['tags']}")

if __name__ == "__main__":
    main()
