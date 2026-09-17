#!/usr/bin/env python3
"""
《剑来》知识图谱提取脚本 V2.0

使用 extraction_prompt_v2.md 的新 Schema 进行章节内容提取。
提取结果保存到 data/v2/ 目录，与旧版本 data/raw/ 区分。

特性：
- 动态上下文注入：维护跨章节状态（人物缓存、未解悬疑等）
- 断点续传
- Schema 验证
"""

import os
import json
import glob
import time
import re
import argparse
import httpx
from typing import Dict, Optional, List
from pathlib import Path
from dataclasses import dataclass, field, asdict
from collections import deque

# --- Configuration ---
BASE_DIR = Path(__file__).parent
CHAPTERS_DIR = BASE_DIR / "chapters"
OUTPUT_DIR = BASE_DIR / "data" / "v2"
PROMPT_FILE = BASE_DIR / "docs" / "extraction_prompt_v2.md"
STATE_FILE = BASE_DIR / "data" / "v2" / "extraction_state.json"

# Dual API Endpoints configuration: (Base URL, Model Name)
API_CONFIGS = [
    ("http://127.0.0.1:7861/v1", "gemini-3-pro-preview"),             # Primary: Gemini CLI
    ("http://127.0.0.1:7861/antigravity/v1", "gemini-3-pro-low")     # Fallback: Antigravity IDE
]
API_PASSWORD = os.environ.get("JIANLAI_LLM_PASSWORD", "")

# V2 Schema 的顶级字段
REQUIRED_KEYS = [
    "meta", "characters", "relations", "events", "economics", 
    "plot_links", "items", "locations", "factions", "quotes"
]

# 近期人物缓存的最大数量
MAX_RECENT_CHARACTERS = 20
# 在场人物缓存的最大数量
MAX_ON_SCENE_CHARACTERS = 10


@dataclass
class ExtractionState:
    """
    提取状态管理类
    
    维护跨章节的动态上下文，包括：
    - 时间锚点和主线剧情
    - 活跃事件
    - 在场人物和近期人物
    - 未解决的伏笔
    """
    # 当前时间锚点
    chapter_time: str = "故事开始"
    # 主线剧情
    main_plot: str = "陈平安在小镇生活"
    # 活跃事件列表
    active_events: List[str] = field(default_factory=list)
    # 当前场景在场人物
    characters_on_scene: List[str] = field(default_factory=list)
    # 近期出现的重要人物
    recent_characters: List[str] = field(default_factory=list)
    # 未解决的伏笔缓冲区
    unidentified_buffer: List[Dict] = field(default_factory=list)
    # 最后处理的章节ID
    last_chapter_id: int = 0
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ExtractionState':
        """从字典创建"""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
    
    def save(self, path: Path):
        """保存状态到文件"""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
    
    @classmethod
    def load(cls, path: Path) -> 'ExtractionState':
        """从文件加载状态"""
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return cls.from_dict(json.load(f))
        return cls()
    
    def update_from_extraction(self, data: Dict, chapter_id: int):
        """
        根据提取结果更新状态
        
        Args:
            data: 提取的 JSON 数据
            chapter_id: 当前章节ID
        """
        self.last_chapter_id = chapter_id
        
        # 1. 更新人物列表
        if "characters" in data:
            new_characters = []
            for char in data["characters"]:
                name = char.get("name", "")
                if name and char.get("is_identified", True):
                    new_characters.append(name)
            
            # 更新在场人物（取最后出现的人物）
            self.characters_on_scene = new_characters[:MAX_ON_SCENE_CHARACTERS]
            
            # 更新近期人物（合并并去重）
            all_recent = new_characters + self.recent_characters
            seen = set()
            unique_recent = []
            for name in all_recent:
                if name not in seen:
                    seen.add(name)
                    unique_recent.append(name)
            self.recent_characters = unique_recent[:MAX_RECENT_CHARACTERS]
        
        # 2. 更新活跃事件
        if "events" in data:
            for event in data["events"]:
                event_name = event.get("name", "")
                status = event.get("status", "")
                scope = event.get("scope", "")
                
                # 只关注宏观和中观事件
                if scope in ["宏观", "中观"] and event_name:
                    if status in ["新发生", "进行中", "关键转折"]:
                        if event_name not in self.active_events:
                            self.active_events.append(event_name)
                    elif status == "已结束":
                        if event_name in self.active_events:
                            self.active_events.remove(event_name)
            
            # 限制活跃事件数量
            self.active_events = self.active_events[-10:]
        
        # 3. 更新伏笔缓冲区
        if "plot_links" in data:
            for link in data["plot_links"]:
                link_type = link.get("type", "")
                status = link.get("status", "")
                
                if link_type == "伏笔" and status == "未解决":
                    # 添加新的未解决伏笔
                    self.unidentified_buffer.append({
                        "chapter": chapter_id,
                        "content": link.get("content", ""),
                        "entity": link.get("related_entity", ""),
                        "clues": link.get("clues", []),
                        "inference": link.get("inference", "")
                    })
                elif link_type in ["身份揭秘", "回调"]:
                    # 移除已解决的伏笔
                    entity = link.get("related_entity", "")
                    if entity:
                        self.unidentified_buffer = [
                            b for b in self.unidentified_buffer 
                            if b.get("entity") != entity
                        ]
            
            # 限制伏笔缓冲区大小
            self.unidentified_buffer = self.unidentified_buffer[-30:]
        
        # 4. 更新时间锚点（从事件推断）
        if "events" in data:
            for event in data["events"]:
                if event.get("scope") in ["宏观", "中观"]:
                    self.chapter_time = event.get("name", self.chapter_time)
                    break
    
    def format_context(self) -> str:
        """
        格式化动态上下文为注入字符串
        """
        # 格式化在场人物
        on_scene = ", ".join(self.characters_on_scene) if self.characters_on_scene else "无"
        
        # 格式化近期人物
        recent = ", ".join(self.recent_characters) if self.recent_characters else "无"
        
        # 格式化活跃事件
        events = ", ".join(self.active_events) if self.active_events else "无"
        
        # 格式化未解悬疑
        if self.unidentified_buffer:
            buffer_lines = []
            for i, item in enumerate(self.unidentified_buffer[-5:], 1):  # 只显示最近5条
                clues = "、".join(item.get("clues", [])[:3])
                line = f"{i}. 第{item.get('chapter')}章：{item.get('content', '')} [线索：{clues}]"
                if item.get("inference"):
                    line += f" → 推测：{item.get('inference')}"
                buffer_lines.append(line)
            buffer = "\n".join(buffer_lines)
        else:
            buffer = "无"
        
        return f"""【当前状态】
- 时间锚点：{self.chapter_time}
- 主线剧情：{self.main_plot}
- 活跃事件：{events}

【人物缓存】
- 在场人物：{on_scene}
- 近期人物：{recent}

【未解悬疑】
{buffer}"""


def load_prompt() -> str:
    """加载提取提示词模板"""
    with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
        return f.read()


def inject_context(prompt_template: str, state: ExtractionState) -> str:
    """
    将动态上下文注入到提示词模板中
    
    替换占位符：
    - {{CHAPTER_TIME}}
    - {{MAIN_PLOT}}  
    - {{ACTIVE_EVENTS}}
    - {{CHARACTERS_ON_SCENE}}
    - {{RECENT_CHARACTERS}}
    - {{UNIDENTIFIED_BUFFER}}
    """
    # 格式化各个占位符的值
    on_scene = ", ".join(state.characters_on_scene) if state.characters_on_scene else "无"
    recent = ", ".join(state.recent_characters) if state.recent_characters else "无"
    events = ", ".join(state.active_events) if state.active_events else "无"
    
    # 格式化伏笔缓冲区
    if state.unidentified_buffer:
        buffer_lines = []
        for item in state.unidentified_buffer[-5:]:
            clues = "、".join(item.get("clues", [])[:3])
            line = f"- 第{item.get('chapter')}章：{item.get('content', '')} [线索：{clues}]"
            if item.get("inference"):
                line += f" → 推测：{item.get('inference')}"
            buffer_lines.append(line)
        buffer = "\n".join(buffer_lines)
    else:
        buffer = "无"
    
    # 替换占位符
    prompt = prompt_template
    prompt = prompt.replace("{{CHAPTER_TIME}}", state.chapter_time)
    prompt = prompt.replace("{{MAIN_PLOT}}", state.main_plot)
    prompt = prompt.replace("{{ACTIVE_EVENTS}}", events)
    prompt = prompt.replace("{{CHARACTERS_ON_SCENE}}", on_scene)
    prompt = prompt.replace("{{RECENT_CHARACTERS}}", recent)
    prompt = prompt.replace("{{UNIDENTIFIED_BUFFER}}", buffer)
    
    return prompt


def call_llm_api(text: str, system_prompt: str) -> Optional[Dict]:
    """
    调用 LLM API 进行知识图谱提取。
    支持从 Gemini CLI 到 Antigravity 的降级。
    """
    
    # 安全设置，防止小说中的暴力/武器内容被拦截
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
                {"text": system_prompt},
                {"text": f"【章节文本】\n{text}"}
            ]
        }],
        "generationConfig": {
            "temperature": 0.1,
            "responseMimeType": "application/json"
        },
        "safetySettings": safety_settings
    }

    # 依次尝试每个端点
    for base_url, model_name in API_CONFIGS:
        endpoint_name = "Gemini CLI" if "antigravity" not in base_url else "Antigravity IDE"
        print(f"  调用 API ({endpoint_name} - {model_name}): 文本长度 {len(text)}...")
        
        try:
            with httpx.Client(timeout=600.0) as client:
                resp = client.post(
                    f"{base_url}/models/{model_name}:generateContent",
                    json=payload,
                    headers={"x-goog-api-key": API_PASSWORD}
                )
            
            # 429 限流，切换到备用端点
            if resp.status_code == 429:
                print(f"  限流 (429) on {endpoint_name}. 切换备用端点...")
                continue
                
            if resp.status_code != 200:
                print(f"  API 错误 ({endpoint_name}): {resp.status_code} {resp.text}")
                continue

            result = resp.json()
            candidates = result.get("candidates", [])
            
            if not candidates:
                print(f"  {endpoint_name} 无返回内容")
                if "promptFeedback" in result:
                    print(f"  [Debug] promptFeedback: {result['promptFeedback']}")
                continue
                
            # 处理多部分响应（如思考模型：part[0]=思考过程，part[1]=内容）
            parts = candidates[0].get("content", {}).get("parts", [])
            content_text = "".join([p.get("text", "") for p in parts])
            
            # 1. 尝试从 Markdown JSON 块中提取
            match = re.search(r"```json\s*(\{.*?\})\s*```", content_text, re.DOTALL)
            if match:
                json_str = match.group(1)
                return json.loads(json_str)
            
            # 2. 回退：提取 { 和 } 之间的原始 JSON
            start_idx = content_text.find('{')
            end_idx = content_text.rfind('}')
            
            if start_idx != -1 and end_idx != -1:
                json_str = content_text[start_idx : end_idx + 1]
                return json.loads(json_str)
            else:
                print(f"  警告: {endpoint_name} 响应中未找到 JSON 对象")
                # 保存调试信息
                debug_file = BASE_DIR / "debug_v2_response.json"
                with open(debug_file, "w", encoding="utf-8") as f:
                    json.dump(candidates, f, ensure_ascii=False, indent=2)
                print(f"  [Debug] 完整响应已保存到 {debug_file}")
                return None
            
        except json.JSONDecodeError as e:
            print(f"  JSON 解析错误: {e}")
        except Exception as e:
            print(f"  {endpoint_name} 异常: {e}")
            
    print("  所有 API 端点均失败")
    return None


def validate_schema(data: Dict) -> bool:
    """验证提取的数据是否符合 V2 Schema"""
    if not isinstance(data, dict):
        print("  验证错误: 数据不是字典")
        return False
    
    for key in REQUIRED_KEYS:
        if key not in data:
            print(f"  验证错误: 缺少字段 '{key}'")
            return False
        
        # meta 是对象，其他都是数组
        if key == "meta":
            if not isinstance(data[key], dict):
                print(f"  验证错误: 字段 '{key}' 应为对象")
                return False
        else:
            if not isinstance(data[key], list):
                print(f"  验证错误: 字段 '{key}' 应为数组")
                return False
            
    return True


def extract_chapter_info(filename: str) -> tuple:
    """
    从文件名提取章节ID和标题
    
    支持两种格式：
    - 旧格式: 006_第1章 惊蛰.txt -> (6, "第1章 惊蛰")
    - 新格式: 第1章 惊蛰.txt -> (1, "第1章 惊蛰")
    """
    import re
    basename = os.path.basename(filename).replace('.txt', '')
    
    # 尝试旧格式: 006_第1章 惊蛰
    if "_" in basename:
        parts = basename.split('_', 1)
        if len(parts) == 2 and parts[0].isdigit():
            chapter_id = int(parts[0])
            chapter_title = parts[1]
            return chapter_id, chapter_title
    
    # 尝试新格式: 第1章 惊蛰
    match = re.match(r'第(\d+)章', basename)
    if match:
        chapter_id = int(match.group(1))
        return chapter_id, basename
    
    return None, basename


def get_sort_key(filepath: str) -> int:
    """
    获取文件排序键
    
    支持两种格式：
    - 旧格式: 006_第1章 惊蛰.txt -> 6
    - 新格式: 第1章 惊蛰.txt -> 1
    """
    import re
    basename = os.path.basename(filepath)
    
    # 尝试旧格式
    if "_" in basename:
        parts = basename.split('_', 1)
        if parts[0].isdigit():
            return int(parts[0])
    
    # 尝试新格式
    match = re.match(r'第(\d+)章', basename)
    if match:
        return int(match.group(1))
    
    return 0


def main():
    parser = argparse.ArgumentParser(description='《剑来》知识图谱提取脚本 V2')
    parser.add_argument('--limit', type=int, default=0, help='限制处理章节数量（0=无限制）')
    parser.add_argument('--start', type=int, default=0, help='起始章节索引')
    parser.add_argument('--reset-state', action='store_true', help='重置状态文件')
    args = parser.parse_args()
    
    # 创建输出目录
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 加载或初始化状态
    if args.reset_state and STATE_FILE.exists():
        STATE_FILE.unlink()
        print("状态文件已重置")
    
    state = ExtractionState.load(STATE_FILE)
    print(f"加载状态: 最后处理章节 {state.last_chapter_id}")
    
    # 加载提示词模板
    print(f"加载提示词: {PROMPT_FILE}")
    prompt_template = load_prompt()
    
    # 获取章节文件列表
    files = sorted(
        glob.glob(str(CHAPTERS_DIR / "*.txt")), 
        key=get_sort_key
    )
    print(f"发现 {len(files)} 个章节文件")
    
    # 获取已处理的文件
    processed_files = set()
    for json_file in glob.glob(str(OUTPUT_DIR / "*.json")):
        if "extraction_state" in json_file:
            continue
        basename = os.path.basename(json_file).replace('.json', '.txt')
        processed_files.add(basename)
    print(f"已处理 {len(processed_files)} 个章节")
    
    # 处理章节
    processed_count = 0
    for i, file_path in enumerate(files):
        if i < args.start:
            continue
            
        if args.limit > 0 and processed_count >= args.limit:
            print(f"\n已达到限制 ({args.limit} 章)，停止处理")
            break
            
        filename = os.path.basename(file_path)
        
        if filename in processed_files:
            continue
            
        chapter_id, chapter_title = extract_chapter_info(filename)
        print(f"\n[{i+1}/{len(files)}] 处理: {filename}")
        
        # 注入动态上下文到提示词
        system_prompt = inject_context(prompt_template, state)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
            
        # 重试机制
        max_retries = 3
        success = False
        
        for attempt in range(max_retries):
            if attempt > 0:
                print(f"  重试 {attempt+1}/{max_retries}...")
                time.sleep(2)
            
            data = call_llm_api(text, system_prompt)
            
            if data:
                # 注入 meta 信息（如果 LLM 没有正确填写）
                if "meta" not in data or not data["meta"]:
                    data["meta"] = {}
                if chapter_id and "chapter_id" not in data["meta"]:
                    data["meta"]["chapter_id"] = chapter_id
                if chapter_title and "chapter_title" not in data["meta"]:
                    data["meta"]["chapter_title"] = chapter_title
                
                if validate_schema(data):
                    output_path = OUTPUT_DIR / filename.replace('.txt', '.json')
                    try:
                        with open(output_path, 'w', encoding='utf-8') as f:
                            json.dump(data, f, ensure_ascii=False, indent=2)
                        print(f"  ✓ 保存: {output_path}")
                        
                        # 更新状态
                        if chapter_id:
                            state.update_from_extraction(data, chapter_id)
                            state.save(STATE_FILE)
                            print(f"  ✓ 状态已更新: 在场人物 {len(state.characters_on_scene)}, 活跃事件 {len(state.active_events)}, 伏笔 {len(state.unidentified_buffer)}")
                        
                        success = True
                        processed_count += 1
                        break
                    except Exception as e:
                        print(f"  保存错误: {e}")
                else:
                    print("  Schema 验证失败")
            else:
                print("  提取失败 (API 或 JSON 错误)")
        
        if not success:
            print(f"  ✗ 跳过 {filename}（{max_retries} 次尝试失败）")
    
    print(f"\n完成！共处理 {processed_count} 个章节")
    print(f"最终状态: 在场人物 {len(state.characters_on_scene)}, 近期人物 {len(state.recent_characters)}, 活跃事件 {len(state.active_events)}, 伏笔 {len(state.unidentified_buffer)}")


if __name__ == "__main__":
    main()
