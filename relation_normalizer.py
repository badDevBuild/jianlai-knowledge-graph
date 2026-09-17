"""关系类型标准化模块。

从 data/build/relation_type_map.json 加载权威映射，提供:
- normalize_relation_type(relation_list) → 语义类别
- get_category_color(category) → 颜色 hex
- get_all_categories() → 类别元数据 dict
- get_reverse_types(type_list) → 反向关系类型列表
"""

import os as _os
import json as _json
from collections import Counter as _Counter

# ── 模块级加载 ────────────────────────────────────────

_MAP_PATH = _os.path.join(
    _os.path.dirname(_os.path.abspath(__file__)),
    "data", "build", "relation_type_map.json"
)

_EXACT_MAP = {}
_FALLBACK_PATTERNS = []
_REVERSE_PAIRS = {}
_CATEGORIES = {}

if _os.path.exists(_MAP_PATH):
    try:
        with open(_MAP_PATH, "r", encoding="utf-8") as _f:
            _data = _json.load(_f)
        _EXACT_MAP = _data.get("exact_map", {})
        _FALLBACK_PATTERNS = _data.get("fallback_patterns", [])
        _REVERSE_PAIRS = _data.get("reverse_pairs", {})
        _CATEGORIES = _data.get("categories", {})
    except Exception as _e:
        print(f"Warning: Failed to load relation type map: {_e}")
else:
    print(f"Warning: relation_type_map.json not found at {_MAP_PATH}")


# ── 公开函数 ──────────────────────────────────────────

def normalize_relation_type(relation_list):
    """将 relation 数组归并为单一语义类别。

    relation_list: ["师徒/利用", "信任"]
    → 展开为原子: ["师徒", "利用", "信任"]
    → Pass 1: exact_map 精确匹配（第一个命中即返回）
    → Pass 2: fallback_patterns 子串匹配
    → 兜底: "其他"
    """
    # 先展开所有原子
    atoms = []
    for compound in relation_list:
        for atom in compound.split("/"):
            atom = atom.strip()
            if atom:
                atoms.append(atom)

    # Pass 1: 精确匹配
    for atom in atoms:
        if atom in _EXACT_MAP:
            return _EXACT_MAP[atom]

    # Pass 2: 子串匹配
    for atom in atoms:
        for pattern in _FALLBACK_PATTERNS:
            keyword = pattern["contains"]
            excludes = pattern.get("exclude", [])
            if keyword in atom and atom not in excludes:
                return pattern["category"]

    return "其他"


def get_category_color(category):
    """返回类别对应的颜色 hex。"""
    info = _CATEGORIES.get(category, _CATEGORIES.get("其他", {}))
    return info.get("color", "#c0bdb5")


def get_all_categories():
    """返回完整的类别元数据 dict。"""
    return dict(_CATEGORIES)


def get_reverse_types(type_list):
    """将类型列表中的有方向性类型翻转为反向形式。

    对称关系（友谊、敌对等）保持不变，
    有方向性的（师徒→弟子、父子→子父等）按 reverse_pairs 翻转。
    """
    result = []
    for compound in type_list:
        parts = compound.split("/")
        reversed_parts = []
        for part in parts:
            part = part.strip()
            reversed_parts.append(_REVERSE_PAIRS.get(part, part))
        result.append("/".join(reversed_parts))
    return result


# ── __main__: 覆盖率报告 ─────────────────────────────

if __name__ == "__main__":
    import sys

    # 加载 relations.json
    rel_path = _os.path.join(
        _os.path.dirname(_os.path.abspath(__file__)),
        "data", "dist", "relations.json"
    )
    if not _os.path.exists(rel_path):
        print(f"Error: {rel_path} not found")
        sys.exit(1)

    with open(rel_path, "r", encoding="utf-8") as f:
        relations = _json.load(f)

    print(f"Loaded {len(relations)} relations from {rel_path}")
    print(f"Exact map entries: {len(_EXACT_MAP)}")
    print(f"Fallback patterns: {len(_FALLBACK_PATTERNS)}")
    print(f"Reverse pairs: {len(_REVERSE_PAIRS)}")
    print()

    # 原子级统计
    atom_counter = _Counter()
    for rel in relations:
        for compound in rel.get("relation", []):
            for atom in compound.split("/"):
                atom = atom.strip()
                if atom:
                    atom_counter[atom] += 1

    mapped_atoms = sum(c for a, c in atom_counter.items() if a in _EXACT_MAP)
    total_atoms = sum(atom_counter.values())
    print(f"=== 原子级覆盖 ===")
    print(f"  精确匹配: {mapped_atoms}/{total_atoms} ({100*mapped_atoms/total_atoms:.1f}%)")
    print(f"  映射条目: {len([a for a in atom_counter if a in _EXACT_MAP])}/{len(atom_counter)}")
    print()

    # 边级统计
    cat_counts = _Counter()
    unmapped_atoms = _Counter()
    for rel in relations:
        cat = normalize_relation_type(rel.get("relation", []))
        cat_counts[cat] += 1
        if cat == "其他":
            for compound in rel.get("relation", []):
                for atom in compound.split("/"):
                    atom = atom.strip()
                    if atom and atom not in _EXACT_MAP:
                        unmapped_atoms[atom] += 1

    total_edges = len(relations)
    mapped_edges = total_edges - cat_counts.get("其他", 0)
    print(f"=== 边级覆盖 ===")
    print(f"  已归类: {mapped_edges}/{total_edges} ({100*mapped_edges/total_edges:.1f}%)")
    print(f"  未归类(其他): {cat_counts.get('其他', 0)}")
    print()

    print(f"=== 类别分布 ===")
    for cat, count in cat_counts.most_common():
        color = get_category_color(cat)
        print(f"  {cat} [{color}]: {count} ({100*count/total_edges:.1f}%)")

    if unmapped_atoms:
        print(f"\n=== 未映射高频原子 (Top 30) ===")
        for atom, count in unmapped_atoms.most_common(30):
            print(f"  {atom}: {count}")
