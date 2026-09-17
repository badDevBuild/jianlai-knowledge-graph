import os
import json
import glob
from collections import defaultdict
from character_merger import CHARACTER_ALIASES, get_canonical_name, merge_character_data
from faction_normalizer import normalize_faction, normalize_faction_multi, is_valid_faction, merge_faction_descriptions, normalize_faction_type
from location_normalizer import normalize_location_name, normalize_location_type, is_valid_location
from relation_normalizer import get_reverse_types

# --- Configuration ---
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DATA_DIR = os.path.join(_BASE_DIR, "data/raw")
BUILD_DIR = os.path.join(_BASE_DIR, "data/build")

def load_json(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {path}: {e}")
        return None

def save_json(data, filename):
    path = os.path.join(BUILD_DIR, filename)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Saved {path}")

def get_sort_key(filepath):
    """从文件名提取数字用于排序，如 '006_第1章 惊蛰.json' -> 6"""
    filename = os.path.basename(filepath)
    prefix = filename.split('_')[0]
    try:
        return int(prefix)
    except (ValueError, IndexError):
        return 999999

def clean_chapter_name(filename):
    """清理章节名，移除数字前缀。如 '006_第1章 惊蛰.json' -> '第1章 惊蛰'"""
    # 移除 .json 后缀
    name = filename.replace('.json', '')
    # 移除数字前缀 (如 006_)
    if '_' in name:
        name = name.split('_', 1)[1]
    return name

def extract_chapter_id(filename):
    """从章节标题提取真实章节号。如 '006_第1章 惊蛰.json' -> '1'"""
    import re
    clean_name = clean_chapter_name(filename)
    # 匹配 "第X章" 模式
    match = re.search(r'第(\d+)章', clean_name)
    if match:
        return match.group(1)
    # 如果没有匹配，返回文件名前缀
    return filename.split('_')[0]

def main():
    if not os.path.exists(BUILD_DIR):
        os.makedirs(BUILD_DIR)

    # 按数字排序文件
    files = sorted(glob.glob(os.path.join(RAW_DATA_DIR, "*.json")), key=get_sort_key)
    print(f"Found {len(files)} raw data files.")

    # --- Data Stores ---
    characters_db = {} # Name -> Profile Object
    items_db = {}      # Name -> Item Object
    locations_db = {}  # Name -> Location Object
    factions_db = {}   # Name -> Faction Object
    timeline_list = [] # List of Event Objects
    
    # --- Processing ---
    for file_path in files:
        filename = os.path.basename(file_path)
        # Extract chapter info roughly "006_第1章 惊蛰.json"
        chapter_id = filename.split('_')[0]
        
        data = load_json(file_path)
        if not data: continue
        
        print(f"Processing {filename}...")
        
        # 1. Characters Merging
        for char in data.get("characters", []):
            name = char.get('name', '')
            if not name: continue
            
            if name not in characters_db:
                characters_db[name] = {
                    "name": name,
                    "aliases": set(),
                    "bio_list": [],  # 收集所有章节的 bio
                    "cultivation_log": [],
                    "factions": set(),
                    "tags": set(),
                    "quotes": [],
                    "relations": {} # Target -> {type, strength, evidence_list}
                }
            
            entry = characters_db[name]
            
            # Aliases
            for alias in char.get("aliases", []):
                entry["aliases"].add(alias)
                
            # Factions - 应用标准化（支持 "/" 拆分多势力）
            raw_faction = char.get("faction", "")
            if raw_faction and raw_faction != "无":
                for nf in normalize_faction_multi(raw_faction):
                    entry["factions"].add(nf)
                
            # Tags
            for tag in char.get("tags", []):
                entry["tags"].add(tag)
            
            # Bio 收集（去重）
            bio = char.get("bio", "").strip()
            if bio and bio not in entry["bio_list"]:
                entry["bio_list"].append(bio)
                
            # Cultivation Log
            cultivation = char.get("cultivation", "")
            if cultivation:
                # Deduplicate consecutive same states? 
                # Ideally yes, but let's just log every mention for now
                entry["cultivation_log"].append({
                    "chapter": clean_chapter_name(filename),
                    "chapter_id": extract_chapter_id(filename),
                    "state": cultivation
                })
                
        # 2. Relations Merging
        for rel in data.get("relations", []):
            src = rel.get("source")
            tgt = rel.get("target")
            if not src or not tgt: continue
            
            # Ensure char entries exist (robustness)
            if src not in characters_db: continue # Skip if source not in char list? Or create stub?
            # Let's assume char extraction handled source creation, but maybe source wasn't in char list?
            # For strictness, only attach relations to existing characters.
            
            entry = characters_db[src]
            
            if tgt not in entry["relations"]:
                entry["relations"][tgt] = {
                    "type": set(),
                    "strength": 0,
                    "evidence": []
                }
            
            rel_entry = entry["relations"][tgt]
            
            # Type (could be list or string in raw data, let's normalize)
            r_type = rel.get("relation")
            if isinstance(r_type, list):
                rel_entry["type"].update(r_type)
            elif isinstance(r_type, str):
                rel_entry["type"].add(r_type)
                
            # Strength
            try:
                strength = int(rel.get("strength", 0))
            except (ValueError, TypeError):
                strength = 0
            rel_entry["strength"] = max(rel_entry["strength"], strength)
            
            # Evidence
            if rel.get("evidence"):
                rel_entry["evidence"].append({
                    "chapter": clean_chapter_name(filename),
                    "text": rel["evidence"]
                })

        # 3. Items Merging
        from item_normalizer import normalize_item_name, is_valid_item # Delayed import to avoid circular dependency if any

        for item in data.get("items", []):
            raw_name = item.get("name")
            if not raw_name: continue
            
            # Application of Item Normalization
            if not is_valid_item(raw_name):
                continue
                
            name = normalize_item_name(raw_name)
            if not name: continue
            
            if name not in items_db:
                items_db[name] = {
                    "name": name,
                    "type": item.get("type", ""),
                    "description": item.get("description", ""),
                    "ownership_log": []
                }
            
            # Ownership
            owner = item.get("owner")
            if owner:
                items_db[name]["ownership_log"].append({
                    "chapter": clean_chapter_name(filename),
                    "owner": owner
                })
                
        # 4. Locations & Factions
        for loc in data.get("locations", []):
            raw_name = loc.get("name")
            if not raw_name: continue
            if not is_valid_location(raw_name):
                continue
            name = normalize_location_name(raw_name)
            if not name: continue
            loc_type = normalize_location_type(loc.get("type", ""))
            if name not in locations_db:
                locations_db[name] = {
                    "name": name,
                    "type": loc_type,
                    "description": loc.get("description", ""),
                    "parent": loc.get("parent", "")
                }
            # Update parent if missing
            if not locations_db[name]["parent"] and loc.get("parent"):
                locations_db[name]["parent"] = loc["parent"]
                
        for fac in data.get("factions", []):
            raw_name = fac.get("name")
            if not raw_name: continue

            # 应用势力名称标准化（支持 "/" 拆分）
            for name in normalize_faction_multi(raw_name):
                if name not in factions_db:
                    factions_db[name] = {
                        "name": name,
                        "type": normalize_faction_type(fac.get("type", "")),
                        "description": fac.get("description", "")
                    }
                else:
                    # 始终合并描述（来自不同章节的信息可能不同）
                    new_desc = fac.get("description", "")
                    if new_desc:
                        factions_db[name]["description"] = merge_faction_descriptions(
                            factions_db[name]["description"],
                            new_desc
                        )

        # 5. Quotes
        for quote in data.get("quotes", []):
            speaker = quote.get("speaker")
            content = quote.get("content")
            if not speaker or not content: continue
            
            if speaker in characters_db:
                characters_db[speaker]["quotes"].append({
                    "content": content,
                    "context": quote.get("context", ""),
                    "chapter": clean_chapter_name(filename)
                })

        # 6. Timeline
        for evt in data.get("events", []):
            evt["source_chapter"] = clean_chapter_name(filename)  # 清理章节名
            evt["chapter_id"] = extract_chapter_id(filename)  # 从章节标题提取真实章节号
            timeline_list.append(evt)

    # --- Post-Processing & Cleaning ---
    
    # 导入境界标准化模块
    from cultivation_normalizer import process_cultivation_log
    
    # --- 人物合并：将别名人物合并到主人物 ---
    print("Merging character aliases...")
    merged_count = 0
    for alias_name, main_name in list(CHARACTER_ALIASES.items()):
        if alias_name in characters_db and main_name in characters_db:
            # 合并数据
            merge_character_data(characters_db[main_name], characters_db[alias_name])
            # 删除别名条目
            del characters_db[alias_name]
            merged_count += 1
            print(f"  合并: {alias_name} -> {main_name}")
        elif alias_name in characters_db and main_name not in characters_db:
            # 主人物不存在，重命名别名为主人物
            characters_db[main_name] = characters_db.pop(alias_name)
            characters_db[main_name]["name"] = main_name
            if isinstance(characters_db[main_name]["aliases"], set):
                characters_db[main_name]["aliases"].add(alias_name)
            else:
                characters_db[main_name]["aliases"].append(alias_name)
            merged_count += 1
            print(f"  重命名: {alias_name} -> {main_name}")
    
    print(f"Merged {merged_count} character aliases.")
    
    # --- 修正关系中的别名引用 ---
    print("Fixing alias references in relations...")
    for name, char in characters_db.items():
        new_relations = {}
        for target, rel_data in char.get("relations", {}).items():
            canonical_target = get_canonical_name(target)
            if canonical_target != target:
                print(f"  关系修正: {name} -> {target} => {name} -> {canonical_target}")
            
            if canonical_target in new_relations:
                # 合并到已存在的关系
                existing = new_relations[canonical_target]
                if isinstance(existing["type"], set):
                    existing["type"].update(rel_data.get("type", set()))
                else:
                    for t in rel_data.get("type", []):
                        if t not in existing["type"]:
                            existing["type"].append(t)
                existing["strength"] = max(existing["strength"], rel_data.get("strength", 0))
                existing["evidence"].extend(rel_data.get("evidence", []))
            else:
                new_relations[canonical_target] = rel_data
        
        char["relations"] = new_relations
    
    # Convert Sets to Lists for JSON serialization
    final_characters = {}
    for name, char in characters_db.items():
        char["aliases"] = list(char["aliases"])
        char["factions"] = sorted(char["factions"])
        char["tags"] = sorted(char["tags"])
        
        # 合并 bio_list 为 bio_summary（用换行符连接，去重后）
        bio_list = char.pop("bio_list", [])
        char["bio_summary"] = "\n\n".join(bio_list) if bio_list else ""
        
        # Clean Relations
        clean_rels = {}
        for tgt, rel_data in char["relations"].items():
            rel_data["type"] = list(rel_data["type"])
            clean_rels[tgt] = rel_data
        char["relations"] = clean_rels
        
        # 标准化修为记录
        if char.get("cultivation_log"):
            processed = process_cultivation_log(char["cultivation_log"])
            char["wudao_log"] = processed["wudao_log"]
            char["lianqi_log"] = processed["lianqi_log"]
            # 保留原始记录供参考
            char["cultivation_log_raw"] = char["cultivation_log"]
            del char["cultivation_log"]
        
        final_characters[name] = char
    
    # --- 自动生成反向关系 ---
    print("Generating reverse relations...")
    reverse_added = 0
    for name, char in final_characters.items():
        for target, rel_data in char.get("relations", {}).items():
            # 检查目标人物是否存在
            if target not in final_characters:
                continue
            
            target_char = final_characters[target]
            
            # 如果目标没有反向关系，自动添加
            if name not in target_char.get("relations", {}):
                target_char["relations"][name] = {
                    "type": get_reverse_types(rel_data["type"]),  # 使用反向类型（师徒→弟子）
                    "strength": rel_data["strength"],
                    "evidence": rel_data["evidence"],
                    "auto_generated": True  # 标记为自动生成
                }
                reverse_added += 1
    
    print(f"Added {reverse_added} reverse relations.")

    # Search index generation moved to after data cleaning steps (see below)

    # --- Save ---
    
    # --- 过滤关系中的无效目标引用 ---
    broken_refs = 0
    for name, char in final_characters.items():
        valid_rels = {}
        for tgt, rel_data in char.get("relations", {}).items():
            if tgt in final_characters:
                valid_rels[tgt] = rel_data
            else:
                broken_refs += 1
        char["relations"] = valid_rels
    if broken_refs:
        print(f"Filtered {broken_refs} broken relation references.")

    # --- 自动应用 AI 总结的简介（如果存在） ---
    BIO_SUMMARIZED_FILE = os.path.join(_BASE_DIR, "data/build/bio_summarized.json")
    if os.path.exists(BIO_SUMMARIZED_FILE):
        print("Applying AI-summarized bios...")
        with open(BIO_SUMMARIZED_FILE, 'r', encoding='utf-8') as f:
            summarized_bios = json.load(f)
        
        applied_count = 0
        for name, new_bio in summarized_bios.items():
            if name in final_characters:
                final_characters[name]['bio_summary'] = new_bio
                applied_count += 1
        
        print(f"Applied {applied_count} AI-summarized bios.")
    
    # --- 自动应用 AI 清洗的元数据（如果存在） ---
    METADATA_CLEANED_FILE = os.path.join(_BASE_DIR, "data/build/metadata_cleaned.json")
    if os.path.exists(METADATA_CLEANED_FILE):
        print("Applying AI-cleaned metadata (Aliases, Factions, Tags)...")
        try:
            with open(METADATA_CLEANED_FILE, 'r', encoding='utf-8') as f:
                cleaned_metadata = json.load(f)
            
            cleaned_count = 0
            for name, data in cleaned_metadata.items():
                if name in final_characters:
                    char = final_characters[name]
                    
                    # 更新 Aliases（直接覆盖）
                    if "aliases" in data:
                        char["aliases"] = data["aliases"]
                    
                    # 更新 Factions（AI 清洗后再进行标准化）
                    if "factions" in data:
                        ai_factions = data["factions"]
                        # 对 AI 清洗后的结果进行标准化和过滤（支持 "/" 拆分）
                        normalized = []
                        for f in ai_factions:
                            normalized.extend(normalize_faction_multi(f))
                        char["factions"] = list(dict.fromkeys(normalized))
                        
                    # 更新 Tags（直接覆盖）
                    if "tags" in data:
                        char["tags"] = data["tags"]
                        
                    cleaned_count += 1
            
            print(f"Applied metadata updates to {cleaned_count} characters.")
        except Exception as e:
            print(f"Error applying cleaned metadata: {e}")

    # --- 自动应用 AI 重写的势力描述（如果存在） ---
    FACTIONS_REWRITTEN_FILE = os.path.join(_BASE_DIR, "data/build/factions_rewritten.json")
    if os.path.exists(FACTIONS_REWRITTEN_FILE):
        print("Applying AI-rewritten faction descriptions...")
        try:
            with open(FACTIONS_REWRITTEN_FILE, 'r', encoding='utf-8') as f:
                rewritten_factions = json.load(f)
            
            rewritten_count = 0
            for name, new_desc in rewritten_factions.items():
                if name in factions_db:
                    factions_db[name]["description"] = new_desc
                    rewritten_count += 1
            
            print(f"Applied {rewritten_count} rewritten faction descriptions.")
        except Exception as e:
            print(f"Error applying rewritten factions: {e}")

    # --- 自动应用势力归属修正（NotebookLM 校验结果）---
    # 注意：必须操作 final_characters（不是 characters_db）
    FACTION_CORRECTIONS_FILE = os.path.join(_BASE_DIR, "data/build/faction_corrections.json")
    if os.path.exists(FACTION_CORRECTIONS_FILE):
        print(f"Applying faction corrections from {FACTION_CORRECTIONS_FILE}...")
        try:
            with open(FACTION_CORRECTIONS_FILE, 'r', encoding='utf-8') as f:
                faction_corrections = json.load(f)

            corrected_count = 0
            for char_name, correct_factions in faction_corrections.items():
                if char_name in final_characters:
                    normalized = []
                    for fac in correct_factions:
                        normalized.extend(normalize_faction_multi(fac))
                    normalized = [f for f in normalized if f]
                    if normalized:
                        final_characters[char_name]["factions"] = list(dict.fromkeys(normalized))
                        corrected_count += 1

            print(f"Applied faction corrections for {corrected_count} characters.")
        except Exception as e:
            print(f"Error applying faction corrections: {e}")

    # --- 自动补全 factions_db（人物引用的势力如果不在库里就创建）---
    auto_added = 0
    for name, char in final_characters.items():
        for fac in char.get("factions", []):
            if fac and fac not in factions_db and is_valid_faction(fac):
                factions_db[fac] = {"name": fac, "type": "其他", "description": ""}
                auto_added += 1
    if auto_added:
        print(f"Auto-added {auto_added} missing factions to factions_db.")

    # --- 用白名单覆盖势力 type（Gemini 提取的 type 不可靠）---
    WHITELIST_PATH = os.path.join(_BASE_DIR, "data/build/faction_whitelist.json")
    if os.path.exists(WHITELIST_PATH):
        try:
            with open(WHITELIST_PATH, 'r', encoding='utf-8') as f:
                wl_data = json.load(f)
            type_overridden = 0
            for std_name, info in wl_data.get("standard_factions", {}).items():
                if std_name in factions_db and "type" in info:
                    if factions_db[std_name]["type"] != info["type"]:
                        factions_db[std_name]["type"] = info["type"]
                        type_overridden += 1
            if type_overridden:
                print(f"Overrode {type_overridden} faction types from whitelist.")
        except Exception as e:
            print(f"Error applying whitelist types: {e}")

    # --- 自动应用 AI 清洗的物品数据（如果存在） ---
    # PREFER items_enriched.json if available
    ITEMS_ENRICHED_FILE = os.path.join(_BASE_DIR, "data/build/items_enriched.json")
    ITEMS_CLEANED_FILE = os.path.join(_BASE_DIR, "data/build/items_cleaned.json")
    
    if os.path.exists(ITEMS_ENRICHED_FILE):
        print(f"Applying Enriched Items from {ITEMS_ENRICHED_FILE}...")
        try:
            with open(ITEMS_ENRICHED_FILE, 'r', encoding='utf-8') as f:
                enriched_items = json.load(f)
            # 对品级进行归一化
            from item_normalizer import normalize_item_grade
            for item_name, item_data in enriched_items.items():
                if "grade" in item_data:
                    item_data["grade"] = normalize_item_grade(item_data["grade"])
            items_db = enriched_items
            print(f"Loaded {len(items_db)} enriched items.")
        except Exception as e:
            print(f"Error applying enriched items: {e}")
            
    elif os.path.exists(ITEMS_CLEANED_FILE):
        print("Applying AI-cleaned items...")
        try:
            with open(ITEMS_CLEANED_FILE, 'r', encoding='utf-8') as f:
                cleaned_items = json.load(f)
            # 对品级进行归一化
            from item_normalizer import normalize_item_grade
            for item_name, item_data in cleaned_items.items():
                if "grade" in item_data:
                    item_data["grade"] = normalize_item_grade(item_data["grade"])
            items_db = cleaned_items
            print(f"Loaded {len(items_db)} cleaned items.")
        except Exception as e:
            print(f"Error applying cleaned items: {e}")

    # --- 自动应用 AI 清洗的地点数据（如果存在） ---
    LOCATIONS_CLEANED_FILE = os.path.join(_BASE_DIR, "data/build/locations_cleaned.json")
    if os.path.exists(LOCATIONS_CLEANED_FILE):
        print("Applying AI-cleaned locations...")
        try:
            with open(LOCATIONS_CLEANED_FILE, 'r', encoding='utf-8') as f:
                cleaned_locations = json.load(f)
            # 替换 locations_db，但需要对 cleaned 数据再跑一遍归一化合并
            normalized_locs = {}
            merged_count = 0
            for raw_name, loc_data in cleaned_locations.items():
                norm_name = normalize_location_name(raw_name)
                if not norm_name or not is_valid_location(raw_name):
                    continue
                loc_data["type"] = normalize_location_type(loc_data.get("type", ""))
                if norm_name in normalized_locs:
                    # 合并：保留描述更长的
                    existing = normalized_locs[norm_name]
                    if len(loc_data.get("description", "")) > len(existing.get("description", "")):
                        loc_data["name"] = norm_name
                        # 保留已有的别名和层级
                        for key in ("aliases", "hierarchy"):
                            if key in existing and key not in loc_data:
                                loc_data[key] = existing[key]
                        normalized_locs[norm_name] = loc_data
                    merged_count += 1
                else:
                    loc_data["name"] = norm_name
                    normalized_locs[norm_name] = loc_data
            locations_db = normalized_locs
            if merged_count:
                print(f"  Merged {merged_count} duplicate locations after normalization.")
            print(f"Loaded {len(locations_db)} cleaned locations.")
        except Exception as e:
            print(f"Error applying cleaned locations: {e}")

    # --- Rebuild Search Index (after all data cleaning) ---
    final_search_index = {}
    
    # Helper to safe get length
    def get_len(obj, key):
        val = obj.get(key)
        if val is None: return 0
        return len(val)

    # Helper to add index entry safely
    def add_index_entry(key, type_, id_, weight, is_alias=False):
        if not key: return
        
        entry = {"type": type_, "id": id_, "weight": weight}
        
        # Conflict Resolution
        if key in final_search_index:
            existing = final_search_index[key]
            
            # Case 1: Existing is Main Name, New is Alias -> SKIP (Protect Main Name)
            if not existing.get("_is_alias", False) and is_alias:
                return
            
            # Case 2: Existing is Alias, New is Main Name -> OVERWRITE
            if existing.get("_is_alias", False) and not is_alias:
                entry["_is_alias"] = False # Mark as main
                final_search_index[key] = entry
                return

            # Case 3: Both are Main Names -> Use type priority
            # character > faction > location > item
            if not existing.get("_is_alias", False) and not is_alias:
                TYPE_PRIORITY = {"character": 4, "faction": 3, "location": 2, "item": 1}
                new_prio = TYPE_PRIORITY.get(type_, 0)
                old_prio = TYPE_PRIORITY.get(existing.get("type", ""), 0)
                if new_prio > old_prio:
                    entry["_is_alias"] = False
                    final_search_index[key] = entry
                return

            # Case 4: Both are Aliases -> Keep Higher Weight
            if existing.get("_is_alias", False) and is_alias:
                if weight > existing.get("weight", 0):
                    entry["_is_alias"] = True
                    final_search_index[key] = entry
                return
        else:
            # New Entry
            entry["_is_alias"] = is_alias
            final_search_index[key] = entry

    # 1. Characters - Main Names
    for name in final_characters.keys():
        char = final_characters[name]
        weight = len(char.get("relations", {})) * 10 + get_len(char, "quotes") + get_len(char, "aliases")
        add_index_entry(name, "character", name, weight, is_alias=False)

    # 2. Characters - Aliases
    for name in final_characters.keys():
        char = final_characters[name]
        weight = len(char.get("relations", {})) * 10 + get_len(char, "quotes") + get_len(char, "aliases")
        for alias in char.get("aliases", []):
            add_index_entry(alias, "character", name, weight, is_alias=True)
            
    # 3. Items
    for name in items_db.keys():
        item = items_db[name]
        weight = 20 + get_len(item, "ownership_log") * 10
        add_index_entry(name, "item", name, weight, is_alias=False)
        for alias in item.get("aliases", []):
             add_index_entry(alias, "item", name, weight, is_alias=True)
        
    # 4. Locations
    for name in locations_db.keys():
        loc = locations_db[name]
        weight = 10 + len(loc.get("description", "") or "") // 20
        add_index_entry(name, "location", name, weight, is_alias=False)
        for alias in loc.get("aliases", []):
             add_index_entry(alias, "location", name, weight, is_alias=True)

    # 5. Factions
    for name in factions_db.keys():
        fac = factions_db[name]
        weight = 10 + len(fac.get("description", "") or "") // 20
        add_index_entry(name, "faction", name, weight, is_alias=False)

    # Clean up temporary field
    for k, v in final_search_index.items():
        if "_is_alias" in v:
            del v["_is_alias"]

    save_json(final_characters, "characters.json")

    # 同步清洗后的数据到 profiles_v3/（build_frontend_data.py 读 profiles_v3/）
    # 同步字段: factions（势力归属）、relations（别名解析+断裂引用过滤后的干净版本）
    # 注意: profiles_v3 文件名可能与 raw 数据名不同（AI 清洗后重命名），
    # 所以需要通过 aliases 字段反查来匹配 raw 名 → profile 文件
    profiles_dir = os.path.join(BUILD_DIR, "profiles_v3")
    if os.path.isdir(profiles_dir):
        # 构建反查索引: raw_name → profile_path（通过 aliases 匹配）
        alias_to_profile_path = {}
        for pf in glob.glob(os.path.join(profiles_dir, "*.json")):
            try:
                with open(pf, 'r', encoding='utf-8') as f:
                    pdata = json.load(f)
                for a in pdata.get("aliases", []) or []:
                    if a not in alias_to_profile_path:
                        alias_to_profile_path[a] = pf
            except Exception as e:
                print(f"  Warning: failed to index {pf}: {e}")

        synced_factions = 0
        synced_relations = 0
        unmatched = 0
        for char_name, char_data in final_characters.items():
            # 优先按文件名直接匹配，其次通过 aliases 反查
            profile_path = os.path.join(profiles_dir, f"{char_name}.json")
            if not os.path.exists(profile_path):
                profile_path = alias_to_profile_path.get(char_name)
            if profile_path and os.path.exists(profile_path):
                try:
                    with open(profile_path, 'r', encoding='utf-8') as f:
                        profile = json.load(f)
                    changed = False
                    if profile.get("factions") != char_data.get("factions"):
                        profile["factions"] = char_data.get("factions", [])
                        synced_factions += 1
                        changed = True
                    if profile.get("relations") != char_data.get("relations"):
                        profile["relations"] = char_data.get("relations", {})
                        synced_relations += 1
                        changed = True
                    if changed:
                        with open(profile_path, 'w', encoding='utf-8') as f:
                            json.dump(profile, f, ensure_ascii=False, indent=2)
                except Exception as e:
                    print(f"  Warning: failed to sync {char_name}: {e}")
            else:
                unmatched += 1
        if synced_factions or synced_relations:
            print(f"Synced to profiles_v3/: {synced_factions} factions, {synced_relations} relations.")
        if unmatched:
            print(f"  ({unmatched} characters had no matching profile — generic/minor names, expected)")

    save_json(items_db, "items.json")
    save_json(locations_db, "locations.json")
    save_json(factions_db, "factions.json")
    save_json(final_search_index, "search_index.json")
    save_json(timeline_list, "timeline.json")

    # --- Item Optimization: Split and Lite ---
    from urllib.parse import quote
    print("Generating optimized item data...")
    items_lite = {}
    items_dir = os.path.join(BUILD_DIR, "items")
    if not os.path.exists(items_dir):
        os.makedirs(items_dir)

    for name, item in items_db.items():
        # 1. Save Full Item Detail
        # Sanitize filename: Just replace / with _ to be safe for FS, keep Chinese chars
        safe_filename = name.replace('/', '_')
        item_path = os.path.join(items_dir, f"{safe_filename}.json")
        with open(item_path, 'w', encoding='utf-8') as f:
            json.dump(item, f, ensure_ascii=False, indent=2)

        # 2. Add to Lite List
        # Calculate current owner
        current_owner = ""
        owners = item.get("ownership_log", [])
        if owners:
            current_owner = owners[-1].get("owner", "")
            
        items_lite[name] = {
            "name": item.get("name"),
            "grade": item.get("grade"),
            "type": item.get("type"),
            "subtype": item.get("subtype", ""), 
            "status": item.get("status", "未知"),
            "icon": item.get("icon"),
            "description": (item.get("description", "") or "")[:60], # Truncate for lite
            "current_owner": current_owner,
            "ownership_count": len(owners)
        }
    
    save_json(items_lite, "items_lite.json")
    print(f"Generated items_lite.json and {len(items_db)} item detail files.")

    print("Knowledge Base Construction Complete.")

if __name__ == "__main__":
    main()
