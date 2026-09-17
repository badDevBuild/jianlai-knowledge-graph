"""
使用 LLM 批量清洗人物的 Aliases 和 Factions
"""
import sys
import json
import os
import httpx
import time
import re

# --- 配置 ---
CHARACTERS_FILE = "data/build/characters.json"
CLEAN_DATA_FILE = "data/build/cleaned_metadata.json"

# API 配置 (优先使用 High 模型处理复杂逻辑)
API_CONFIGS = [
    ("http://127.0.0.1:7861/antigravity/v1", "gemini-3-pro-high"),
    ("http://127.0.0.1:7861/v1", "gemini-3-pro-preview")
]
API_PASSWORD = os.environ.get("JIANLAI_LLM_PASSWORD", "")


CLEAN_PROMPT_TEMPLATE = """
你是一位数据治理专家。请对以下小说人物的【别名列表 (Aliases)】、【势力列表 (Factions)】和【标签列表 (Tags)】进行深度清洗和标准化。

**处理原则**：

1.  **Aliases (别名) 清洗**：
    *   **移除通用词**：删除“年轻人”、“少年”、“男子”、“那个人”、“某人”、“客官”、“外乡人”、“好人”、“爹”、“师父”等毫无辨识度的泛指。
    *   **移除描述性短语**：删除过长的、显而易见是描述而非称呼的短语（如“一袭白衣的年轻人”、“被他娘亲一手调教出来的少年”）。
    *   **保留强特征**：保留有特定含义的绰号、官职、尊称（如“隐官”、“二店主”、“泥瓶巷少年”、“绣虎”、“老秀才”）。
    *   **去重与规范**：去除重复项，统一标点。

2.  **Factions (势力) 清洗**：
    *   **语义归一化**：将含义相同的不同表述合并。例如：
        *   “落魄山 (隐性)”、“落魄山（暂未正式建立）” -> **"落魄山"**
        *   “文圣一脉(非正式)” -> **"文圣一脉"**
    *   **拆分复合项**：将“剑气长城/隐官一脉”拆分为 **"剑气长城"** 和 **"隐官一脉"**。
    *   **移除无效项**：删除“无”、“无 (游历中)”、“未知”等无意义条目。

3.  **Tags (标签) 清洗**：
    *   **身份归一化**：将“二境武夫”、“二境武夫(曾)”、“二境武夫(伪装)”等统一为 **“武夫”** 或保留最高境界。将“剑修(伪)”、“剑修(隐含)”等统一为 **“剑修”**。
    *   **去除冗余**：删除“主角”、“好人”、“坚毅”、“勤奋”等性格描述或无意义标签，只保留身份、职业、特殊体质等关键属性（如“龙窑学徒”、“文圣弟子”、“隐官”、“止境武夫”）。
    *   **合并同义词**：如“读书人”、“儒生”、“书生”统一为 **“读书人”** 或 **“儒家弟子”**。

**输入格式**：
```json
{{
  "人物名": {{
    "aliases": ["别名1", ...],
    "factions": ["势力1", ...],
    "tags": ["标签1", ...]
  }}
}}
```

**输出格式**：
请返回清洗后的 JSON 对象，格式必须严格保持一致：
```json
{{
  "人物名": {{
    "aliases": ["清洗后的别名1", ...],
    "factions": ["清洗后的势力1", ...],
    "tags": ["清洗后的标签1", ...]
  }}
}}
```

**待处理数据**：
{data_chunk}
"""


def call_gemini_api(prompt):
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.1} # 低温度以保证严谨
    }
    
    for base_url, model_name in API_CONFIGS:
        print(f"  Calling {model_name}...")
        try:
            with httpx.Client(timeout=300.0) as client: # 增加超时时间
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
                print(f"  Error {resp.status_code}: {resp.text}")
                
        except Exception as e:
            print(f"  Exception: {e}")
            
    return None

def extract_json(text):
    """从返回文本中提取 JSON"""
    try:
        match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        
        # Fallback
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1:
            return json.loads(text[start:end+1])
    except Exception as e:
        print(f"  JSON Parse Error: {e}")
    return None

def clean_batch(batch_data):
    prompt = CLEAN_PROMPT_TEMPLATE.format(data_chunk=json.dumps(batch_data, ensure_ascii=False, indent=2))
    response = call_gemini_api(prompt)
    if response:
        return extract_json(response)
    return None

METADATA_RAW_FILE = "data/build/metadata_raw.json"
METADATA_CLEANED_FILE = "data/build/metadata_cleaned.json"

def load_characters():
    with open(CHARACTERS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_metadata_to_file():
    """Step 1: 提取需要清洗的数据到文件"""
    print("正在加载数据...")
    chars = load_characters()
    metadata = {}
    
    for name, char in chars.items():
        aliases = list(set(char.get("aliases", [])))
        factions = list(set(char.get("factions", [])))
        tags = list(set(char.get("tags", [])))
        
        # 无论数据多少都提取，确保全面清洗
        if aliases or factions or tags:
            metadata[name] = {
                "aliases": aliases,
                "factions": factions,
                "tags": tags
            }
            
    print(f"提取了 {len(metadata)} 个人物的数据")
    
    # 陈平安的数据量最大，打印出来看看
    if "陈平安" in metadata:
        print(f"陈平安: {len(metadata['陈平安']['aliases'])} 个别名, {len(metadata['陈平安']['factions'])} 个势力, {len(metadata['陈平安']['tags'])} 个标签")
        
    with open(METADATA_RAW_FILE, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    print(f"已保存到 {METADATA_RAW_FILE}")


def process_metadata_with_ai():
    """Step 2: 调用 AI 清洗数据"""
    print("正在加载待处理数据...")
    if not os.path.exists(METADATA_RAW_FILE):
        print(f"未找到 {METADATA_RAW_FILE}，请先运行 extract")
        return

    with open(METADATA_RAW_FILE, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
        
    cleaned_results = {}
    # 支持断点续传
    if os.path.exists(METADATA_CLEANED_FILE):
        with open(METADATA_CLEANED_FILE, 'r', encoding='utf-8') as f:
            cleaned_results = json.load(f)
        print(f"检测到已有进度，已完成 {len(cleaned_results)} 个人物")

    # 过滤已完成的
    to_process = {k: v for k, v in metadata.items() if k not in cleaned_results}
    print(f"剩余待处理: {len(to_process)} 个人物")
    
    # 1. 优先处理陈平安 (如果未完成)
    if "陈平安" in to_process:
        print(">>> 正在单独处理: 陈平安")
        res = clean_batch({"陈平安": to_process["陈平安"]})
        if res and "陈平安" in res:
            cleaned_results["陈平安"] = res["陈平安"]
            print(f"  陈平安清洗完成: Tags {len(to_process['陈平安']['tags'])} -> {len(res['陈平安']['tags'])}")
            # 立即保存
            with open(METADATA_CLEANED_FILE, 'w', encoding='utf-8') as f:
                json.dump(cleaned_results, f, ensure_ascii=False, indent=2)
            del to_process["陈平安"]
        else:
            print("  陈平安处理失败，跳过")
    
    # 2. 批量处理其他人
    BATCH_SIZE = 100 # 增加批大小，一次处理更多
    keys = list(to_process.keys())
    
    # 按数据量排序，优先处理复杂的
    keys.sort(key=lambda k: len(to_process[k]['aliases']) + len(to_process[k]['factions']) + len(to_process[k].get('tags', [])), reverse=True)
    
    for i in range(0, len(keys), BATCH_SIZE):
        batch_keys = keys[i:i+BATCH_SIZE]
        batch_data = {k: to_process[k] for k in batch_keys}
        
        print(f">>> 处理批次 {i//BATCH_SIZE + 1}/{(len(keys)+BATCH_SIZE-1)//BATCH_SIZE} ({len(batch_keys)} 人): {batch_keys[:3]}...")
        
        res = clean_batch(batch_data)
        
        if res:
            cleaned_results.update(res)
            print(f"  批次成功，总进度: {len(cleaned_results)}/{len(metadata)}")
            # 实时保存
            with open(METADATA_CLEANED_FILE, 'w', encoding='utf-8') as f:
                json.dump(cleaned_results, f, ensure_ascii=False, indent=2)
        else:
            print("  批次失败，跳过")
            
        time.sleep(1)

    print(f"\n清洗完成！结果已保存到 {METADATA_CLEANED_FILE}")


def replace_metadata_in_db():
    """Step 3: 将清洗后的数据替换回原文件"""
    print("正在替换数据...")
    if not os.path.exists(METADATA_CLEANED_FILE):
        print(f"未找到 {METADATA_CLEANED_FILE}，请先运行 process")
        return
        
    with open(METADATA_CLEANED_FILE, 'r', encoding='utf-8') as f:
        cleaned_data = json.load(f)
        
    with open(CHARACTERS_FILE, 'r', encoding='utf-8') as f:
        chars = json.load(f)
        
    count = 0
    total_aliases_removed = 0
    
    for name, data in cleaned_data.items():
        if name in chars:
            old_aliases_len = len(chars[name].get('aliases', []))
            new_aliases_len = len(data.get('aliases', []))
            
            chars[name]['aliases'] = data['aliases']
            chars[name]['factions'] = data['factions']
            chars[name]['tags'] = data.get('tags', [])
            
            diff = old_aliases_len - new_aliases_len
            if diff != 0:
                total_aliases_removed += diff
            count += 1
            
    print(f"已更新 {count} 个人物")
    print(f"共精简了 {total_aliases_removed} 个冗余别名")
    
    # 备份原文件
    if not os.path.exists(CHARACTERS_FILE + ".bak"):
        import shutil
        shutil.copy(CHARACTERS_FILE, CHARACTERS_FILE + ".bak")
        print(f"原文件已备份为 {CHARACTERS_FILE}.bak")
    
    with open(CHARACTERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(chars, f, ensure_ascii=False, indent=2)
    print(f"替换完成！")


def main():
    if len(sys.argv) < 2:
        print("使用方式:")
        print("  python clean_metadata.py extract   # 1. 提取数据")
        print("  python clean_metadata.py process   # 2. AI 清洗")
        print("  python clean_metadata.py replace   # 3. 替换生效")
        sys.exit(1)
        
    cmd = sys.argv[1]
    
    if cmd == "extract":
        extract_metadata_to_file()
    elif cmd == "process":
        process_metadata_with_ai()
    elif cmd == "replace":
        replace_metadata_in_db()
    else:
        print(f"未知命令: {cmd}")

if __name__ == "__main__":
    main()
