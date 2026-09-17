import json
import os
import time
import httpx

# === API Configuration ===
API_PASSWORD = os.environ.get("JIANLAI_LLM_PASSWORD", "")
BATCH_SIZE = 100 # Smaller batch for locations as hierarchy reasoning is complex

BATCH_CLEAN_PROMPT = """
你是一位《剑来》小说的地理考据专家。请根据以下地点列表的原始数据片段，批量整理并生成这些地点的**标准地理档案**。
重点在于构建**层级结构 (Hierarchy)**，解决"孤儿节点"问题。

**输入数据 (JSON List):**
{input_json}

**任务要求：**
对于列表中的每一个地点，请生成一个包含以下字段的对象：
1.  **canonical_name**: 地点的标准名称（修正错别字、去除无关修饰）。
2.  **type**: 地点类型 (选择其一: 天下, 大洲, 王朝, 城市, 宗门, 城镇, 村落, 山脉, 水域, 建筑, 遗迹, 店铺, 渡口, 地点)。
3.  **hierarchy**: **核心字段**。请尽力推断该地点的完整从属链路。
    *   格式: [天下, 大洲, 王朝/区域, 城市/宗门, 具体地点]
    *   示例 (泥瓶巷): ["浩然天下", "东宝瓶洲", "大骊王朝", "龙泉县", "泥瓶巷"]
    *   示例 (剑气长城): ["剑气长城/五彩天下"] (特殊独立区域)
    *   如果某一级不确定，可省略，但必须确保从大到小的顺序。
4.  **description**: 综合所有片段，写一段精炼的地理志描述。包含方位、特色、归属势力及相关重要人物。
5.  **aliases**: 提取所有别名。

**输出格式 (JSON Object):**
请返回一个 JSON 对象，**键必须与输入数据中的 "name" 字段完全一致**。
```json
{{
  "InputName": {{
    "canonical_name": "...",
    "type": "...",
    "hierarchy": ["...", "..."],
    "description": "...",
    "aliases": [...]
  }},
  ...
}}
```
"""

def call_gemini_api(prompt: str) -> str:
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"}
    }
    
    API_CONFIGS = [
        ("http://127.0.0.1:7861/v1", "gemini-3-pro-preview"),
        ("http://127.0.0.1:7861/antigravity/v1", "gemini-3-pro-high")
    ]
    
    for base_url, model_name in API_CONFIGS:
        try:
            print(f"  Attempting API: {base_url} ({model_name})...")
            with httpx.Client(timeout=300.0) as client:
                full_url = f"{base_url}/models/{model_name}:generateContent"
                resp = client.post(full_url, json=payload, headers={"x-goog-api-key": API_PASSWORD})
                
                if resp.status_code == 200:
                    try:
                        data = resp.json()
                        parts = data.get("candidates", [])[0].get("content", {}).get("parts", [])
                        if len(parts) > 0:
                            return parts[-1].get("text", "")
                    except:
                        pass
                else:
                    print(f"  Error {resp.status_code}")
        except Exception as e:
            print(f"  Connection Error: {e}")
            
    return None

def extract_json(text: str) -> dict:
    import re
    if not text: return None
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
    if json_match: text = json_match.group(1)
    brace_match = re.search(r'\{[\s\S]*\}', text)
    if brace_match:
        try: return json.loads(brace_match.group())
        except: pass
    return None

def run_step2():
    input_file = "data/build/locations_step1_aggregated.json"
    output_file = "data/build/locations_step2_ai_raw.json"
    
    print(f"Step 2: Loading {input_file}...")
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            merged_locations = json.load(f)
    except FileNotFoundError:
        print("Input file not found.")
        return

    ai_raw_results = {}
    if os.path.exists(output_file):
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                ai_raw_results = json.load(f)
            print(f"Resuming... Already processed {len(ai_raw_results)} items.")
        except:
            pass

    items_list = list(merged_locations.items())
    items_to_process = [x for x in items_list if x[0] not in ai_raw_results]
    total_items = len(items_to_process)
    
    print(f"Processing {total_items} locations in batches of {BATCH_SIZE}...")

    for i in range(0, total_items, BATCH_SIZE):
        batch = items_to_process[i : i + BATCH_SIZE]
        print(f"Processing Batch {i//BATCH_SIZE + 1} ({len(batch)} items)...")
        
        batch_input = []
        for name, fragment_list in batch:
            chunks = []
            for frag in fragment_list:
                desc = frag.get("description", "无描述")
                chunks.append(f"[{frag.get('original_name')}]: {desc}, ParentHint: {frag.get('parent','无')}")
            
            batch_input.append({
                "name": name,
                "context": chunks
            })
            
        prompt = BATCH_CLEAN_PROMPT.format(input_json=json.dumps(batch_input, ensure_ascii=False, indent=2))
        resp_text = call_gemini_api(prompt)
        
        if resp_text:
            batch_results = extract_json(resp_text)
            if batch_results:
                for k, v in batch_results.items():
                    ai_raw_results[k] = v
                
                # Save Checkpoint
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(ai_raw_results, f, indent=2, ensure_ascii=False)
            else:
                print("  JSON Parsing Failed")
        else:
             print("  API Failed")

    print(f"Done! Saved raw AI results to {output_file}")

if __name__ == "__main__":
    run_step2()
