import os
import json
import glob
import time
import httpx
from typing import List, Dict

# --- Configuration ---
CHAPTERS_DIR = "/Users/shushu/剑来/chapters"
RAW_DATA_DIR = "data/raw" # Per-chapter JSONs
# Dual API Endpoints configuration: (Base URL, Model Name)
API_CONFIGS = [
    ("http://127.0.0.1:7861/v1", "gemini-3-pro-preview"),             # Primary: Gemini CLI
    ("http://127.0.0.1:7861/antigravity/v1", "gemini-3-pro-low")     # Fallback: Antigravity IDE
]
API_PASSWORD = os.environ.get("JIANLAI_LLM_PASSWORD", "")

# --- System Prompt V2 ---
SYSTEM_PROMPT = """
你是一位精通小说分析的专家。请从《剑来》小说的文本片段中提取详细的“世界知识图谱”信息。

你需要提取以下几类信息，并以严格的 JSON 格式返回：

1. **人物 (Characters)**:
   - 提取所有登场或被提及的重要人物。
   - 字段: 
     - `name`: 标准人名。
     - `aliases`: 别名/绰号列表 (e.g. ["草鞋少年", "陈先生"])。
     - `bio`: 简短的人物介绍/状态描述。
     - `cultivation`: 当前修道境界 (e.g. "玉璞境", "二境武夫")，若文中未提则留空。
     - `faction`: 所属势力/宗门 (e.g. "落魄山", "正阳山")。
     - `tags`: 身份标签 (e.g. ["剑修", "纯粹武夫"])。

2. **关系 (Relations)**:
   - 人物之间的互动或关系。
   - 字段: `source` (主语), `target` (宾语), `relation` (关系类型), `evidence` (中文原文证据), `strength` (1-10)。

3. **物品/神兵 (Items)**:
   - 重要的法宝、飞剑、武器。
   - 字段: `name`, `type` (e.g. "飞剑", "仙兵"), `owner` (持有者), `description`, `rank` (品阶, 若有)。

4. **地理/地点 (Locations)**:
   - 出现的地点、山头、城池。
   - 字段: `name`, `type`, `description`, `parent` (所属大洲/天下/洞天)。

5. **势力 (Factions)**:
   - 宗门、组织、王朝。
   - 字段: `name`, `type`, `description`。

6. **文化/金句 (Quotes)**:
   - 极具哲理或代表性的句子。
   - 字段: `content` (内容), `speaker` (说话者), `context` (语境)。

7. **大事件 (Events)**:
   - 发生的关键剧情事件。
   - 字段: `name`, `type`, `participants` (参与者列表), `description`.

**输出格式要求**:
- 必须是合法的 JSON **对象** (Object)，包含上述 7 个 key。
- **请将最终的 JSON 结果包裹在 Markdown 代码块中**，格式如下：
```json
{{ ... }}
```
- 如果某类信息没有提取到，请返回空列表 `[]`。
- 所有内容使用**中文**。

**JSON 示例**:
{{
  "characters": [
    {{ "name": "陈平安", "aliases": ["泥瓶巷少年"], "cultivation": "长生桥断", "faction": "无" }}
  ],
  "relations": [
    {{ "source": "陈平安", "target": "宁姚", "relation": "爱慕", "strength": 9, "evidence": "..." }}
  ],
  "items": [],
  "locations": [],
  "factions": [],
  "quotes": [],
  "events": []
}}
"""

def call_local_gemini(text: str) -> Dict:
    """
    Calls the local Gemini API to extract V2 Schema data.
    Supports fallback from Gemini CLI endpoint to Antigravity endpoint.
    """
    
    # Safety settings to prevent blocking content (novel violence/weapons)
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
    ]

    payload = {
        "contents": [{
            "role": "user",
            "parts": [
                {"text": SYSTEM_PROMPT},
                {"text": f"小说文本:\n{text}"}
            ]
        }],
        "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json"},
        "safetySettings": safety_settings
    }
    
    import re

    # Try each endpoint in order
    for i, (base_url, model_name) in enumerate(API_CONFIGS):
        endpoint_name = "Gemini CLI" if "antigravity" not in base_url else "Antigravity IDE"
        print(f"  Calling API ({endpoint_name} - {model_name}): Size {len(text)}...")
        
        try:
            with httpx.Client(timeout=600.0) as client:
                resp = client.post(
                    f"{base_url}/models/{model_name}:generateContent",
                    json=payload,
                    headers={"x-goog-api-key": API_PASSWORD}
                )
            
            # If 429, continue to next endpoint (fallback)
            if resp.status_code == 429:
                print(f"  Rate Limit (429) on {endpoint_name}. Switching to fallback...")
                continue
                
            # If other error, log it but maybe don't fallback immediately unless it's a server error?
            # User instructions say fallback on quota issues. 429 is the main one.
            # But let's be robust: if 503 or 500, maybe fallback too?
            # For now, let's treat any non-200 as a reason to try the next one, 
            # OR just return None if it's the last one.
            if resp.status_code != 200:
                print(f"  API Error ({endpoint_name}): {resp.status_code} {resp.text}")
                continue

            # Success
            result = resp.json()
            candidates = result.get("candidates", [])
            if not candidates:
                # Debug: Print full response to diagnose empty candidates
                print(f"  No candidates returned from {endpoint_name}.")
                print(f"  [Debug] Full response keys: {result.keys()}")
                if "promptFeedback" in result:
                    print(f"  [Debug] promptFeedback: {result['promptFeedback']}")
                if "error" in result:
                    print(f"  [Debug] error: {result['error']}")
                # Dump to file for detailed inspection
                with open("debug_no_candidates.json", "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                print(f"  [Debug] Full response dumped to debug_no_candidates.json")
                continue
                
            # Handle multi-part responses (e.g. Thinking Models: part[0]=thought, part[1]=content)
            parts = candidates[0].get("content", {}).get("parts", [])
            content_text = "".join([p.get("text", "") for p in parts])
            
            # 1. Try to find Markdown JSON block first (Best for Thinking Models)
            match = re.search(r"```json\s*(\{.*?\})\s*```", content_text, re.DOTALL)
            if match:
                json_str = match.group(1)
                return json.loads(json_str)
            
            # 2. Fallback: Find raw JSON object between first { and last }
            start_idx = content_text.find('{')
            end_idx = content_text.rfind('}')
            
            if start_idx != -1 and end_idx != -1:
                json_str = content_text[start_idx : end_idx + 1]
                return json.loads(json_str)
            else:
                print(f"  Warning: No JSON object found in {endpoint_name} response.")
                # Dump full response to file for debugging
                debug_file = "debug_api_response.json"
                with open(debug_file, "w", encoding="utf-8") as f:
                    json.dump(candidates, f, ensure_ascii=False, indent=2)
                print(f"  [Use Debug] Full response dumped to {debug_file}")
                return None
            
        except Exception as e:
            print(f"  Exception with {endpoint_name}: {e}")
            # Try next endpoint
            
    print("  All API endpoints failed.")
    return None

def validate_data(data: Dict) -> bool:
    """
    Validates that the extracted data conforms to the expected V2 Schema.
    """
    required_keys = ["characters", "relations", "items", "locations", "factions", "quotes", "events"]
    if not isinstance(data, dict):
        return False
    
    for key in required_keys:
        if key not in data:
            print(f"  Validation Error: Missing key '{key}'")
            return False
        if not isinstance(data[key], list):
            print(f"  Validation Error: Key '{key}' is not a list")
            return False
            
    return True

def main():
    if not os.path.exists(RAW_DATA_DIR):
        os.makedirs(RAW_DATA_DIR)
        
    files = sorted(glob.glob(os.path.join(CHAPTERS_DIR, "*.txt")), key=lambda x: int(os.path.basename(x).split('_')[0]))
    print(f"Found {len(files)} chapters total.")
    
    processed_files = set()
    for json_file in glob.glob(os.path.join(RAW_DATA_DIR, "*.json")):
        basename = os.path.basename(json_file).replace('.json', '.txt')
        processed_files.add(basename)
        
    print(f"Found {len(processed_files)} processed chapters.")

    for i, file_path in enumerate(files):
        filename = os.path.basename(file_path)
        
        if filename in processed_files:
            continue
            
        print(f"[{i+1}/{len(files)}] Processing {filename}...")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
            
        # Retry loop
        max_retries = 3
        success = False
        
        for attempt in range(max_retries):
            if attempt > 0:
                print(f"  Retry attempt {attempt+1}/{max_retries}...")
                time.sleep(2) # Cooldown
            
            data = call_local_gemini(text)
            
            if data:
                if validate_data(data):
                    output_path = os.path.join(RAW_DATA_DIR, filename.replace('.txt', '.json'))
                    try:
                        with open(output_path, 'w', encoding='utf-8') as f:
                            json.dump(data, f, ensure_ascii=False, indent=2)
                        print(f"  Saved {output_path}")
                        success = True
                        break # Success, exit retry loop
                    except Exception as e:
                        print(f"  Error saving file: {e}")
                else:
                    print("  Schema validation failed.")
            else:
                print("  Extraction failed (API or JSON error).")
        
        if not success:
            print(f"  Skipping {filename} after {max_retries} failed attempts.")

if __name__ == "__main__":
    main()
