import json
import os
import glob
from pathlib import Path

# Paths - 使用绝对路径，避免工作目录依赖
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(_SCRIPT_DIR)
PROFILES_DIR = os.path.join(_PROJECT_DIR, 'data/build/profiles_v3')
IMAGES_DIR = os.path.join(_PROJECT_DIR, 'data/build/character_images')
DIST_DIR = os.path.join(_PROJECT_DIR, 'data/dist')

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def build_data():
    ensure_dir(DIST_DIR)
    chars_dir = os.path.join(DIST_DIR, 'chars')
    ensure_dir(chars_dir)

    profiles = glob.glob(os.path.join(PROFILES_DIR, '*.json'))
    lite_data = {}

    print(f"Found {len(profiles)} profiles in {PROFILES_DIR}")
    
    # 1. Collect all data and group by name to resolve duplicates
    grouped_profiles = {} # name -> list of {path, data}
    
    for profile_path in profiles:
        try:
            with open(profile_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            name = data.get('name')
            if not name:
                continue
                
            if name not in grouped_profiles:
                grouped_profiles[name] = []
            grouped_profiles[name].append({'path': profile_path, 'data': data})
            
        except Exception as e:
            print(f"Error reading {profile_path}: {e}")

    # 2. Process unique characters
    for name, sources in grouped_profiles.items():
        # Pick the best source
        selected_source = None
        
        # Priority 1: Filename matches name (e.g. 陈平安.json for 陈平安)
        for source in sources:
            filename = os.path.basename(source['path'])
            basename = os.path.splitext(filename)[0]
            if basename == name:
                selected_source = source
                break
        
        # Priority 2: Use the source with the most data (largest JSON string)
        if not selected_source:
            # Sort by content length descending
            sources.sort(key=lambda x: len(json.dumps(x['data'])), reverse=True)
            selected_source = sources[0]
            if len(sources) > 1:
                print(f"Warning: Multiple sources for {name}, picked largest: {selected_source['path']}")

        path = selected_source['path']
        data = selected_source['data']
        
        try:

            # Standardize fields for V3
            # Ensure 'cultivation' is present (it is in V3)
            # Ensure 'appearance' is present
            
            # 1. Generate Lite Entry
            # We need: name, avatar, factions, bio_summary (or bio truncated), tags, cultivation state (for list display), relationCount
            
            # Cultivation logic for list view (get highest/current state)
            cultivation_txt = "未知"
            # Legacy support: Generate cultivation_log
            legacy_log = []
            
            if data.get('cultivation'):
                # Try to find the most relevant state. V3 has 'notes' and 'realm'. 
                # Let's pick the first one or search for specific keywords if multiple.
                # Usually array has [Martial, Qi] or just one.
                states = []
                for c in data['cultivation']:
                    level = c.get('realm_name') or c.get('realm')
                    stage = c.get('stage')
                    if level and level != '无':
                        full_state = f"{level} ({stage})" if stage else level
                        states.append(level) # For lite string
                        
                        # Add to legacy log
                        legacy_log.append({
                            "state": full_state,
                            "chapter": c.get('notes', '未知') or '未知',
                            "clean_chapter": "未知"
                        })
                        
                if states:
                    cultivation_txt = "/".join(states)

            # Bio summary
            bio = data.get('bio', '')
            bio_summary = bio[:50] + '...' if len(bio) > 50 else bio
            
            # Relation Count
            relations = data.get('relations', {})
            relation_count = len(relations)

            # 只有当由于 UGC 产生了确定存在于目录中的实体文件时，我们才注册这张原图
            # V3 新增逻辑：如果不存在 UGC 图，但存在 V3 版构建的 webp 头像，则使用 V3 头像
            # 否则留空，让小程序端通过 useData.ts 自动发起 LOCAL_AVATARS 保底或者动态 UI 姓名图片
            avatar_url = ""
            img_search = glob.glob(os.path.join(os.path.dirname(__file__), '..', 'taro-app', 'public', 'data', 'img', 'avatars', f"{name}.*"))
            if img_search:
                actual_ext = os.path.splitext(img_search[0])[1]
                avatar_url = f"https://shushu.host/jianlai/img/avatars/{name}{actual_ext}"
            else:
                v3_search = glob.glob(os.path.join(os.path.dirname(__file__), '..', 'data', 'dist', 'img', 'avatars', f"{name}.*"))
                if v3_search:
                    actual_ext = os.path.splitext(v3_search[0])[1]
                    avatar_url = f"https://shushu.host/jianlai/data/img/avatars/{name}{actual_ext}"

            raw_quotes = data.get('quotes', [])
            raw_aliases = data.get('aliases', [])

            lite_entry = {
                "name": name,
                "avatar": avatar_url, # Production URL
                "factions": data.get('factions', []),
                "bio_summary": bio_summary,
                "tags": data.get('tags', []),
                "cultivation": cultivation_txt,
                "relationCount": relation_count,
                "quotes": raw_quotes,
                "aliases": raw_aliases,
                # Keep counts for backward compat (faction scoring uses these)
                "quotes_count": len(raw_quotes),
                "aliases_count": len(raw_aliases),
            }
            
            lite_data[name] = lite_entry

            # 2. Save Full Character JSON
            # We treat the source V3 JSON as nearly the target, just maybe add the avatar url if we want it self-contained
            data['avatar'] = lite_entry['avatar']
            data['cultivation_log'] = legacy_log # Polyfill for old code
            
            # Save to chars/
            with open(os.path.join(chars_dir, f"{name}.json"), 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"Error processing {profile_path}: {e}")

    # Save Lite Data
    with open(os.path.join(DIST_DIR, 'characters_lite.json'), 'w', encoding='utf-8') as f:
        # Save as dictionary to match current CharactersDB structure
        json.dump(lite_data, f, ensure_ascii=False, indent=2)

    print(f"Generated characters_lite.json with {len(lite_data)} entries.")
    print(f"Generated {len(lite_data)} individual character files in {chars_dir}")

    # Copy relations.json
    relations_src = os.path.join(_PROJECT_DIR, 'taro-app/src/data/relations.json')
    if os.path.exists(relations_src):
        import shutil
        shutil.copy(relations_src, os.path.join(DIST_DIR, 'relations.json'))
        print(f"Copied {relations_src} to {DIST_DIR}")
    else:
        print(f"Warning: {relations_src} not found. Relations graph will be empty.")
    
    # 3. Generate Quotes DB
    all_quotes = []
    print("Generating quotes database...")
    for name, entry in lite_data.items():
         # Load full data to get quotes
         full_path = os.path.join(chars_dir, f"{name}.json")
         try:
            with open(full_path, 'r', encoding='utf-8') as f:
                char_data = json.load(f)
            
            quotes = char_data.get('quotes', [])
            for q in quotes:
                if isinstance(q, dict) and q.get('content'):
                    all_quotes.append({
                        "content": q.get('content'),
                        "context": q.get('context', ''),
                        "author": name,
                        "avatar": entry['avatar']
                    })
                elif isinstance(q, str):
                    all_quotes.append({
                        "content": q,
                        "context": '',
                        "author": name,
                        "avatar": entry['avatar']
                    })
         except Exception as e:
            print(f"Error extracting quotes for {name}: {e}")

    # Merge persisted quote tags (from classify_quotes.py)
    tags_path = os.path.join(_PROJECT_DIR, 'data/build/quote_tags.json')
    if os.path.exists(tags_path):
        with open(tags_path, 'r', encoding='utf-8') as f:
            tag_map = json.load(f)  # {content_hash: tags_list}
        tagged = 0
        for q in all_quotes:
            key = q['content'][:50]  # Use first 50 chars as key
            if key in tag_map:
                q['tags'] = tag_map[key]
                tagged += 1
        print(f"Merged {tagged} quote tags from quote_tags.json")

    with open(os.path.join(DIST_DIR, 'quotes.json'), 'w', encoding='utf-8') as f:
        json.dump(all_quotes, f, ensure_ascii=False, indent=2)
    print(f"Generated quotes.json with {len(all_quotes)} entries.")

    # 4. 复制非人物数据到 dist (locations, items_lite)
    import shutil as _shutil
    BUILD_DIR = os.path.join(_PROJECT_DIR, 'data/build')
    for src_name in ['locations.json', 'items_lite.json', 'items.json',
                      'search_index.json', 'timeline.json']:
        src = os.path.join(BUILD_DIR, src_name)
        dst = os.path.join(DIST_DIR, src_name)
        if os.path.exists(src):
            _shutil.copy2(src, dst)
            print(f"Copied {src_name} to dist")
        else:
            print(f"Warning: {src} not found, skipping.")

    # 4.1 复制单个物品详情 JSON 到 dist/items/
    items_src_dir = os.path.join(BUILD_DIR, 'items')
    items_dst_dir = os.path.join(DIST_DIR, 'items')
    if os.path.isdir(items_src_dir):
        ensure_dir(items_dst_dir)
        item_count = 0
        for fname in os.listdir(items_src_dir):
            if fname.endswith('.json'):
                _shutil.copy2(os.path.join(items_src_dir, fname), os.path.join(items_dst_dir, fname))
                item_count += 1
        print(f"Copied {item_count} individual item files to {items_dst_dir}")
    else:
        print(f"Warning: {items_src_dir} not found, skipping individual items.")

    # 5. 构建 factions.json（预计算 score/members/member_count）
    factions_src = os.path.join(BUILD_DIR, 'factions.json')
    if os.path.exists(factions_src):
        with open(factions_src, 'r', encoding='utf-8') as f:
            factions_raw = json.load(f)

        # 用已构建的 lite_data 计算每个宗派的成员和评分
        # 只匹配 factions_raw 中实际存在的宗派名（过滤掉混入的地点名）
        valid_faction_names = set(factions_raw.keys())
        faction_members = {}   # name -> [(char_name, importance)]
        
        for char_name, char_entry in lite_data.items():
            char_importance = (char_entry.get('relationCount', 0) or 0) * 10 \
                + (char_entry.get('quotes_count', 0) or 0) \
                + (char_entry.get('aliases_count', 0) or 0)
            
            for fac_name in char_entry.get('factions', []):
                if fac_name in valid_faction_names:
                    if fac_name not in faction_members:
                        faction_members[fac_name] = []
                    faction_members[fac_name].append((char_name, char_importance))

        # 境界 → 数值等级映射（用于计算势力等级）
        REALM_RANK = {
            '合道': 15, '十四境': 14, '飞升境': 13, '仙人境': 12,
            '玉璞境': 11, '元婴境': 10, '金丹境': 9, '龙门境': 8,
            '观海境': 7, '洞府境': 6,
            '止境': 14, '山巅境': 13, '远游境': 12, '金身境': 11,
            '山水神灵': 10, '武胆境': 8, '雄魄境': 7,
            '儒家圣人': 14, '儒家圣贤': 13, '剑仙': 13, '地仙': 12,
            '中五境': 8, '下五境': 5, '炼气境': 3,
            '柳筋境': 3, '骨架境': 4, '草根境': 2,
        }

        def get_realm_rank(cultivation_str):
            if not cultivation_str or cultivation_str == '未知':
                return 0
            best = 0
            for realm, rank in REALM_RANK.items():
                if realm in cultivation_str:
                    best = max(best, rank)
            return best

        # 境界等级 → 实力权重（指数递增，顶级差距大，底级差距小）
        def realm_weight(rank):
            if rank <= 0:
                return 0
            return max(1, round(1000 * (2 ** (rank - 15))))

        char_realm_ranks = {}
        for char_name, char_entry in lite_data.items():
            char_realm_ranks[char_name] = get_realm_rank(char_entry.get('cultivation', ''))

        # 加载势力位置数据（由 enrich_faction_locations.py 生成）
        faction_locs_path = os.path.join(BUILD_DIR, 'faction_locations.json')
        faction_locs = {}
        if os.path.exists(faction_locs_path):
            with open(faction_locs_path, 'r', encoding='utf-8') as f:
                faction_locs = json.load(f)
            print(f"Loaded {len(faction_locs)} faction locations from {faction_locs_path}")

        # 为每个宗派计算 score 并附加 members + location
        for name, fac_data in factions_raw.items():
            members_list = faction_members.get(name, [])
            # 按重要性降序排列
            members_list.sort(key=lambda x: x[1], reverse=True)

            member_count = len(members_list)
            total_importance = sum(imp for _, imp in members_list)
            score = member_count * 100 + total_importance

            fac_data['member_count'] = member_count
            fac_data['score'] = score
            fac_data['members'] = [m[0] for m in members_list]

            # 计算势力实力（指数加权求和）
            if members_list:
                member_ranks = [char_realm_ranks.get(m[0], 0) for m in members_list]
                ranked = [r for r in member_ranks if r > 0]
                if ranked:
                    fac_data['power_score'] = sum(realm_weight(r) for r in ranked)

            # 合并位置数据
            if name in faction_locs:
                loc_info = faction_locs[name]
                loc = loc_info.get('location', '未知')
                region = loc_info.get('region', '未知')
                if loc != '未知':
                    fac_data['location'] = loc
                if region != '未知':
                    fac_data['region'] = region

        factions_dst = os.path.join(DIST_DIR, 'factions.json')
        with open(factions_dst, 'w', encoding='utf-8') as f:
            json.dump(factions_raw, f, ensure_ascii=False, indent=2)
        
        # 输出 Top 20 验证
        sorted_factions = sorted(factions_raw.values(), key=lambda x: x.get('score', 0), reverse=True)
        print(f"Generated factions.json with {len(factions_raw)} entries (precomputed scores).")
        print("Top 20 factions by score:")
        for i, fac in enumerate(sorted_factions[:20]):
            print(f"  {i+1}. {fac['name']} (score={fac.get('score',0)}, members={fac.get('member_count',0)}, type={fac.get('type','')})")
    else:
        print(f"Warning: {factions_src} not found, skipping factions.")


if __name__ == "__main__":
    build_data()
