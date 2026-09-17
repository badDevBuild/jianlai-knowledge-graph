"""
势力描述重写脚本 (Faction Description Rewriter)

功能：调用 LLM 将合并后的冗余描述重写为精炼、流畅的单一描述

用法：
    python3 rewrite_faction_descriptions.py process  # 调用 LLM 处理
    python3 rewrite_faction_descriptions.py replace  # 应用重写结果
"""

import os
import sys
import json
import time
import httpx
import re

# === 配置 ===
FACTIONS_FILE = "data/build/factions.json"
REWRITTEN_FILE = "data/build/factions_rewritten.json"

# API 配置（与 clean_metadata.py 一致）
API_CONFIGS = [
    ("http://127.0.0.1:7861/antigravity/v1", "gemini-3-pro-high"),
    ("http://127.0.0.1:7861/v1", "gemini-3-pro-preview")
]
API_PASSWORD = os.environ.get("JIANLAI_LLM_PASSWORD", "")

# 每批处理的势力数量
BATCH_SIZE = 100

# === Prompt 模板 ===
REWRITE_PROMPT = """你是一位专业的《剑来》小说编辑。请根据以下多条关于同一势力的描述片段，重写为一段精炼、流畅、信息完整的势力介绍。

要求：
1. 合并重复信息，去除冗余
2. 保留所有独特的细节信息
3. 使用流畅的叙述性语言
4. 控制在 50-150 字之间
5. 不要添加原文没有的信息

**输入格式**：
```json
{{
  "势力名1": "描述片段1；描述片段2；...",
  "势力名2": "描述片段1；描述片段2；...",
  ...
}}
```

**输出格式**：
请返回清洗后的 JSON 对象，格式必须严格保持一致：
```json
{{
  "势力名1": "重写后的描述",
  "势力名2": "重写后的描述",
  ...
}}
```

**待处理数据**：
{data_chunk}
"""


def load_factions():
    """加载势力数据"""
    with open(FACTIONS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def call_gemini_api(prompt: str) -> str:
    """调用 Gemini API（与 clean_metadata.py 一致）"""
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.3}
    }
    
    for base_url, model_name in API_CONFIGS:
        print(f"  Calling {model_name}...")
        try:
            with httpx.Client(timeout=300.0) as client:
                resp = client.post(
                    f"{base_url}/models/{model_name}:generateContent",
                    json=payload,
                    headers={"x-goog-api-key": API_PASSWORD}
                )
            
            if resp.status_code == 200:
                result = resp.json()
                # Handle Thinking Models
                parts = result.get("candidates", [])[0].get("content", {}).get("parts", [])
                if len(parts) > 1:
                    return parts[-1].get("text", "")
                else:
                    return "".join([p.get("text", "") for p in parts])
            else:
                print(f"  Error {resp.status_code}: {resp.text[:200]}")
                
        except Exception as e:
            print(f"  Exception: {e}")
            
    return None


def extract_json(text: str) -> dict:
    """从 LLM 响应中提取 JSON"""
    # 尝试找到 JSON 代码块
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
    if json_match:
        text = json_match.group(1)
    
    # 尝试直接解析
    try:
        return json.loads(text)
    except:
        pass
    
    # 尝试找到 { } 包裹的内容
    brace_match = re.search(r'\{[\s\S]*\}', text)
    if brace_match:
        try:
            return json.loads(brace_match.group())
        except:
            pass
    
    return None


def process_factions():
    """处理势力描述"""
    factions = load_factions()
    
    # 筛选需要重写的势力（描述中包含分号，说明是合并的）
    to_process = {}
    for name, fac in factions.items():
        desc = fac.get("description", "")
        if "；" in desc:  # 合并过的描述
            to_process[name] = desc
    
    print(f"共 {len(factions)} 个势力，其中 {len(to_process)} 个需要重写")
    
    # 加载已有进度
    rewritten = {}
    if os.path.exists(REWRITTEN_FILE):
        with open(REWRITTEN_FILE, 'r', encoding='utf-8') as f:
            rewritten = json.load(f)
        print(f"检测到已有进度，已完成 {len(rewritten)} 个")
    
    # 过滤已完成的
    remaining = {k: v for k, v in to_process.items() if k not in rewritten}
    print(f"剩余待处理: {len(remaining)} 个")
    
    if not remaining:
        print("所有势力已处理完毕！")
        return
    
    # 分批处理
    names = list(remaining.keys())
    total_batches = (len(names) + BATCH_SIZE - 1) // BATCH_SIZE
    
    for i in range(0, len(names), BATCH_SIZE):
        batch_names = names[i:i+BATCH_SIZE]
        batch_data = {n: remaining[n] for n in batch_names}
        batch_num = i // BATCH_SIZE + 1
        
        print(f"\n>>> 处理批次 {batch_num}/{total_batches} ({len(batch_names)} 个): {batch_names[:3]}...")
        
        # 构建 prompt
        prompt = REWRITE_PROMPT.format(data_chunk=json.dumps(batch_data, ensure_ascii=False, indent=2))
        
        # 调用 API
        response = call_gemini_api(prompt)
        if not response:
            print("  API 调用失败，跳过此批次")
            continue
        
        # 解析结果
        result = extract_json(response)
        if not result:
            print("  JSON 解析失败，跳过此批次")
            continue
        
        # 保存结果
        for name, new_desc in result.items():
            if name in batch_data:
                rewritten[name] = new_desc
                print(f"  ✓ {name}: {new_desc[:50]}...")
        
        # 保存进度
        with open(REWRITTEN_FILE, 'w', encoding='utf-8') as f:
            json.dump(rewritten, f, ensure_ascii=False, indent=2)
        
        print(f"  批次完成，总进度: {len(rewritten)}/{len(to_process)}")
        
        # 短暂延迟
        time.sleep(1)
    
    print(f"\n处理完成！共重写 {len(rewritten)} 个势力描述")
    print(f"结果保存在: {REWRITTEN_FILE}")


def replace_descriptions():
    """将重写后的描述应用到 factions.json"""
    if not os.path.exists(REWRITTEN_FILE):
        print(f"错误: {REWRITTEN_FILE} 不存在，请先运行 process 命令")
        return
    
    # 加载数据
    with open(REWRITTEN_FILE, 'r', encoding='utf-8') as f:
        rewritten = json.load(f)
    
    factions = load_factions()
    
    # 替换描述
    replaced_count = 0
    for name, new_desc in rewritten.items():
        if name in factions:
            old_desc = factions[name].get("description", "")
            factions[name]["description"] = new_desc
            replaced_count += 1
            print(f"  替换: {name}")
            print(f"    旧: {old_desc[:60]}...")
            print(f"    新: {new_desc[:60]}...")
    
    # 保存
    with open(FACTIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(factions, f, ensure_ascii=False, indent=2)
    
    print(f"\n完成！共替换 {replaced_count} 个势力描述")
    print(f"结果保存在: {FACTIONS_FILE}")


def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  python3 rewrite_faction_descriptions.py process  # 调用 LLM 重写描述")
        print("  python3 rewrite_faction_descriptions.py replace  # 应用重写结果")
        return
    
    command = sys.argv[1]
    
    if command == "process":
        process_factions()
    elif command == "replace":
        replace_descriptions()
    else:
        print(f"未知命令: {command}")


if __name__ == "__main__":
    main()
