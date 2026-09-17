import json
import os
import time
import httpx
from collections import defaultdict
from item_normalizer import normalize_item_name, normalize_item_type, is_valid_item

# === API Configuration (Reuse from other scripts) ===
API_PASSWORD = os.environ.get("JIANLAI_LLM_PASSWORD", "")
API_CONFIGS = [
    ("http://127.0.0.1:7861/antigravity/v1", "gemini-3-pro-high"),
    ("http://127.0.0.1:7861/v1", "gemini-3-pro-preview")
]

# === Prompt Template for Batch Processing ===
BATCH_CLEAN_PROMPT = """
你是一位《剑来》小说的设定专家。请根据以下物品列表的原始数据片段，批量整理并生成这些物品的最终标准档案。

**输入数据 (JSON List):**
{input_json}

**任务要求：**
对于列表中的每一个物品，请生成一个包含以下字段的对象：
1.  **description**: 综合所有片段，写一段精炼、准确的描述。包含物品外观、功能、来源及重要变迁。
2.  **grade**: 判断其最高品秩 (凡物, 灵器, 法宝, 半仙兵, 仙兵, 神器, 未知)。
3.  **status**: 判断物品最后状态 (活跃, 损毁, 遗失, 消耗)。
4.  **type**: 确认物品类型 (兵器, 法宝, 书籍, 货币, 灵物, 消耗品, 饰品, 其他)。
5.  **aliases**: 提取所有别名。

**输出格式 (JSON Object):**
请返回一个 JSON 对象，键为物品的标准名称，值为处理后的详细信息。
```json
{{
  "StandardItemName1": {{
    "description": "...",
    "grade": "...",
    "status": "...",
    "type": "...",
    "aliases": [...]
  }},
  "StandardItemName2": {{ ... }}
}}
```
"""

def call_gemini_api(prompt: str) -> str:
    """调用 Gemini API"""
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"}
    }
    
    for base_url, model_name in API_CONFIGS:
        try:
            with httpx.Client(timeout=180.0) as client: # Increased timeout for larger batch
                full_url = f"{base_url}/models/{model_name}:generateContent"
                
                resp = client.post(
                    full_url,
                    json=payload,
                    headers={"x-goog-api-key": API_PASSWORD}
                )
                if resp.status_code == 200:
                    return resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                else:
                    print(f"  API Error ({model_name}): {resp.status_code} - {resp.text[:100]}")
        except Exception as e:
            print(f"  Connection Error ({model_name}): {e}")
            
    return None

def process_items():
    print("Loading items.json...")
    with open("data/build/items.json", "r", encoding="utf-8") as f:
        raw_items = json.load(f)

    # 1. 归一化与聚合
    merged_items = defaultdict(list)
    print("Normalizing and aggregating items...")
    
    for name, data in raw_items.items():
        if not is_valid_item(name):
            continue
        norm_name = normalize_item_name(name)
        if not norm_name:
             continue
        data["original_name"] = name
        merged_items[norm_name].append(data)

    print(f"Reduced {len(raw_items)} raw items to {len(merged_items)} unique entities.")

    # 2. AI Batch Cleaning
    cleaned_data = {}
    BATCH_SIZE = 25 # Adjusted to 25 for safe token limits
    
    items_list = list(merged_items.items())
    
    # Resume logic
    if os.path.exists("data/build/items_cleaned_wip.json"):
        with open("data/build/items_cleaned_wip.json", "r", encoding="utf-8") as f:
            cleaned_data = json.load(f)
        print(f"Resuming... Already processed {len(cleaned_data)} items.")
    
    items_to_process = [x for x in items_list if x[0] not in cleaned_data]
    total_items = len(items_to_process)
    print(f"Processing {total_items} items in batches of {BATCH_SIZE}...")

    # Batch Process
    for i in range(0, total_items, BATCH_SIZE):
        batch = items_to_process[i : i + BATCH_SIZE]
        print(f"Processing Batch {i//BATCH_SIZE + 1} ({len(batch)} items)...")
        
        # Prepare Batch Input
        batch_input = []
        for name, fragment_list in batch:
            chunks = []
            for frag in fragment_list:
                desc = frag.get("description", "无描述")
                orig = frag.get("original_name")
                chunks.append(f"[{orig}]: {desc}")
            
            batch_input.append({
                "name": name,
                "descriptions": chunks,
                "original_types": list(set(f.get("type", "") for f in fragment_list))
            })
            
        # Call API
        prompt = BATCH_CLEAN_PROMPT.format(input_json=json.dumps(batch_input, ensure_ascii=False, indent=2))
        resp_json = call_gemini_api(prompt)
        
        if resp_json:
            try:
                ai_results = json.loads(resp_json)
                
                # Merge AI results back with local data (ownership logs)
                for name, fragment_list in batch:
                    ai_item = ai_results.get(name)
                    
                    # Prepare Aggregated Logs
                    all_logs = []
                    for frag in fragment_list:
                         if "ownership_log" in frag:
                            all_logs.extend(frag["ownership_log"])
                    
                    # Deduplicate Logs
                    unique_logs = {}
                    for log in all_logs:
                        key = f"{log.get('chapter', '')}_{log.get('owner', '')}"
                        if key not in unique_logs:
                            unique_logs[key] = log
                    
                    # Sort Logs (Regex based)
                    import re
                    def parse_chapter(log):
                        c = log.get('chapter', '')
                        m = re.search(r"第(\d+)章", c)
                        return int(m.group(1)) if m else 99999
                        
                    sorted_logs = sorted(list(unique_logs.values()), key=parse_chapter)

                    if ai_item:
                         cleaned_data[name] = {
                            "name": name,
                            "type": normalize_item_type(ai_item.get("type", "其他")),
                            "grade": ai_item.get("grade", "未知"),
                            "status": ai_item.get("status", "未知"),
                            "description": ai_item.get("description", ""),
                            "aliases": list(set(ai_item.get("aliases", []) + [f["original_name"] for f in fragment_list if f["original_name"] != name])),
                            "ownership_log": sorted_logs
                        }
                    else:
                        # Fallback if AI missed an item in batch
                        cleaned_data[name] = {
                            "name": name,
                            "type": normalize_item_type(fragment_list[0].get("type", "其他")),
                            "grade": "未知",
                            "status": "未知",
                            "description": fragment_list[0].get("description", ""),
                            "aliases": [f["original_name"] for f in fragment_list if f["original_name"] != name],
                            "ownership_log": sorted_logs
                        }
            except json.JSONDecodeError:
                print("  Batch JSON Parse Error! Falling back to raw data for this batch.")
                # Fallback whole batch
                for name, fragment_list in batch:
                     cleaned_data[name] = {
                        "name": name,
                        "type": normalize_item_type(fragment_list[0].get("type", "其他")),
                        "description": fragment_list[0].get("description", ""),
                        "ownership_log": [] # Simplified fallback
                     }
        else:
             print("  Batch API Failed!")
             # Fallback
             for name, fragment_list in batch:
                 cleaned_data[name] = {
                    "name": name,
                    "description": "AI Processing Failed",
                    "type": "未知",
                    "ownership_log": []
                 }

        # Save checkpoint
        with open("data/build/items_cleaned_wip.json", "w", encoding="utf-8") as f:
            json.dump(cleaned_data, f, indent=2, ensure_ascii=False)
            
    # Final
    with open("data/build/items_cleaned.json", "w", encoding="utf-8") as f:
        json.dump(cleaned_data, f, indent=2, ensure_ascii=False)
    print("Done!")

if __name__ == "__main__":
    process_items()
