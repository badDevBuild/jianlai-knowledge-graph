"""
金句分类标签批量分类脚本
使用 Gemini API 对 quotes.json 中的金句进行情感分类
6 个标签: 励志 / 感伤 / 豪气 / 幽默 / 哲理 / 温情
每条金句 1-2 个标签

用法: python scripts/classify_quotes.py
幂等: 已有 tags 的金句会被跳过
"""

import json
import os
import time
import httpx

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(_SCRIPT_DIR)
QUOTES_PATH = os.path.join(_PROJECT_DIR, 'data/dist/quotes.json')

API_CONFIGS = [
    ("http://127.0.0.1:7861/v1", "gemini-3-pro-preview"),
    ("http://127.0.0.1:7861/antigravity/v1", "gemini-3-pro-low"),
]
API_PASSWORD = os.environ.get("JIANLAI_LLM_PASSWORD", "")

BATCH_SIZE = 100  # 每批分类的金句数量
VALID_TAGS = {"励志", "感伤", "豪气", "幽默", "哲理", "温情"}

SYSTEM_PROMPT = """你是金句分类专家。给定一批金句，为每条金句分配1-2个情感标签。

可用标签（只能用这6个）：
- 励志：激励人心、催人奋进
- 感伤：伤感、离别、遗憾
- 豪气：气势磅礴、英雄气概
- 幽默：诙谐、调侃、逗趣
- 哲理：深刻道理、人生感悟
- 温情：温暖人心、感人至深

规则：
1. 每条金句必须有1-2个标签，不能为空
2. 只使用上述6个标签，不能自创
3. 返回严格 JSON 数组，每个元素是标签数组

示例输入：
["天下事，有所激有所逼而成者，居其半。", "你好，我叫阿良，善良的良。"]

示例输出：
[["哲理", "励志"], ["温情"]]
"""


def call_api(messages, config_idx=0):
    """调用 API，带容错切换"""
    base_url, model = API_CONFIGS[config_idx]
    try:
        resp = httpx.post(
            f"{base_url}/chat/completions",
            json={
                "model": model,
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": 65535,
            },
            headers={"Authorization": f"Bearer {API_PASSWORD}"},
            timeout=180,
        )
        if resp.status_code == 429 and config_idx == 0:
            print("  速率限制，切换备用端点...")
            time.sleep(2)
            return call_api(messages, 1)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        if config_idx == 0:
            print(f"  主端点失败 ({e})，切换备用...")
            time.sleep(1)
            return call_api(messages, 1)
        raise


def parse_tags_response(text, batch_size):
    """解析 API 返回的标签数组"""
    # 提取 JSON 部分
    text = text.strip()
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()

    tags_list = json.loads(text)

    if not isinstance(tags_list, list) or len(tags_list) != batch_size:
        raise ValueError(f"期望 {batch_size} 个结果，得到 {len(tags_list) if isinstance(tags_list, list) else 'non-list'}")

    # 验证标签
    result = []
    for tags in tags_list:
        if isinstance(tags, str):
            tags = [tags]
        valid = [t for t in tags if t in VALID_TAGS]
        if not valid:
            valid = ["哲理"]  # 兜底
        result.append(valid[:2])
    return result


def main():
    with open(QUOTES_PATH, 'r', encoding='utf-8') as f:
        quotes = json.load(f)

    # 找出未分类的金句
    unclassified = [(i, q) for i, q in enumerate(quotes) if not q.get('tags')]
    print(f"总金句: {len(quotes)}, 待分类: {len(unclassified)}")

    if not unclassified:
        print("所有金句已分类完成！")
        return

    classified_count = 0
    for batch_start in range(0, len(unclassified), BATCH_SIZE):
        batch = unclassified[batch_start:batch_start + BATCH_SIZE]
        contents = [q['content'] for _, q in batch]

        print(f"\n批次 {batch_start // BATCH_SIZE + 1}: 分类 {len(batch)} 条金句...")

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(contents, ensure_ascii=False)},
        ]

        try:
            response = call_api(messages)
            tags_list = parse_tags_response(response, len(batch))

            for (idx, quote), tags in zip(batch, tags_list):
                quotes[idx]['tags'] = tags
                classified_count += 1

            print(f"  已分类 {classified_count}/{len(unclassified)}")

            # 每批保存一次（断点续跑）
            with open(QUOTES_PATH, 'w', encoding='utf-8') as f:
                json.dump(quotes, f, ensure_ascii=False, indent=2)

            time.sleep(3)

        except Exception as e:
            print(f"  批次失败: {e}")
            # 保存已有进度
            with open(QUOTES_PATH, 'w', encoding='utf-8') as f:
                json.dump(quotes, f, ensure_ascii=False, indent=2)
            print(f"  已保存进度 ({classified_count} 条)")
            time.sleep(10)
            continue

    print(f"\n完成！共分类 {classified_count} 条金句")

    # 持久化标签到 build 目录（防止 build_frontend_data.py 重建时丢失）
    tags_path = os.path.join(_PROJECT_DIR, 'data/build/quote_tags.json')
    tag_map = {}
    for q in quotes:
        if q.get('tags'):
            key = q['content'][:50]  # 用前50字符作为 key
            tag_map[key] = q['tags']
    with open(tags_path, 'w', encoding='utf-8') as f:
        json.dump(tag_map, f, ensure_ascii=False, indent=2)
    print(f"持久化 {len(tag_map)} 条标签到 {tags_path}")

    # 统计
    tag_counts = {}
    for q in quotes:
        for t in q.get('tags', []):
            tag_counts[t] = tag_counts.get(t, 0) + 1
    print("\n标签统计:")
    for tag, count in sorted(tag_counts.items(), key=lambda x: -x[1]):
        print(f"  {tag}: {count}")


if __name__ == '__main__':
    main()
