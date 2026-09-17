# 项目整理分析报告

> 生成日期: 2026-03-04
> 目的: 全面梳理项目目录结构、数据管道、LLM脚本，为后续整理提供依据

---

## 一、项目目录总体现状

### 根目录文件统计

- Python 脚本: 40+ 个（散落在根目录）
- JSON 数据文件: 10+ 个（与 data/ 目录重复）
- Markdown 文档: 10+ 个（混杂 PRD/设计/临时计划）
- 日志文件: 5 个
- 调试产物: 5+ 个
- 配置文件: 3 个 (nginx)
- 密钥文件: 2 个
- 图片文件: 3 个

### 目录大小分布

| 目录 | 大小 | 说明 |
|---|---|---|
| `taro-app/` | 797MB | 含 node_modules |
| `data/` | 393MB | 主要是 data/build/ (350MB) |
| `item_images/` | 326MB | 2300张物品图标 |
| `frontend/` | 231MB | 含 node_modules |
| `人物设计图/` | 40MB | Excel设定 |
| `chapters/` | 38MB | 1218章原始文本 |
| `merged_chapters/` | 36MB | 合并章节(已废弃) |
| `temp_images/` | 26MB | 3张UUID临时图片 |
| `images/` | 2.8MB | 少量图片 |
| `openspec/` | 232KB | 架构文档 |
| `scripts/` | 172KB | Python脚本(部分) |
| `docs/` | 92KB | 文档 |
| `__pycache__/` | 76KB | Python缓存 |
| `shushu.host_nginx 3/` | 24KB | SSL证书(不应在此) |

### data/ 子目录

| 目录 | 大小 | 用途 |
|---|---|---|
| `data/build/` | 350MB | 核心构建产物(含 character_images/, profiles_v3/, items/) |
| `data/dist/` | 16MB | **最终生产数据**(前端实际使用) |
| `data/raw/` | 13MB | AI提取的原始JSON(1218个文件) |
| `data/images/` | 12MB | 人物图片 |
| `data/backup/` | 1.8MB | 旧备份(duplicates_v3) |
| `data/v2/` | 100KB | 实验性V2提取(5个文件+state, 未投产) |

### data/dist/ (最终生产数据)

```
data/dist/
├── characters_lite.json   # 人物列表轻量版
├── characters_top.json    # 首页Top20人物
├── chars/                 # 1603个人物详情JSON
├── factions.json          # 势力(含score/members)
├── img/avatars/           # 头像图片
├── items_lite.json        # 物品列表
├── locations.json         # 地点
├── quotes.json            # 全量金句
├── quotes_top.json        # 热门金句
├── relations.json         # 关系图谱
├── search_index.json      # 搜索索引
└── timeline.json          # 时间线
```

### data/build/ 内容明细

```
data/build/
├── characters.json              # 全量人物数据(核心)
├── character_images/            # AI生成的人物头像
├── character_image_prompts.json # 头像生成提示词
├── character_profile_chen_ping_an.json  # 陈平安专用档案
├── profiles_v3/                 # V3人物档案(每人一个JSON)
├── factions.json                # 全量势力数据
├── factions_rewritten.json      # AI重写后的势力描述
├── items.json                   # 全量物品数据
├── items_lite.json              # 物品轻量版
├── items/                       # 单物品详情文件
├── items_cleaned.json           # AI清洗后物品
├── items_cleaned_wip.json       # 物品清洗中间checkpoint
├── items_enriched.json          # NotebookLM富化后物品
├── items_step1_aggregated.json  # 物品处理step1产出
├── items_step2_ai_raw.json      # 物品处理step2产出
├── locations.json               # 全量地点数据
├── locations_cleaned.json       # AI清洗后地点
├── locations_step1_aggregated.json  # 地点处理step1产出
├── locations_step2_ai_raw.json  # 地点处理step2产出
├── timeline.json                # 时间线事件
├── search_index.json            # 搜索索引
├── bio_raw.json                 # 人物简介原始提取
├── bio_summarized.json          # AI总结后的简介
├── metadata_raw.json            # 元数据原始提取
├── metadata_cleaned.json        # AI清洗后元数据
├── all_appearances.json         # 汇总外貌数据
├── generic_names_list.txt       # 泛指名列表
├── generic_names_review.txt     # 泛指名审核
├── missing_profiles_list.txt    # 缺失档案列表
├── profile_generation_blocklist.txt  # 档案生成黑名单
├── debug_batch_1.txt            # 调试产物
└── test_cuicheng.json           # 测试产物
```

---

## 二、完整数据管道

### 阶段 0: 原始素材

| 文件 | 大小 | 说明 |
|---|---|---|
| `chapters/*.txt` | 38MB | 1218章原始文本, 格式: `006_第1章 惊蛰.txt` |
| `剑来 (烽火戏诸侯).md` | 37MB | 全书Markdown(单文件) |
| `人物设计图/*.xlsx` | 40MB | Excel人物设定 |

### 阶段 1: AI提取 (章节 → 结构化JSON)

**核心脚本**: `extract_pipeline.py`

- **输入**: `chapters/*.txt` (1218个文件)
- **输出**: `data/raw/*.json` (1218个文件, 13MB)
- **LLM**: 本地 Gemini API (`gemini-3-pro-preview`)
- **调用方式**: Gemini generateContent API
- **提取的7类实体**: characters, relations, items, locations, factions, quotes, events
- **容错机制**: 双端点(主/备) + 3次重试 + 429自动切换
- **状态**: 已完成全部1218章

**废弃版本**: `extract_v2.py` → `data/v2/` (只处理了5章就停了)

- V2增加了动态上下文注入、跨章节状态追踪
- Schema更复杂(增加 meta, economics, plot_links)
- 从未投入生产

### 阶段 2: 知识库构建 (合并+归一化)

**核心脚本**: `build_knowledge_base.py`

- **输入**: `data/raw/*.json`
- **输出**: `data/build/` 下的基础数据
- **依赖模块**:
  - `character_merger.py` — 226个人物别名映射
  - `faction_normalizer.py` — 势力名标准化
  - `item_normalizer.py` — 物品名标准化
  - `cultivation_normalizer.py` — 修真境界标准化
  - `location_normalizer.py` — (未直接import，但影响数据)

**内部处理流程**:

1. 遍历所有 raw JSON，聚合 characters/items/locations/factions/events/quotes
2. 人物：调用 `character_merger.py` 做别名合并 (226个映射)
3. 势力：调用 `faction_normalizer.py` 标准化
4. 物品：调用 `item_normalizer.py` 标准化
5. 境界：调用 `cultivation_normalizer.py` 拆分武道/炼气日志
6. 自动生成反向关系
7. **自动拾取 AI 清洗结果** (如果 data/build/ 下存在以下文件):
   - `bio_summarized.json` → 覆盖 bio_summary
   - `metadata_cleaned.json` → 覆盖 aliases/factions/tags
   - `factions_rewritten.json` → 覆盖势力描述
   - `items_enriched.json` 或 `items_cleaned.json` → 覆盖物品数据
   - `locations_cleaned.json` → 覆盖地点数据
8. 构建搜索索引

**产出文件**:
- `data/build/characters.json` — 全量人物
- `data/build/items.json` + `items_lite.json` + `items/*.json` — 物品
- `data/build/locations.json` — 地点
- `data/build/factions.json` — 势力
- `data/build/timeline.json` — 时间线
- `data/build/search_index.json` — 搜索索引

### 阶段 3: AI清洗 (各维度独立处理)

每个清洗脚本都是"运行一次，结果持久化"模式，产出文件放在 `data/build/`，等下次重跑 `build_knowledge_base.py` 时自动拾取。

#### 3a. 人物简介总结: `summarize_bio.py`

- **工作流**: `extract` → `summarize` → `replace` (三步CLI)
- **输入**: `data/build/characters.json`
- **中间**: `data/build/bio_raw.json`
- **输出**: `data/build/bio_summarized.json` → 回写 characters.json
- **LLM**: Gemini API (preview/high)
- **策略**: 长简介(>5000字)单独处理，短简介10个一批
- **温度**: 0.3

#### 3b. 元数据清洗: `clean_metadata.py`

- **工作流**: `extract` → `process` → `replace` (三步CLI)
- **输入**: `data/build/characters.json`
- **中间**: `data/build/metadata_raw.json`
- **输出**: `data/build/metadata_cleaned.json` → 回写 characters.json
- **LLM**: Gemini API (high优先)
- **策略**: 陈平安单独处理，其他100个一批
- **温度**: 0.1
- **清洗内容**: 别名去泛指、势力归一化拆分、标签去冗余

#### 3c. 物品清洗 (三步流水线)

1. `step1_aggregate.py`: `data/build/items.json` → `items_step1_aggregated.json`
   - 按标准化名称聚合，合并重复物品
   - 依赖: `item_normalizer.py`

2. `step2_ai_process.py`: → `items_step2_ai_raw.json`
   - AI批量清洗(description/grade/status/type/aliases)
   - LLM: Gemini API, 300个一批
   - 依赖: `item_normalizer.py`

3. `step3_finalize.py`: → `items_cleaned.json`
   - 合并AI结果与本地数据
   - 去重、处理ownership_log

**旧版合体脚本**: `clean_items.py` (已被三步版替代)

#### 3d. 物品富化: `enrich_items_pipeline.py`

- **输入**: `items.json` (根目录) 或 `items_enriched.json` (续传)
- **输出**: `items_enriched.json` (根目录, **注意: 不在 data/build/**)
- **LLM**: NotebookLM CLI (notebook ID: `3dcbda80-313f-49cc-ab2c-d85833ec202c`)
- **策略**: 10个一批，优先处理仙兵/法宝，支持续传
- **富化字段**: type, subtype, holder, rank, visual, provenance, evolution等

#### 3e. 地点清洗 (三步流水线)

1. `step1_aggregate_locations.py`: `data/build/locations.json` → `locations_step1_aggregated.json`
2. `step2_ai_process_locations.py`: → `locations_step2_ai_raw.json` (100个一批)
3. `step3_finalize_locations.py`: → `locations_cleaned.json`

#### 3f. 势力描述重写: `rewrite_faction_descriptions.py`

- **工作流**: `process` → `replace` (两步CLI)
- **输入**: `data/build/factions.json` (筛选含"；"的合并描述)
- **输出**: `data/build/factions_rewritten.json` → 回写 factions.json
- **LLM**: Gemini API (high优先), 100个一批, 温度0.3

### 阶段 4: 人物档案生成 (V3 Profile)

#### 批量生成: `scripts/batch_generate_profiles.py`

- **输入**: `data/build/characters.json` + `docs/notebooklm_prompt_char_profile.md`
- **输出**: `data/build/profiles_v3/*.json`
- **LLM**: NotebookLM CLI
- **策略**: 按重要性(quotes+relations数量)排序，支持 blocklist
- **合并**: AI生成的档案 + 原有 quotes/relations
- **辅助脚本**:
  - `scripts/regenerate_chen_ping_an.py` — 单独重新生成陈平安
  - `scripts/retry_failed_errors.py` — 重试JSON解析失败的人物

#### 外貌提取: `scripts/extract_appearances.py`

- **输入**: `data/build/profiles_v3/*.json`
- **输出**: `data/build/all_appearances.json`

### 阶段 5: 图片生成

#### 人物头像: `scripts/batch_generate_character_images.py`

- **输入**: `data/build/character_image_prompts.json`
- **输出**: `data/build/character_images/*.jpg`
- **工具**: 本地 Draw Things (通过 `.agent/skills/image-gen/scripts/generate_image.py`)
- **并发**: 多线程

#### 物品图标 (方式一): `generate_item_icons.py`

- **输入**: `frontend/public/data/items.json`
- **输出**: `frontend/public/images/items/*.png`
- **LLM**: Gemini Image API (`gemini-3-pro-image`)
- **策略**: 50个一批

#### 物品图标 (方式二): `batch_generate_images.py`

- **输入**: `items_prompts.json` (根目录)
- **输出**: `item_images/*.jpg` (根目录, 2300张, 326MB)
- **工具**: ModelScope (远程) + Draw Things (本地降级)
- **并发**: 3线程

### 阶段 6: 前端数据打包

**核心脚本**: `scripts/build_frontend_data.py`

- **输入**:
  - `data/build/profiles_v3/*.json`
  - `data/build/character_images/`
  - `taro-app/public/data/img/avatars/` (UGC头像)
  - `taro-app/src/data/relations.json`
  - `data/build/locations.json`
  - `data/build/items_lite.json`
  - `data/build/factions.json`
- **输出**: `data/dist/` (16MB, 最终生产数据)
  - `characters_lite.json`, `chars/*.json`, `quotes.json`, `quotes_top.json`
  - `relations.json`, `factions.json`, `locations.json`, `items_lite.json`
  - `search_index.json`, `timeline.json`, `img/avatars/`

**辅助脚本**: `generate_top_characters.py`

- **输入**: `data/dist/characters_lite.json`
- **输出**: `data/dist/characters_top.json` (Top 20)

### 阶段 7: 部署上线

- `data/dist/` 内容部署到 `https://shushu.host/jianlai/data/`
- 通过 nginx 静态文件服务
- 小程序通过 `Taro.request()` 从该URL加载数据
- 数据带 24小时本地缓存 (Taro Storage)
- 配置文件: `nginx_new.conf`, `mcp-website.conf`, `markdown-ssr.conf`

### UGC 热更新流程

`scripts/review_ugc.py` 实现了完整的用户投稿审核+热部署:

1. 从云端 API 拉取待审核投稿
2. 人工审核 (交互式CLI: Y/N/S/Q)
3. 通过后调用 LLM 润色合并内容
4. 修改 `data/build/profiles_v3/` 或 `data/build/*.json`
5. 自动触发 `scripts/build_frontend_data.py` 重新构建
6. 自动触发 `generate_top_characters.py` 更新Top
7. 增量推送改动文件到云端 (curl API)

---

## 三、LLM 脚本完整盘点

### 调用方式

| 途径 | 端点 | API格式 |
|---|---|---|
| 本地 Gemini API (gcli2api) | `http://127.0.0.1:7861` | Gemini generateContent |
| 本地 Gemini API (gcli2api) | `http://127.0.0.1:7861` | OpenAI chat/completions (仅review_ugc.py) |
| NotebookLM CLI | `notebooklm ask --notebook <ID>` | CLI subprocess |

### 端点配置

```python
# 主端点 (Gemini CLI)
("http://127.0.0.1:7861/v1", "gemini-3-pro-preview")

# 备用端点 (Antigravity IDE)
("http://127.0.0.1:7861/antigravity/v1", "gemini-3-pro-low")   # extract_pipeline
("http://127.0.0.1:7861/antigravity/v1", "gemini-3-pro-high")  # 清洗脚本

# 图片生成
("http://127.0.0.1:7861/antigravity/v1", "gemini-3-pro-image")
```

### 模型使用分布

| 模型 | 使用场景 |
|---|---|
| `gemini-3-pro-preview` | 章节提取、物品清洗(step2) |
| `gemini-3-pro-high` | 元数据清洗、势力重写、简介总结(备用) |
| `gemini-3-pro-low` | 章节提取(备用) |
| `gemini-3-pro-image` | 物品图标生成 |
| `gemini-3-pro-preview-maxthinking` | PDF转换(无关脚本) |

### 生产在用的LLM脚本 (8个)

| # | 脚本 | 调用方式 | 频率 |
|---|---|---|---|
| 1 | `extract_pipeline.py` | Gemini API | 一次性(已完成) |
| 2 | `summarize_bio.py` | Gemini API | 一次性(已完成) |
| 3 | `clean_metadata.py` | Gemini API | 一次性(已完成) |
| 4 | `step2_ai_process.py` | Gemini API | 一次性(已完成) |
| 5 | `step2_ai_process_locations.py` | Gemini API | 一次性(已完成) |
| 6 | `rewrite_faction_descriptions.py` | Gemini API | 一次性(已完成) |
| 7 | `scripts/batch_generate_profiles.py` | NotebookLM CLI | 一次性(已完成) |
| 8 | `scripts/review_ugc.py` | Gemini API (OpenAI格式) | **常态运行** |

### 辅助/一次性LLM脚本 (7个)

| 脚本 | 被什么替代/状态 |
|---|---|
| `clean_items.py` | 被 step1/2/3 三步版替代 |
| `enrich_items_pipeline.py` | 已完成, 产出 items_enriched.json |
| `scripts/retry_failed_errors.py` | 辅助脚本, 已完成 |
| `scripts/regenerate_chen_ping_an.py` | 一次性, 已完成 |
| `generate_item_icons.py` | 已完成(产出到frontend/) |
| `batch_generate_images.py` | 已完成(产出到item_images/) |
| `scripts/batch_generate_character_images.py` | 已完成 |

### 与本项目无关的LLM脚本 (2个)

| 脚本 | 说明 |
|---|---|
| `pdf2md_ref.py` | 保险PDF转Markdown, 路径指向 gcli2api/ |
| `reference_image_script.py` | 纯API测试脚本 |

### 代码重复问题

以下函数在 10+ 个文件中被复制粘贴:

```python
# 每个脚本都独立实现了:
def call_gemini_api(prompt):     # API调用 + 双端点容错
def extract_json(text):          # 从LLM响应提取JSON
def repair_json_content(text):   # 修复JSON格式问题 (3个文件)
def clean_json_response(text):   # 清理JSON响应 (3个文件)
```

差异仅在于: 端点优先级、超时时间(60s~600s)、temperature(0.1~0.3)、是否启用 responseMimeType

---

## 四、根目录文件归属分析

### 可直接清理的文件

| 类别 | 文件 | 原因 |
|---|---|---|
| 调试产物 | `debug_api_response.json` (24KB) | 一次性调试输出 |
| 调试产物 | `debug_no_candidates.json` (110B) | 一次性调试输出 |
| 调试产物 | `debug_keys.py` (1.2KB) | 一次性调试脚本 |
| 调试产物 | `debug_modelscope_size.py` (4KB) | 一次性调试脚本 |
| 日志 | `batch_error.log` (490KB) | profile生成错误日志 |
| 日志 | `clean_items.log` (285B) | 物品清洗日志 |
| 日志 | `step2.log` (133B) | step2运行日志 |
| 日志 | `step2_final.log` (392B) | step2运行日志 |
| 日志 | `step2_final_v4.log` (594B) | step2运行日志 |
| 临时计划 | `task_plan.md` (578B) | AI agent中间产物 |
| 临时计划 | `progress.md` (75B) | AI agent中间产物 |
| 临时计划 | `findings.md` (254B) | AI agent中间产物 |
| 临时计划 | `implementation_plan.md` (3KB) | AI agent中间产物 |
| 临时计划 | `temp_script_plan.py` (1.3KB) | 临时脚本计划 |
| 临时测试 | `test_concurrency.py` (1.4KB) | 一次性并发测试 |
| 临时测试 | `test_ar_16_9.jpg` (18KB) | 测试图片 |
| 临时测试 | `v3_check.py` (501B) | 一次性检查脚本 |
| 临时图片 | `temp_images/` (26MB, 3张) | UGC审核临时预览 |
| 缓存 | `__pycache__/` (76KB) | Python缓存 |
| 重复报告 | `duplicate_report.json` (22KB) | 数据清洗中间报告 |
| 重复报告 | `duplicate_report.txt` (219KB) | 数据清洗中间报告 |
| 重复报告 | `duplicate_candidates.md` (10KB) | 数据清洗中间报告 |
| 重复报告 | `duplicate_candidates_deep.md` (17KB) | 数据清洗中间报告 |
| 无关脚本 | `pdf2md_ref.py` (4.4KB) | 保险PDF处理, 完全无关 |
| 无关脚本 | `reference_image_script.py` (4.2KB) | 纯API测试 |
| 冗余图片 | `icon.png` (5.2MB) | 如只需jpg则png冗余 |
| 敏感文件 | `deploy_key.pem` (451B) | 不应在项目目录 |
| 敏感文件 | `insure.pem` (1.7KB) | 不应在项目目录 |
| 敏感文件 | `shushu.host_nginx 3/` (24KB, 含SSL证书) | 不应在项目目录 |
| 空目录 | `.cursor/` | 内容已删除 |

### 根目录散落的重复数据

| 文件 | 大小 | 重复位置 | 说明 |
|---|---|---|---|
| `bio_summarized.json` | 109KB | `data/build/bio_summarized.json` | 完全重复 |
| `items.json` | 1.3MB | `data/build/items.json` | 完全重复 |
| `items_enriched.json` | 4.3MB | `data/build/items_enriched.json` | 完全重复 |
| `items_prompts.json` | 1.3MB | — | 一次性中间产物 |
| `relations_full.json` | 709KB | — | 被 build_knowledge_base.py 替代 |
| `relations_clean.json` | 248KB | — | process_data.py 产出, 已废弃 |
| `relations_demo.json` | 5.4KB | — | 早期demo |
| `extracted_character_names.txt` | 22KB | — | 一次性产物 |
| `name_collisions.json` | 174KB | — | 一次性分析报告 |
| `character_prompts.md` | 20KB | — | 绘图提示词参考 |

### 应归类整理的脚本

#### → `scripts/pipeline/` (核心提取管线)
- `extract_pipeline.py`
- `build_knowledge_base.py`
- `character_merger.py`

#### → `scripts/normalize/` (标准化模块)
- `cultivation_normalizer.py`
- `faction_normalizer.py`
- `item_normalizer.py`
- `location_normalizer.py`

#### → `scripts/clean/` (AI清洗脚本)
- `summarize_bio.py`
- `clean_metadata.py`
- `step1_aggregate.py`
- `step2_ai_process.py`
- `step3_finalize.py`
- `step1_aggregate_locations.py`
- `step2_ai_process_locations.py`
- `step3_finalize_locations.py`
- `rewrite_faction_descriptions.py`
- `enrich_items_pipeline.py`
- `clean_items.py` (已废弃, 可删或归档)

#### → `scripts/image/` (图片生成)
- `batch_generate_images.py`
- `generate_item_icons.py`
- `compress_avatars.py`
- `run_character_generation.py`

#### → `scripts/util/` (工具脚本)
- `check_rows.py`
- `check_isolated_chars.py`
- `export_prompts.py`
- `verify_chapters.py`
- `rename_chapters.py`
- `read_excel_structure.py`
- `split_characters.py`
- `split_demo.py`
- `process_data.py` (已废弃)
- `generate_top_characters.py`

#### → `docs/` (文档)
- `app_prd.md`
- `ui_design_brief.md`
- `world_story.md`
- `character_prompts.md`
- `UGC审核与热更新_完整说明文档.md`

#### → `config/` (配置)
- `nginx_new.conf`
- `markdown-ssr.conf`
- `mcp-website.conf`

### 已废弃的目录/文件

| 目录/文件 | 原因 |
|---|---|
| `merged_chapters/` (36MB) | 122个合并章节, 无任何脚本引用 |
| `item_images/` (326MB) | 应归入 data/ 体系, 或确认是否已上传到服务器 |
| `data/v2/` (100KB) | V2提取实验, 未投产 |
| `data/backup/duplicates_v3/` | 旧备份 |
| `graph_view.html` (8.2KB) | 早期图谱可视化demo |
| `architecture.canvas` (10KB) | Obsidian画布文件 |
| `.obsidian/` | Obsidian配置, 如不用Obsidian可删 |
| `.agent/` | Agent配置, 需确认是否仍在使用 |
| `openspec/` | 架构提案, 需确认是否仍有参考价值 |

---

## 五、缺失的 .gitignore

项目没有 `.gitignore`，以下内容应被忽略:

```
# Python
__pycache__/
*.pyc
*.pyo

# Node.js
node_modules/
.taro/

# OS
.DS_Store
Thumbs.db

# IDE
.cursor/
.vscode/

# 敏感文件
*.pem
*.key
*.crt
*.csr

# 临时文件
temp_images/
*.log
debug_*.json

# 构建产物
data/build/
data/dist/
frontend/dist/
taro-app/dist/
```

---

## 六、scripts/ 目录现有内容

```
scripts/
├── __pycache__/
├── analyze_duplicates.py           # 分析重复人物
├── analyze_generic_names_score.py  # 分析泛指名评分
├── api_ugc.py                      # UGC API服务端
├── batch_generate_character_images.py  # 批量生成人物头像
├── batch_generate_profiles.py      # 批量生成V3人物档案
├── build_frontend_data.py          # 最终前端数据打包
├── check_json_names.py             # 检查JSON名称
├── cleanup_duplicates.py           # 清理重复数据
├── cleanup_hallucinations.py       # 清理AI幻觉数据
├── extract_appearances.py          # 提取外貌数据
├── find_generic_names.py           # 找泛指名
├── find_incomplete_profiles.py     # 找不完整档案
├── find_potential_duplicates.py    # 找潜在重复
├── generate_character_prompts.py   # 生成人物绘画提示词
├── generate_relations_graph.py     # 生成关系图
├── merge_character_data_v3.py      # V3人物数据合并(陈平安专用)
├── regenerate_chen_ping_an.py      # 重新生成陈平安档案
├── report_missing_profiles.py      # 报告缺失档案
├── retry_failed_errors.py          # 重试失败的档案生成
├── review_ugc.py                   # UGC审核系统
├── test_generate_cuicheng.py       # 测试生成崔瀺
├── ugc_data/                       # UGC本地数据
├── verify_batch_progress.py        # 验证批量进度
└── verify_ssh.sh                   # SSH验证脚本
```

---

## 七、前端数据加载方式

### 小程序 (taro-app/)

- 数据通过 `Taro.request()` 从 `https://shushu.host/jianlai/data/` 加载
- 使用 `useData.ts` 中封装的 hooks
- 三级缓存: 内存 → Taro Storage (24h TTL) → 网络
- 渐进式预加载: 1s后搜索索引 → 2s后人物+势力 → 4s后物品+地点
- 人物详情按需加载: `chars/{name}.json`

### 加载的文件清单

| 文件 | Hook | 场景 |
|---|---|---|
| `characters_top.json` | `useTopCharacters()` | 首页 |
| `characters_lite.json` | `useCharacters()` | 人物列表 |
| `chars/{name}.json` | `useCharacter(name)` | 人物详情 |
| `items_lite.json` | `useItems()` | 物品列表 |
| `items/{name}.json` | `useItem(name)` | 物品详情(注:指向 shushu.host) |
| `factions.json` | `useFactions()` | 势力列表 |
| `locations.json` | `useLocations()` | 地点列表 |
| `relations.json` | `useRelations()` | 关系图谱 |
| `timeline.json` | `useTimeline()` | 时间线 |
| `search_index.json` | `useSearch()` | 搜索 |
| `quotes_top.json` | `useQuotes()` | 首页金句(先加载) |
| `quotes.json` | `useQuotes()` | 完整金句(5s后懒加载) |
