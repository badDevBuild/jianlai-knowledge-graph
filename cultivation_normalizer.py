"""
修为境界标准化模块

武道境界体系：
1、炼体三境：泥胚境，木胎境，水银境
2、炼气三境：英魂境，雄魄境，武胆境
3、炼神三境：金身境，羽化境，山巅境
4、止境：气盛境，归真境，神到境
5、武神境

练气士境界体系：
1、下五境：铜皮境，草根境，柳筋境，骨气境，铸庐境
2、中五境：洞府境，观海境，龙门境，金丹境，元婴境
3、上五境：玉璞境，仙人境，飞升境，十四境，十五境
"""

import re

# 武道境界标准名称和等级
WUDAO_LEVELS = {
    "泥胚境": 1, "木胎境": 2, "水银境": 3,
    "英魂境": 4, "雄魄境": 5, "武胆境": 6,
    "金身境": 7, "羽化境": 8, "山巅境": 9,
    "止境": 10, "气盛境": 10, "归真境": 11, "神到境": 12,
    "武神境": 13
}

# 练气士境界标准名称和等级
LIANQI_LEVELS = {
    "铜皮境": 1, "草根境": 2, "柳筋境": 3, "骨气境": 4, "铸庐境": 5,
    "洞府境": 6, "观海境": 7, "龙门境": 8, "金丹境": 9, "元婴境": 10,
    "玉璞境": 11, "仙人境": 12, "飞升境": 13, "十四境": 14, "十五境": 15
}

# 武道别名映射 -> 标准境界
WUDAO_ALIASES = {
    # 数字境界
    "一境武夫": "泥胚境", "武道一境": "泥胚境", "一境": "泥胚境",
    "二境武夫": "木胎境", "武道二境": "木胎境", "二境": "木胎境",
    "三境武夫": "水银境", "武道三境": "水银境", "三境": "水银境",
    "四境武夫": "英魂境", "武道四境": "英魂境", "四境": "英魂境", "武道第四境": "英魂境",
    "五境武夫": "雄魄境", "武道五境": "雄魄境", "五境": "雄魄境",
    "六境武夫": "武胆境", "武道六境": "武胆境", "六境": "武胆境",
    "七境武夫": "金身境", "武道七境": "金身境", "七境": "金身境",
    "八境武夫": "羽化境", "武道八境": "羽化境", "八境": "羽化境",
    "九境武夫": "山巅境", "武道九境": "山巅境", "九境": "山巅境",
    "十境武夫": "气盛境", "武道十境": "气盛境", "十境": "气盛境",
    "十一境武夫": "归真境", "武道十一境": "归真境", "十一境": "归真境",
    "十二境武夫": "神到境", "武道十二境": "神到境", "十二境": "神到境",
    # 境界名
    "金身境武夫": "金身境",
    "止境武夫": "止境", "止境气盛一层": "气盛境",
    "止境气盛": "气盛境", "气盛一层": "气盛境",
    "止境归真": "归真境", "归真一层": "归真境",
    "止境神到": "神到境", "神到一层": "神到境",
    # 武夫三境
    "武夫三境": "水银境",
    "武夫四境": "英魂境",
    "武夫五境": "雄魄境",
    "武夫六境": "武胆境",
}

# 练气士别名映射 -> 标准境界
LIANQI_ALIASES = {
    # 剑修/剑仙通常指玉璞境
    "剑仙": "玉璞境",
    # 简称
    "元婴": "元婴境",
    "金丹": "金丹境",
    "玉璞": "玉璞境",
    "仙人": "仙人境",
    "飞升": "飞升境",
    # 数字境界
    "练气士五境": "铸庐境",
    "五境练气士": "铸庐境",
    "下五境": "铸庐境",  # 下五境的顶点
}

# 武道关键词（用于判断是否为武道记录）
WUDAO_KEYWORDS = ['武夫', '武道', '止境', '纯粹武夫', '金身境武夫', '气盛', '归真', '神到']
WUDAO_KEYWORDS.extend(WUDAO_LEVELS.keys())

# 练气士关键词
LIANQI_KEYWORDS = ['剑修', '剑仙', '练气士', '元婴', '玉璞', '仙人', '飞升', '金丹', '洞府', '观海', '龙门']
LIANQI_KEYWORDS.extend(LIANQI_LEVELS.keys())


def normalize_wudao(state: str) -> tuple:
    """
    标准化武道境界
    返回: (标准境界名, 等级) 或 (None, None) 如果无法识别
    """
    # 先尝试别名映射（按长度降序匹配，避免"一境"误匹配"十一境"）
    for alias, standard in sorted(WUDAO_ALIASES.items(), key=lambda x: len(x[0]), reverse=True):
        if alias in state:
            return (standard, WUDAO_LEVELS.get(standard))

    # 再尝试直接匹配标准境界名（同样按长度降序）
    for level_name in sorted(WUDAO_LEVELS.keys(), key=len, reverse=True):
        if level_name in state:
            return (level_name, WUDAO_LEVELS[level_name])

    # 纯粹武夫只是通用称呼，不返回具体境界
    return (None, None)


def normalize_lianqi(state: str) -> tuple:
    """
    标准化练气士境界
    返回: (标准境界名, 等级) 或 (None, None) 如果无法识别
    """
    # 先尝试别名映射（按长度降序匹配）
    for alias, standard in sorted(LIANQI_ALIASES.items(), key=lambda x: len(x[0]), reverse=True):
        if alias in state:
            return (standard, LIANQI_LEVELS.get(standard))

    # 再尝试直接匹配标准境界名（按长度降序）
    for level_name in sorted(LIANQI_LEVELS.keys(), key=len, reverse=True):
        if level_name in state:
            return (level_name, LIANQI_LEVELS[level_name])
    
    # 特殊处理：剑修（未明确境界）
    if "剑修" in state:
        return ("剑修", 0)
    
    # 十四境特殊处理
    if "十四境" in state:
        return ("十四境", 14)
    
    return (None, None)


def classify_cultivation_record(state: str) -> str:
    """
    判断修为记录属于武道还是练气士
    返回: "wudao", "lianqi", "both", "unknown"
    """
    is_wudao = any(kw in state for kw in WUDAO_KEYWORDS)
    is_lianqi = any(kw in state for kw in LIANQI_KEYWORDS)
    
    if is_wudao and is_lianqi:
        return "both"
    elif is_wudao:
        return "wudao"
    elif is_lianqi:
        return "lianqi"
    else:
        return "unknown"


def process_cultivation_log(raw_log: list) -> dict:
    """
    处理原始修为记录，输出标准化的武道和练气士双线记录
    
    规则：
    1. 去除连续重复的境界记录
    2. 保留境界变化的完整轨迹（包括可能的跌境重修）
    3. 过滤掉等级为0的未明确境界
    
    输入: [{"chapter": "第1章", "chapter_id": "1", "state": "二境武夫"}, ...]
    输出: {
        "wudao_log": [{"chapter": "第1章", "chapter_id": "1", "level": "木胎境", "order": 2}, ...],
        "lianqi_log": [...]
    }
    """
    wudao_log = []
    lianqi_log = []
    
    # 用于去除连续重复
    last_wudao_level = None
    last_lianqi_level = None
    
    for entry in raw_log:
        state = entry.get('state', '')
        chapter = entry.get('chapter', '')
        chapter_id = entry.get('chapter_id', '')
        
        category = classify_cultivation_record(state)
        
        if category in ("wudao", "both"):
            level_name, order = normalize_wudao(state)
            # 过滤掉无效境界，去除连续重复
            if level_name and order and order > 0 and level_name != last_wudao_level:
                wudao_log.append({
                    "chapter": chapter,
                    "chapter_id": chapter_id,
                    "level": level_name,
                    "order": order
                })
                last_wudao_level = level_name
        
        if category in ("lianqi", "both"):
            level_name, order = normalize_lianqi(state)
            # 过滤掉无效境界（order=0表示未明确），去除连续重复
            if level_name and order and order > 0 and level_name != last_lianqi_level:
                lianqi_log.append({
                    "chapter": chapter,
                    "chapter_id": chapter_id,
                    "level": level_name,
                    "order": order
                })
                last_lianqi_level = level_name
    
    return {
        "wudao_log": wudao_log,
        "lianqi_log": lianqi_log
    }


if __name__ == "__main__":
    # 测试
    import json
    
    with open('data/build/characters.json', 'r') as f:
        chars = json.load(f)
    
    chen = chars.get('陈平安', {})
    raw_log = chen.get('cultivation_log', [])
    
    result = process_cultivation_log(raw_log)
    
    print("=" * 60)
    print("陈平安 武道修为时间线")
    print("=" * 60)
    for entry in result['wudao_log']:
        print(f"  {entry['chapter']}: {entry['level']} (等级{entry['order']})")
    
    print("\n" + "=" * 60)
    print("陈平安 练气士修为时间线")
    print("=" * 60)
    for entry in result['lianqi_log']:
        print(f"  {entry['chapter']}: {entry['level']} (等级{entry['order']})")
