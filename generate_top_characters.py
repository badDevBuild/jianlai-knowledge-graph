#!/usr/bin/env python3
"""
Generate characters_top.json for fast Home page loading.
Extracts top 20 characters by relation count from characters_lite.json.
"""

import json
from pathlib import Path

def generate_top_characters():
    # 路径配置
    base_dir = Path(__file__).parent
    input_file = base_dir / "data/dist/characters_lite.json"
    output_file = base_dir / "data/dist/characters_top.json"
    
    # 读取完整数据
    with open(input_file, 'r', encoding='utf-8') as f:
        characters = json.load(f)
    
    # 转换为列表并计算分数
    char_list = []
    for name, data in characters.items():
        # 使用与前端相同的排序逻辑
        relation_count = data.get('relationCount', len(data.get('relations', {})))
        quotes_count = len(data.get('quotes', []))
        aliases_count = len(data.get('aliases', []))
        score = relation_count * 10 + quotes_count + aliases_count
        char_list.append((name, data, score))
    
    # 按分数降序排序，取前 20
    char_list.sort(key=lambda x: x[2], reverse=True)
    top_chars = char_list[:20]
    
    # 构建输出数据 - 只保留首页展示所需的最小字段
    output_data = {}
    for name, data, _ in top_chars:
        output_data[name] = {
            "name": data.get("name", name),
            "avatar": data.get("avatar", ""),
            "aliases": data.get("aliases", [])[:3],  # 最多保留3个别名
            "factions": data.get("factions", [])[:2],  # 最多保留2个势力
            "relationCount": data.get("relationCount", 0),
            "quotes": data.get("quotes", [])[:1],  # 只保留1条语录用于预览
        }
    
    # 写入文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, separators=(',', ':'))
    
    # 输出统计
    input_size = input_file.stat().st_size / 1024
    output_size = output_file.stat().st_size / 1024
    print(f"生成完成!")
    print(f"  输入: {input_file.name} ({input_size:.1f} KB, {len(characters)} 人物)")
    print(f"  输出: {output_file.name} ({output_size:.1f} KB, {len(top_chars)} 人物)")
    print(f"  压缩比: {output_size/input_size*100:.1f}%")

if __name__ == "__main__":
    generate_top_characters()
