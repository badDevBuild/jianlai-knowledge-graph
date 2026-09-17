
import json
import re
import os

SOURCE_DATA = 'data/build/characters.json'

def load_source_data():
    with open(SOURCE_DATA, 'r', encoding='utf-8') as f:
        return json.load(f)

def is_generic_name(name):
    # Common suffixes for generic roles/types
    suffixes = [
        r"老人$", r"老者$", r"老头$", r"老翁$", r"老妪$", r"婆婆$", r"爷爷$", r"奶奶$", r"祖宗$", r"祖师$",
        r"男子$", r"女子$", r"汉子$", r"妇人$", r"夫子$", r"先生$", r"小姐$", r"夫人$",
        r"少年$", r"少女$", r"童子$", r"孩童$", r"稚童$", r"婴儿$", r"儿$", r"女$",
        r"道士$", r"道人$", r"僧人$", r"和尚$", r"尼姑$", r"剑修$", r"剑仙$", r"武夫$", r"书生$", r"儒生$", r"修?士$",
        r"掌柜$", r"店主$", r"伙计$", r"船夫$", r"车夫$", r"马夫$", r"樵夫$", r"渔夫$", r"厨子$",
        r"城主$", r"宗主$", r"山主$", r"洞主$", r"岛主$", r"谷主$", r"观主$", r"帮主$", r"门主$", r"楼主$", r"府主$",
        r"皇帝$", r"皇$", r"帝$", r"太子$", r"王爷$", r"公主$", r"郡主$", r"娘娘$", r"太后$", r"妃$",
        r"侍郎$", r"尚书$", r"将军$", r"都督$", r"太守$", r"刺史$", r"县令$", r"督造$", r"校尉$", r"捕快$",
        r"师兄$", r"师弟$", r"师姐$", r"师妹$", r"师父$", r"师傅$", r"徒弟$",
        r"大爷$", r"大叔$", r"大娘$", r"大婶$",
        r"氏$", r"朋友$", r"客人$", r"前辈$", r"晚辈$", r"人$", r"鬼$", r"妖$", r"魔$", r"精$", r"怪$", r"神$", r"仙$"
    ]
    
    # Common descriptive prefixes/adjectives check
    # If a name starts with these and ends with a suffix from above, it's very likely generic
    # But even if it just ends with the suffix and is > 2 chars, it might be.
    # We will be aggressive with the regex list above.
    
    # Check "Surname + Title" pattern e.g. "李掌柜", "王大爷" (2-3 chars, starts with surname-like, ends with title)
    # This is harder to distinguish from full names without a surname list, but we can try basic heuristics.
    
    # Check for specific "Adjective + Noun" patterns
    adjectives = [
        r"^白衣", r"^青衫", r"^黑衣", r"^红衣", r"^紫衣", r"^黄衣", r"^绿衣", r"^蓝衣", r"^锦袍", r"^华服",
        r"^中年", r"^年轻", r"^老年", r"^幼年",
        r"^高大", r"^矮小", r"^胖", r"^瘦", r"^魁梧",
        r"^负剑", r"^佩剑", r"^提刀", r"^挎刀", r"^背剑",
        r"^独臂", r"^瘸腿", r"^瞎", r"^盲",
        r"^神秘", r"^陌生", r"^外乡", r"^无名", r"^某", r"那位"
    ]
    
    # 1. Matches generic suffix
    combined_suffix_pattern = "|".join(suffixes)
    if re.search(combined_suffix_pattern, name):
        # Filter out obvious proper names if they match suffix but look like names?
        # E.g. "李老人" might be generic, "陈平安" is distinct.
        # "平安" doesn't match suffixes. 
        # "阿良" doesn't.
        # "老秀才" matches "秀才" (add to list) or "老" prefix.
        return True

    # 2. Starts with generic adjective
    combined_adj_pattern = "|".join(adjectives)
    if re.search(combined_adj_pattern, name):
        return True
        
    return False

def main():
    if not os.path.exists(SOURCE_DATA):
        print(f"Error: {SOURCE_DATA} not found.")
        return

    full_data = load_source_data()
    
    generic_candidates = []
    
    for name in full_data.keys():
        if is_generic_name(name):
            generic_candidates.append(name)
            
    # Sort for easier reading
    generic_candidates.sort()
    
    print(f"Found {len(generic_candidates)} potential generic names/titles.")
    print("-" * 30)
    
    # Print sample
    for name in generic_candidates[:100]:
        print(name)
    if len(generic_candidates) > 100:
        print(f"... and {len(generic_candidates) - 100} more.")

    # Save to file
    with open("data/build/generic_names_list.txt", "w", encoding='utf-8') as f:
        for name in generic_candidates:
            f.write(name + "\n")
            
    print("-" * 30)
    print("List saved to data/build/generic_names_list.txt")

if __name__ == "__main__":
    main()
