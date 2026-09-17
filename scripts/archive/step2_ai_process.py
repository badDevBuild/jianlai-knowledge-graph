import json
import os
import time
import httpx
from item_normalizer import normalize_item_type

# === API Configuration ===
API_PASSWORD = os.environ.get("JIANLAI_LLM_PASSWORD", "")
API_CONFIGS = [
    ("http://127.0.0.1:7861/v1", "gemini-3-pro-preview"),
    ("http://127.0.0.1:7861/antigravity/v1", "gemini-3-pro-high")
]

BATCH_SIZE = 300 

BATCH_CLEAN_PROMPT = """
你是一位《剑来》小说的设定专家。请根据以下物品列表的原始数据片段，批量整理并生成这些物品的最终标准档案。

**输入数据 (JSON List):**
{input_json}

**任务要求：**
对于列表中的每一个物品，请生成一个包含以下字段的对象：
1.  **standard_name**: 物品的最终标准名称（修正错别字、去除修饰语）。
2.  **description**: 综合所有片段，写一段精炼、准确的描述。包含物品外观、功能、来源及重要变迁。
3.  **grade**: 判断其最高品秩 (凡物, 灵器, 法宝, 半仙兵, 仙兵, 神器, 未知)。
4.  **status**: 判断物品最后状态 (活跃, 损毁, 遗失, 消耗)。
5.  **type**: 确认物品类型 (兵器, 法宝, 书籍, 货币, 灵物, 消耗品, 饰品, 其他)。
6.  **aliases**: 提取所有别名。

**输出格式 (JSON Object):**
请返回一个 JSON 对象，**键必须与输入数据中的 "name" 字段完全一致 (即使它是错的)**，值为处理后的详细信息。
```json
{{
  "InputOriginalName": {{
    "standard_name": "StandardName",
    "description": "...",
    "grade": "...",
    "status": "...",
    "type": "...",
    "aliases": [...]
  }},
  "InputOriginalName2": {{ ... }}
}}
```
"""

def call_gemini_api(prompt: str) -> str:
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"}
    }
    
    # Priority order from working script (Testing Preview First for Speed)
    PROPER_API_CONFIGS = [
        ("http://127.0.0.1:7861/v1", "gemini-3-pro-preview"),
        ("http://127.0.0.1:7861/antigravity/v1", "gemini-3-pro-high")
    ]
    
    for base_url, model_name in PROPER_API_CONFIGS:
        try:
            print(f"  Attempting API: {base_url} ({model_name})...")
            with httpx.Client(timeout=300.0) as client:
                full_url = f"{base_url}/models/{model_name}:generateContent"
                
                resp = client.post(
                    full_url,
                    json=payload,
                    headers={"x-goog-api-key": API_PASSWORD}
                )
                print(f"  Response Status: {resp.status_code}")
                if resp.status_code == 200:
                    try:
                        data = resp.json()
                        # Robust parsing for Thinking Models (parts array)
                        parts = data.get("candidates", [])[0].get("content", {}).get("parts", [])
                        if len(parts) > 1:
                            return parts[-1].get("text", "")
                        elif len(parts) == 1:
                            return parts[0].get("text", "")
                        else:
                            print(f"  API Empty Content: {json.dumps(data)}")
                            return None
                    except Exception as e:
                         print(f"  JSON Decode Error: {e}")
                else:
                    print(f"  API Error ({model_name}): {resp.status_code} - {resp.text[:200]}")
        except Exception as e:
            print(f"  Connection Error ({model_name}): {e}")
            
    return None

def extract_json(text: str) -> dict:
    """从 LLM 响应中提取 JSON"""
    import re
    # 尝试找到 JSON 代码块
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
    if json_match:
        text = json_match.group(1)
    
    # 尝试直接解析
    try:
        return json.loads(text)
    except:
        pass
    
    # 尝试找到 { } 包裹的内容 (Fallback)
    brace_match = re.search(r'\{[\s\S]*\}', text)
    if brace_match:
        try:
            return json.loads(brace_match.group())
        except:
            pass
    return None

def run_step2():
    input_file = "data/build/items_step1_aggregated.json"
    output_file = "data/build/items_step2_ai_raw.json"
    
    print(f"Step 2: Loading {input_file}...")
    with open(input_file, "r", encoding="utf-8") as f:
        merged_items = json.load(f)

    # Load existing progress
    ai_raw_results = {}
    if os.path.exists(output_file):
        try:
            with open(output_file, "r", encoding="utf-8") as f:
               ai_raw_results = json.load(f)
            print(f"Resuming... Already processed {len(ai_raw_results)} batches/items.") # Note: structure might vary, let's assume flat dict for now
        except:
             print("Warning: Could not read existing output file. Starting fresh.")

    items_list = list(merged_items.items())
    # Filter items that are already in ai_raw_results (keys are item names)
    # Wait, ai_raw_results will likely contain the merged results from batches.
    
    items_to_process = [x for x in items_list if x[0] not in ai_raw_results]
    total_items = len(items_to_process)
    
    print(f"Processing {total_items} items in batches of {BATCH_SIZE}...")

    for i in range(0, total_items, BATCH_SIZE):
        batch = items_to_process[i : i + BATCH_SIZE]
        print(f"Processing Batch {i//BATCH_SIZE + 1} ({len(batch)} items)...")
        
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
            
        prompt = BATCH_CLEAN_PROMPT.format(input_json=json.dumps(batch_input, ensure_ascii=False, indent=2))
        resp_text = call_gemini_api(prompt)
        
        if resp_text:
            # Parse with robust extractor
            batch_results = extract_json(resp_text)
            
            if batch_results:
                # Store results
                for k, v in batch_results.items():
                    ai_raw_results[k] = v
            else:
               print(f"  JSON Parsing Failed in Batch {i//BATCH_SIZE + 1}! Saving raw text.")
               with open(f"data/build/debug_batch_{i//BATCH_SIZE + 1}.txt", "w", encoding="utf-8") as log:
                    log.write(resp_text)
        else:
            print("  API Failed.")

        # Save Checkpoint
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(ai_raw_results, f, indent=2, ensure_ascii=False)

    print(f"Done! Saved raw AI results to {output_file}")

if __name__ == "__main__":
    run_step2()
