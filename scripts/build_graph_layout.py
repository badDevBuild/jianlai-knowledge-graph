#!/usr/bin/env python3
"""
构建关系图谱布局数据 (graph_layout.json)

从 data/dist/ 读取势力和关系数据，预计算：
1. 势力分级分类（世界级/组织级/小型）
2. 势力间关系强度
3. 势力级 force-directed 布局坐标
4. 势力内人物布局坐标
5. 关系类型归并映射

输入: data/dist/factions.json + data/dist/relations.json
输出: data/dist/graph_layout.json

不修改任何现有文件，仅生成新文件。
"""

import json
import math
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone

# 添加项目根目录到 path，以便导入 relation_normalizer
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from relation_normalizer import normalize_relation_type, get_category_color, get_all_categories

# ── 配置 ──────────────────────────────────────────────

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DIST_DIR = os.path.join(PROJECT_ROOT, "data", "dist")

FACTIONS_PATH = os.path.join(DIST_DIR, "factions.json")
RELATIONS_PATH = os.path.join(DIST_DIR, "relations.json")
OUTPUT_PATH = os.path.join(DIST_DIR, "graph_layout.json")

# Layer 0 最多显示多少个势力气泡
MAX_FACTIONS = 80

# 最小成员数阈值（低于此的势力归入"江湖散修"）
MIN_MEMBERS = 3

# 世界级实体名单（人工标注 —— 这些不是具体势力组织）
WORLD_LEVEL_NAMES = {
    "浩然天下", "青冥天下", "蛮荒天下", "西方佛国", "莲花天下",
    "流霞天下", "噍吧天下",
}

# 势力类型 → 颜色（Layer 0 气泡颜色）
FACTION_TYPE_COLORS = {
    "宗门": "#5d7a5d",     # 竹青
    "王朝": "#b03a2e",     # 朱砂
    "军事组织": "#4a5568",  # 铁灰
    "教派": "#b8860b",     # 赭石
    "书院": "#485a6c",     # 靛青
    "家族": "#7a6e5d",     # 栗壳
    "跨界组织": "#6b4c6e",  # 紫檀
    "神道势力": "#8b7355",  # 古铜
    "地方势力": "#6b8e7b",  # 青铜
    "江湖门派": "#5a5a5a",  # 灰墨
    "商业组织": "#8b6914",  # 暗金
    "官方机构": "#4a6670",  # 墨蓝
    "妖族势力": "#8b0000",  # 暗红
    "其他": "#999999",     # 淡墨
}


# ── 数据加载 ─────────────────────────────────────────

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ── 势力分类与筛选 ────────────────────────────────────

def classify_factions(factions_dict):
    """将势力分为世界级、组织级、小型三类，返回可渲染的组织级势力列表。"""

    world_level = []
    organizational = []
    small = []

    for name, data in factions_dict.items():
        members = data.get("members", [])
        member_count = len(members)

        if name in WORLD_LEVEL_NAMES:
            world_level.append((name, data))
        elif member_count >= MIN_MEMBERS:
            organizational.append((name, data))
        else:
            small.append((name, data))

    # 按 score（综合重要性）排序，取 top N
    organizational.sort(key=lambda x: x[1].get("score", 0), reverse=True)
    selected = organizational[:MAX_FACTIONS]

    print(f"  世界级实体（排除）: {len(world_level)} 个")
    print(f"  组织级势力: {len(organizational)} 个 → 取 Top {MAX_FACTIONS}: {len(selected)} 个")
    print(f"  小型势力（归入散修）: {len(small)} 个")

    return selected, world_level, small


# ── 人物势力归属 ──────────────────────────────────────

def build_char_faction_map(selected_factions):
    """构建人物 → 势力映射。

    直接使用 dist/factions.json 的 members 列表（唯一数据源，与势力页面一致）。
    人物可以属于多个势力。
    """
    char_to_factions = defaultdict(set)
    faction_members_set = {}

    for fname, fdata in selected_factions:
        members = set(fdata.get("members", []))
        faction_members_set[fname] = members
        for m in members:
            char_to_factions[m].add(fname)

    char_factions_final = {}
    for char, fset in char_to_factions.items():
        char_factions_final[char] = list(fset)

    print(f"  从 factions.json members 直接取: {len(char_factions_final)} 个人物")

    return char_factions_final, faction_members_set


# ── 势力间关系强度 ────────────────────────────────────

def compute_faction_edges(selected_factions, relations, char_factions_map):
    """计算势力间的关系强度（跨势力关系数）。"""

    faction_names = {fname for fname, _ in selected_factions}
    edge_counter = Counter()

    for r in relations:
        s_factions = char_factions_map.get(r["source"], [])
        t_factions = char_factions_map.get(r["target"], [])
        for sf in s_factions:
            for tf in t_factions:
                if sf != tf and sf in faction_names and tf in faction_names:
                    key = tuple(sorted([sf, tf]))
                    edge_counter[key] += 1

    edges = []
    for (f1, f2), count in edge_counter.most_common():
        if count >= 2:  # 至少 2 条跨势力关系才画线
            edges.append({
                "source": f1,
                "target": f2,
                "strength": count,
            })

    return edges


# ── 布局计算（纯 Python，不依赖 networkx）─────────────

def force_directed_layout(nodes, edges, width=1.0, height=1.0, iterations=500):
    """多环布局：大势力在内环，小势力在外环，充分利用画布空间。

    nodes: [{"id": str, "size": float}]  按重要性降序排列
    edges: [{"source": str, "target": str, "strength": float}]

    返回: {node_id: (x, y)}
    """
    import random

    positions = {}
    n = len(nodes)
    if n == 0:
        return positions

    cx, cy = width / 2, height / 2

    # 按大小降序排列
    sorted_nodes = sorted(nodes, key=lambda nd: nd["size"], reverse=True)

    # 前 3 个最大的放中心区域（紧凑三角形）
    center_count = min(3, n)
    center_angles = [-math.pi / 2, math.pi / 6, 5 * math.pi / 6]
    for i in range(center_count):
        if i == 0:
            positions[sorted_nodes[0]["id"]] = [cx, cy]
        else:
            r = 0.1
            positions[sorted_nodes[i]["id"]] = [
                cx + r * math.cos(center_angles[i]),
                cy + r * math.sin(center_angles[i]),
            ]

    # 其余分多环放置
    remaining = sorted_nodes[center_count:]
    ring = 1
    idx = 0
    while idx < len(remaining):
        # 每环容量：内环少、外环多
        capacity = 6 + 4 * ring
        ring_nodes = remaining[idx:idx + capacity]

        # 环半径：从 0.18 开始，每环递增 0.10，最大到边缘
        radius = 0.15 + ring * 0.10
        max_radius = min(width, height) / 2 - 0.04
        radius = min(radius, max_radius)

        for i, nd in enumerate(ring_nodes):
            angle = (2 * math.pi * i / len(ring_nodes)) - math.pi / 2
            # 随机抖动避免太规整
            random.seed(hash(nd["id"]) & 0xFFFFFFFF)
            jitter_r = radius * random.uniform(-0.02, 0.02)
            jitter_a = random.uniform(-0.1, 0.1)
            x = cx + (radius + jitter_r) * math.cos(angle + jitter_a)
            y = cy + (radius + jitter_r) * math.sin(angle + jitter_a)
            # 边界钳制
            margin = nd["size"] + 0.02
            x = max(margin, min(width - margin, x))
            y = max(margin, min(height - margin, y))
            positions[nd["id"]] = [x, y]

        idx += capacity
        ring += 1

    return positions


def circular_layout(members, cx, cy, radius):
    """在圆形区域内为成员分配位置。重要性高的靠近中心。"""
    if not members:
        return {}

    # 按重要性排序
    sorted_members = sorted(members, key=lambda m: m["importance"], reverse=True)
    positions = {}

    for i, m in enumerate(sorted_members):
        if i == 0:
            # 最重要的在中心
            positions[m["name"]] = (cx, cy)
        else:
            # 其余按螺旋分布
            ring = (i - 1) // 8 + 1  # 每环8个
            angle_offset = (i - 1) % 8
            angle = (angle_offset / 8) * 2 * math.pi + ring * 0.3
            r = radius * (0.3 + 0.7 * ring / max(len(sorted_members) // 8, 1))
            r = min(r, radius * 0.9)
            positions[m["name"]] = (
                cx + r * math.cos(angle),
                cy + r * math.sin(angle),
            )

    return positions


# ── 关系类型统计 ──────────────────────────────────────

def compute_relation_type_stats(relations):
    """统计关系类型归并结果（使用 relation_normalizer 统一映射）。"""
    category_counts = Counter()
    unmapped_atoms = Counter()

    for r in relations:
        cat = normalize_relation_type(r.get("relation", []))
        category_counts[cat] += 1
        if cat == "其他":
            for compound in r.get("relation", []):
                for atom in compound.split("/"):
                    atom = atom.strip()
                    if atom:
                        unmapped_atoms[atom] += 1

    return category_counts, unmapped_atoms


# ── 主流程 ────────────────────────────────────────────

def main():
    print("=" * 60)
    print("构建关系图谱布局数据")
    print("=" * 60)

    # 1. 加载数据
    print("\n[1/6] 加载数据...")
    factions = load_json(FACTIONS_PATH)
    relations = load_json(RELATIONS_PATH)
    print(f"  势力: {len(factions)} 个")
    print(f"  关系: {len(relations)} 条")

    # 2. 势力分类与筛选
    print("\n[2/6] 势力分类与筛选...")
    selected, world_level, small = classify_factions(factions)
    selected_names = [name for name, _ in selected]
    print(f"  选中势力: {', '.join(selected_names[:10])}...")

    # 3. 构建人物-势力映射
    print("\n[3/6] 构建人物-势力映射...")
    char_factions_map, faction_members_set = build_char_faction_map(selected)

    # 计算每个人物的关系数（用于重要性）
    char_rel_count = Counter()
    for r in relations:
        char_rel_count[r["source"]] += 1
        char_rel_count[r["target"]] += 1

    # 添加 "江湖散修" 兜底组：未分配但有 5+ 关系的人物
    unassigned_important = []
    for char, count in char_rel_count.items():
        if char not in char_factions_map and count >= 5:
            unassigned_important.append(char)
            char_factions_map[char] = ["江湖散修"]

    if unassigned_important:
        print(f"  江湖散修（兜底）: {len(unassigned_important)} 人")
        selected.append(("江湖散修", {
            "name": "江湖散修",
            "type": "其他",
            "description": "未归属于特定势力的重要人物",
            "members": unassigned_important,
            "score": 0,
        }))

    total_assigned = len(char_factions_map)

    # 统计每个势力的实际渲染成员数（人物可出现在多个势力中）
    faction_render_members = defaultdict(list)
    for char, flist in char_factions_map.items():
        for faction in flist:
            faction_render_members[faction].append({
                "name": char,
                "importance": char_rel_count.get(char, 0),
            })

    # 过滤掉分配后 0 成员的势力
    before = len(selected)
    selected = [(fname, fdata) for fname, fdata in selected
                if len(faction_render_members.get(fname, [])) > 0]
    removed = before - len(selected)
    if removed:
        print(f"  移除 {removed} 个空势力（分配后 0 成员）")

    print(f"  已分配人物: {total_assigned} / ~1600")
    for fname, _ in selected[:5]:
        mc = len(faction_render_members.get(fname, []))
        print(f"    {fname}: {mc} 人")

    # 4. 计算势力间关系
    print("\n[4/6] 计算势力间关系强度...")
    faction_edges = compute_faction_edges(selected, relations, char_factions_map)
    print(f"  跨势力关系线: {len(faction_edges)} 条")
    for e in faction_edges[:5]:
        print(f"    {e['source']} ↔ {e['target']}: {e['strength']} 条关系")

    # 5. 计算布局
    print("\n[5/6] 计算布局坐标...")

    # 5a. 势力级布局
    faction_nodes = []
    for fname, fdata in selected:
        mc = len(faction_render_members.get(fname, []))
        # 气泡半径正比于 sqrt(成员数)
        radius = 0.02 + 0.06 * math.sqrt(mc) / math.sqrt(120)
        faction_nodes.append({
            "id": fname,
            "size": radius,
        })

    faction_positions = force_directed_layout(faction_nodes, faction_edges)

    # 5b. 势力内人物布局
    faction_data_list = []
    for fname, fdata in selected:
        pos = faction_positions.get(fname, (0.5, 0.5))
        members = faction_render_members.get(fname, [])
        mc = len(members)
        radius = 0.02 + 0.06 * math.sqrt(mc) / math.sqrt(120)

        # 人物布局
        member_positions = circular_layout(members, pos[0], pos[1], radius)

        member_list = []
        for m in sorted(members, key=lambda x: x["importance"], reverse=True):
            mpos = member_positions.get(m["name"], (pos[0], pos[1]))
            member_list.append({
                "name": m["name"],
                "x": round(mpos[0], 4),
                "y": round(mpos[1], 4),
                "importance": m["importance"],
            })

        faction_data_list.append({
            "id": fname,
            "x": round(pos[0], 4),
            "y": round(pos[1], 4),
            "radius": round(radius, 4),
            "memberCount": mc,
            "type": fdata.get("type", "其他"),
            "color": FACTION_TYPE_COLORS.get(fdata.get("type", "其他"), "#999999"),
            "members": member_list,
        })

    # 6. 关系类型统计
    print("\n[6/6] 关系类型归并统计...")
    cat_counts, unmapped = compute_relation_type_stats(relations)
    mapped_total = sum(v for k, v in cat_counts.items() if k != "其他")
    unmapped_total = cat_counts.get("其他", 0)
    print(f"  已归类: {mapped_total} ({100*mapped_total/len(relations):.1f}%)")
    print(f"  未归类（其他）: {unmapped_total} ({100*unmapped_total/len(relations):.1f}%)")
    all_categories = get_all_categories()
    print(f"  类别分布:")
    for cat, count in cat_counts.most_common():
        color = get_category_color(cat)
        print(f"    {cat} [{color}]: {count}")
    if unmapped:
        print(f"  未映射的高频原子类型 (Top 20):")
        for atom, count in unmapped.most_common(20):
            print(f"    {atom}: {count}")

    # ── 输出 ──
    output = {
        "factions": faction_data_list,
        "factionEdges": faction_edges,
        "relationCategories": {
            cat: {"color": info["color"], "count": cat_counts.get(cat, 0)}
            for cat, info in all_categories.items()
        },
        "meta": {
            "totalFactions": len(faction_data_list),
            "totalMembers": total_assigned,
            "totalRelations": len(relations),
            "totalChars": 1603,  # from chars/ count
            "coveragePercent": round(100 * total_assigned / 1603, 1),
            "generatedAt": datetime.now(timezone.utc).isoformat(),
        },
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    file_size_kb = os.path.getsize(OUTPUT_PATH) / 1024
    print(f"\n{'=' * 60}")
    print(f"输出: {OUTPUT_PATH}")
    print(f"文件大小: {file_size_kb:.1f} KB")
    print(f"势力数: {len(faction_data_list)}")
    print(f"人物覆盖: {total_assigned} / 1603 ({100*total_assigned/1603:.1f}%)")
    print(f"跨势力关系线: {len(faction_edges)}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
