"""
人物简介 AI 总结脚本

功能：
1. 提取所有人物的合并简介到单独文件
2. 调用本地 Gemini API 对简介进行总结
3. 将总结后的内容替换回 characters.json

使用方式：
1. 先运行 extract: python summarize_bio.py extract
2. 检查 data/build/bio_raw.json 和提示词
3. 运行 summarize: python summarize_bio.py summarize
4. 检查 data/build/bio_summarized.json
5. 运行 replace: python summarize_bio.py replace
"""

import os
import sys
import json
import time
import httpx
from typing import Dict, Optional

# --- 配置 ---
CHARACTERS_FILE = "data/build/characters.json"
BIO_RAW_FILE = "data/build/bio_raw.json"
BIO_SUMMARIZED_FILE = "data/build/bio_summarized.json"

# API 配置（与 extract_pipeline.py 保持一致）
API_CONFIGS = [
    ("http://127.0.0.1:7861/v1", "gemini-3-pro-preview"),             # Primary: Gemini CLI
    ("http://127.0.0.1:7861/antigravity/v1", "gemini-3-pro-high")     # Fallback: Antigravity IDE
]
API_PASSWORD = os.environ.get("JIANLAI_LLM_PASSWORD", "")

# --- 提示词 ---
SUMMARIZE_PROMPT = """你是一位专业的文学分析师。请对以下《剑来》小说人物的多段描述进行总结，生成一段精炼、完整的人物简介。

**要求**：
1. 合并所有描述中的关键信息，去除重复内容
2. 按照人物发展顺序整理（如：出身背景 → 重要经历 → 最终成就）
3. 保留人物的核心身份、重要关系、标志性事件
4. 输出长度控制在 200-500 字之间
5. 使用流畅的叙述性语言，不要使用列表格式

**人物名**：{name}

**原始描述**：
{bio}

**请输出简洁的人物简介**："""

# --- 批量处理提示词 ---
BATCH_SUMMARIZE_PROMPT = """你是一位专业的文学分析师。请对以下《剑来》小说人物的描述进行总结。

**要求**：
1. 合并各人物所有描述中的关键信息，去除重复内容
2. 按照人物发展顺序整理（如：出身背景 → 重要经历 → 最终成就）
3. 保留人物的核心身份、重要关系、标志性事件
4. 每个人物的输出长度控制在 200-500 字之间
5. 使用流畅的叙述性语言

**输出格式**：
请返回一个 JSON 对象，格式如下：
```json
{{
  "人物名1": "总结后的简介...",
  "人物名2": "总结后的简介..."
}}
```

**人物列表**：
{characters}
"""


def extract_bio():
    """提取所有人物简介到单独文件"""
    print("正在提取人物简介...")
    
    with open(CHARACTERS_FILE, 'r', encoding='utf-8') as f:
        chars = json.load(f)
    
    bio_data = {}
    for name, char in chars.items():
        bio = char.get('bio_summary', '')
        if bio:
            bio_data[name] = {
                "bio_length": len(bio),
                "bio_text": bio
            }
    
    with open(BIO_RAW_FILE, 'w', encoding='utf-8') as f:
        json.dump(bio_data, f, ensure_ascii=False, indent=2)
    
    print(f"已提取 {len(bio_data)} 个人物的简介到 {BIO_RAW_FILE}")
    
    # 统计
    total_chars = sum(b['bio_length'] for b in bio_data.values())
    long_bios = [(name, b['bio_length']) for name, b in bio_data.items() if b['bio_length'] > 1000]
    long_bios.sort(key=lambda x: -x[1])
    
    print(f"总字符数: {total_chars:,}")
    print(f"超过1000字的人物: {len(long_bios)}")
    if long_bios[:10]:
        print("前10个最长简介:")
        for name, length in long_bios[:10]:
            print(f"  {name}: {length:,} 字")


def call_gemini_api(prompt: str) -> Optional[str]:
    """调用本地 Gemini API"""
    import re
    
    payload = {
        "contents": [{
            "role": "user",
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {"temperature": 0.3}
    }
    
    for base_url, model_name in API_CONFIGS:
        endpoint_name = "Gemini CLI" if "antigravity" not in base_url else "Antigravity IDE"
        print(f"  调用 {endpoint_name} ({model_name})...")
        
        try:
            with httpx.Client(timeout=300.0) as client:
                resp = client.post(
                    f"{base_url}/models/{model_name}:generateContent",
                    json=payload,
                    headers={"x-goog-api-key": API_PASSWORD}
                )
            
            if resp.status_code == 429:
                print(f"  限流 (429)，切换到备用端点...")
                continue
                
            if resp.status_code != 200:
                print(f"  API 错误: {resp.status_code}")
                continue
            
            result = resp.json()
            candidates = result.get("candidates", [])
            if not candidates:
                print(f"  无返回结果")
                continue
            
            parts = candidates[0].get("content", {}).get("parts", [])
            # Thinking Models: part[0]=thought, part[1]=content，取最后一个 part
            if len(parts) > 1:
                content_text = parts[-1].get("text", "")
            else:
                content_text = "".join([p.get("text", "") for p in parts])
            return content_text
            
        except Exception as e:
            print(f"  异常: {e}")
    
    return None


def extract_chinese_summary(text: str) -> str:
    """
    从 LLM 返回的文本中提取中文简介部分。
    LLM 可能返回英文思考过程，需要只保留最后的中文简介。
    """
    import re
    
    # 尝试匹配 **人物简介** 或 **XXX人物简介** 后面的内容
    patterns = [
        r'\*\*人物简介[：:]\s*(.+?)(?:\n\n\*\*|$)',  # **人物简介：xxx**
        r'\*\*[^*]+人物简介\*\*\s*\n(.+?)(?:\n\n\*\*|$)',  # **XXX人物简介**\n内容
        r'(?:^|\n\n)([^\n\*]+，[^\n]+。.+?)$',  # 最后一段以中文开头的内容
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            result = match.group(1).strip()
            # 确保结果包含足够的中文内容
            chinese_ratio = len(re.findall(r'[\u4e00-\u9fff]', result)) / max(len(result), 1)
            if chinese_ratio > 0.5:  # 至少50%是中文
                return result
    
    # 备用方案：找最后一个以中文字符开头的段落
    paragraphs = text.split('\n\n')
    for para in reversed(paragraphs):
        para = para.strip()
        if para and re.match(r'[\u4e00-\u9fff]', para):
            # 检查是否是有效的中文段落（不是标题）
            if len(para) > 50 and '，' in para:
                return para
    
    # 如果都失败，返回原文本（可能已经是纯中文）
    return text


def summarize_bio():
    """调用 AI 对简介进行总结（优化版：长简介单独处理，短简介批量处理）"""
    import re
    
    print("正在加载简介数据...")
    
    with open(BIO_RAW_FILE, 'r', encoding='utf-8') as f:
        bio_data = json.load(f)
    
    # 筛选需要总结的人物（简介超过 500 字的）
    to_summarize = {name: data for name, data in bio_data.items() if data['bio_length'] > 500}
    
    print(f"需要总结的人物数: {len(to_summarize)}")
    
    # 已处理的结果
    summarized = {}
    if os.path.exists(BIO_SUMMARIZED_FILE):
        with open(BIO_SUMMARIZED_FILE, 'r', encoding='utf-8') as f:
            summarized = json.load(f)
        print(f"已有 {len(summarized)} 个人物的总结")
    
    # 分类：长简介（>5000字）单独处理，短简介批量处理
    LONG_THRESHOLD = 5000
    long_bios = {name: data for name, data in to_summarize.items() 
                 if data['bio_length'] > LONG_THRESHOLD and name not in summarized}
    short_bios = {name: data for name, data in to_summarize.items() 
                  if data['bio_length'] <= LONG_THRESHOLD and name not in summarized}
    
    print(f"长简介（单独处理）: {len(long_bios)} 个")
    print(f"短简介（批量处理）: {len(short_bios)} 个")
    
    # 1. 单独处理长简介
    for i, (name, data) in enumerate(long_bios.items()):
        print(f"[长简介 {i+1}/{len(long_bios)}] 总结 {name} (原长: {data['bio_length']} 字)...")
        
        prompt = SUMMARIZE_PROMPT.format(
            name=name,
            bio=data['bio_text'][:30000]
        )
        
        result = call_gemini_api(prompt)
        
        if result:
            # 提取中文简介部分，过滤英文思考内容
            clean_summary = extract_chinese_summary(result)
            summarized[name] = clean_summary
            print(f"  完成，新长度: {len(clean_summary)} 字")
            
            with open(BIO_SUMMARIZED_FILE, 'w', encoding='utf-8') as f:
                json.dump(summarized, f, ensure_ascii=False, indent=2)
        else:
            print(f"  失败，跳过")
        
        time.sleep(0.5)
    
    # 2. 批量处理短简介（每批 10 个）
    BATCH_SIZE = 10
    short_list = list(short_bios.items())
    
    for batch_idx in range(0, len(short_list), BATCH_SIZE):
        batch = short_list[batch_idx:batch_idx + BATCH_SIZE]
        batch_names = [name for name, _ in batch]
        
        print(f"[批量 {batch_idx//BATCH_SIZE + 1}/{(len(short_list) + BATCH_SIZE - 1)//BATCH_SIZE}] 处理 {len(batch)} 个人物: {', '.join(batch_names[:3])}...")
        
        # 构建批量提示词
        characters_text = ""
        for name, data in batch:
            characters_text += f"\n### {name}\n{data['bio_text'][:3000]}\n"
        
        prompt = BATCH_SUMMARIZE_PROMPT.format(characters=characters_text)
        
        result = call_gemini_api(prompt)
        
        if result:
            # 尝试解析 JSON
            try:
                # 提取 JSON 块
                json_match = re.search(r'```json\s*(\{.*?\})\s*```', result, re.DOTALL)
                if json_match:
                    batch_result = json.loads(json_match.group(1))
                else:
                    # 尝试直接解析
                    start_idx = result.find('{')
                    end_idx = result.rfind('}')
                    if start_idx != -1 and end_idx != -1:
                        batch_result = json.loads(result[start_idx:end_idx+1])
                    else:
                        print(f"  无法解析 JSON，跳过此批次")
                        continue
                
                for name, summary in batch_result.items():
                    # 批量结果也可能包含思考内容，需要过滤
                    clean_summary = extract_chinese_summary(summary.strip())
                    summarized[name] = clean_summary
                    print(f"  {name}: {len(clean_summary)} 字")
                
                with open(BIO_SUMMARIZED_FILE, 'w', encoding='utf-8') as f:
                    json.dump(summarized, f, ensure_ascii=False, indent=2)
                    
            except json.JSONDecodeError as e:
                print(f"  JSON 解析失败: {e}")
        else:
            print(f"  API 调用失败，跳过此批次")
        
        time.sleep(0.5)
    
    print(f"\n总结完成！共 {len(summarized)} 个人物")
    print(f"结果保存在: {BIO_SUMMARIZED_FILE}")


def replace_bio():
    """将总结后的简介替换回 characters.json"""
    print("正在加载数据...")
    
    with open(CHARACTERS_FILE, 'r', encoding='utf-8') as f:
        chars = json.load(f)
    
    with open(BIO_SUMMARIZED_FILE, 'r', encoding='utf-8') as f:
        summarized = json.load(f)
    
    replaced_count = 0
    for name, new_bio in summarized.items():
        if name in chars:
            old_len = len(chars[name].get('bio_summary', ''))
            chars[name]['bio_summary'] = new_bio
            new_len = len(new_bio)
            replaced_count += 1
            print(f"  {name}: {old_len} → {new_len} 字")
    
    with open(CHARACTERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(chars, f, ensure_ascii=False, indent=2)
    
    print(f"\n替换完成！共替换 {replaced_count} 个人物的简介")


def show_prompt():
    """显示提示词供用户检查"""
    print("=" * 60)
    print("单个人物总结提示词")
    print("=" * 60)
    print(SUMMARIZE_PROMPT)
    print("\n" + "=" * 60)
    print("批量总结提示词（暂未使用）")
    print("=" * 60)
    print(BATCH_SUMMARIZE_PROMPT)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方式:")
        print("  python summarize_bio.py extract    # 提取简介到单独文件")
        print("  python summarize_bio.py prompt     # 显示提示词")
        print("  python summarize_bio.py summarize  # 调用 AI 总结")
        print("  python summarize_bio.py replace    # 替换回 characters.json")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "extract":
        extract_bio()
    elif cmd == "prompt":
        show_prompt()
    elif cmd == "summarize":
        summarize_bio()
    elif cmd == "replace":
        replace_bio()
    else:
        print(f"未知命令: {cmd}")
        sys.exit(1)
