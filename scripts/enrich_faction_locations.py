#!/usr/bin/env python3
"""
通过 NotebookLM 批量查询势力所在地点，丰富 factions 数据。

用法:
    JIANLAI_NOTEBOOK_ID=<notebook-id> python scripts/enrich_faction_locations.py
"""

import json
import subprocess
import time
import sys
import os

# 配置
BATCH_SIZE = 15  # 每批查询的势力数量
MAX_RETRIES = 3  # 每批最大重试次数
RETRY_DELAY = 5  # 重试间隔秒数
OUTPUT_FILE = "data/build/faction_locations.json"
FACTIONS_FILE = "data/build/factions.json"
NOTEBOOK_ID = os.environ.get("JIANLAI_NOTEBOOK_ID", "")

# 提示词模板
PROMPT_TEMPLATE = """你是《剑来》小说的知识专家。请根据小说原文内容，回答以下势力的所在地点信息。

## 要求
1. 只回答你确定的信息，不确定的填 "未知"
2. location: 势力的山门/总部/驻地的具体名称
3. region: 所属的大区域，格式为 "X天下 > X洲 > X国/王朝"，层级用 " > " 分隔
4. 严格按照下方 JSON 数组格式返回，不要有任何多余的解释文字

## 返回格式示例
```json
[
  {{"faction": "落魄山", "location": "落魄山（处州龙泉县）", "region": "浩然天下 > 东宝瓶洲 > 大骊王朝"}},
  {{"faction": "正阳山", "location": "一线峰", "region": "浩然天下 > 东宝瓶洲 > 大骊王朝"}},
  {{"faction": "某个不确定的势力", "location": "未知", "region": "未知"}}
]
```

## 需要查询的势力列表
{faction_list}

请直接返回 JSON 数组，不要有其他文字。"""


def ask_notebooklm(question: str, retry=0) -> str:
    """调用 NotebookLM 提问，返回回答文本。"""
    try:
        result = subprocess.run(
            ["notebooklm", "ask", question, "--notebook", NOTEBOOK_ID, "--new"],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode != 0:
            print(f"  [ERROR] notebooklm 返回错误: {result.stderr.strip()}")
            if retry < MAX_RETRIES:
                print(f"  [RETRY] 第 {retry+1} 次重试，等待 {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY)
                return ask_notebooklm(question, retry + 1)
            return ""
        return result.stdout
    except subprocess.TimeoutExpired:
        print(f"  [TIMEOUT] 查询超时")
        if retry < MAX_RETRIES:
            print(f"  [RETRY] 第 {retry+1} 次重试...")
            time.sleep(RETRY_DELAY)
            return ask_notebooklm(question, retry + 1)
        return ""


def parse_json_from_response(text: str) -> list:
    """从 NotebookLM 回答中提取 JSON 数组。"""
    # 去掉 "Answer:" 前缀等
    text = text.strip()
    if "Answer:" in text:
        text = text.split("Answer:", 1)[1].strip()

    # 尝试找到 JSON 数组
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1:
        print(f"  [WARN] 未找到 JSON 数组")
        return []

    json_str = text[start:end + 1]

    # 清理常见问题
    import re
    # 1. 移除字符串值内的控制字符（保留 \n \t 等转义）
    json_str = re.sub(r'[\x00-\x1f\x7f]', ' ', json_str)
    # 2. 尾部多余逗号
    json_str = json_str.replace(",]", "]").replace(",}", "}")
    # 3. 多余空格压缩
    json_str = re.sub(r'  +', ' ', json_str)

    try:
        data = json.loads(json_str)
        if isinstance(data, list):
            return data
        return []
    except json.JSONDecodeError as e:
        print(f"  [WARN] JSON 解析失败: {e}")
        # 最后尝试: 用 strict=False 模式
        try:
            import ast
            data = ast.literal_eval(json_str)
            if isinstance(data, list):
                return data
        except:
            pass
        return []


def main():
    if not NOTEBOOK_ID:
        print("[ERROR] 请先设置 JIANLAI_NOTEBOOK_ID 环境变量", file=sys.stderr)
        sys.exit(2)

    # 加载势力数据
    with open(FACTIONS_FILE, "r") as f:
        factions = json.load(f)

    faction_names = sorted(factions.keys())
    print(f"共 {len(faction_names)} 个势力需要查询位置信息")

    # 加载已有结果（支持断点续传）
    results = {}
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r") as f:
            results = json.load(f)
        print(f"已有 {len(results)} 个势力的位置数据，将跳过")

    # 过滤掉已有结果的势力
    remaining = [n for n in faction_names if n not in results]
    print(f"还需查询 {len(remaining)} 个势力")

    if not remaining:
        print("全部查询完成！")
        return

    # 分批查询
    total_batches = (len(remaining) + BATCH_SIZE - 1) // BATCH_SIZE
    for batch_idx in range(total_batches):
        start = batch_idx * BATCH_SIZE
        end = min(start + BATCH_SIZE, len(remaining))
        batch = remaining[start:end]

        print(f"\n=== 批次 {batch_idx + 1}/{total_batches} ({len(batch)} 个势力) ===")
        for n in batch:
            print(f"  - {n}")

        # 构建势力列表文本
        faction_list = "\n".join(f"{i+1}. {name}" for i, name in enumerate(batch))
        prompt = PROMPT_TEMPLATE.format(faction_list=faction_list)

        # 查询
        print(f"  正在查询 NotebookLM...")
        response = ask_notebooklm(prompt)

        if not response:
            print(f"  [FAIL] 批次 {batch_idx + 1} 查询失败，跳过")
            continue

        # 解析结果
        items = parse_json_from_response(response)
        if not items:
            print(f"  [FAIL] 批次 {batch_idx + 1} 解析失败，尝试重新查询...")
            time.sleep(RETRY_DELAY)
            response = ask_notebooklm(prompt)
            items = parse_json_from_response(response)

        if items:
            print(f"  [OK] 成功解析 {len(items)} 条结果")
            for item in items:
                name = item.get("faction", "")
                if name and name in factions:
                    results[name] = {
                        "location": item.get("location", "未知"),
                        "region": item.get("region", "未知")
                    }
                    print(f"    {name} -> {item.get('location', '?')} ({item.get('region', '?')})")
                elif name:
                    # 名称可能有细微差异，尝试模糊匹配
                    for fn in batch:
                        if name in fn or fn in name:
                            results[fn] = {
                                "location": item.get("location", "未知"),
                                "region": item.get("region", "未知")
                            }
                            print(f"    {fn} (模糊匹配 '{name}') -> {item.get('location', '?')}")
                            break
        else:
            print(f"  [FAIL] 批次 {batch_idx + 1} 两次查询均失败")

        # 每批保存一次（断点续传）
        with open(OUTPUT_FILE, "w") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"  已保存，累计 {len(results)}/{len(faction_names)} 个势力")

        # 批次间间隔，避免频率限制
        if batch_idx < total_batches - 1:
            time.sleep(3)

    print(f"\n===== 全部完成 =====")
    print(f"成功: {len(results)}/{len(faction_names)} 个势力")
    print(f"结果保存在: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
