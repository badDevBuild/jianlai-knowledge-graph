# 剑来知识图谱项目

> 这是一个从小说《剑来》中提取结构化知识图谱的项目，包含人物、关系、物品、地点、事件等实体的自动化提取、合并、清洗和可视化展示。

## 项目概览

本项目通过 Gemini API 从 1200+ 章小说文本中提取结构化数据，构建完整的知识图谱，并提供 Web 和微信小程序两种前端展示方式。

**技术栈**: Python 3 (数据处理) + Gemini API (信息提取) + Taro (微信小程序)

## 核心架构

### 数据管道四阶段

```
1. 预处理 (Preprocess)
   章节文件 → 分段处理 → 上下文注入

2. 提取 (Extract)
   Gemini API → JSON 结构化数据 → 存储到 data/raw/

3. 清洗 (Clean)
   别名解析 → 实体合并 → 数据归一化 → 存储到 data/build/

4. 可视化 (Visualize)
   Web 应用 + 微信小程序
```

### 目录结构

```
.gitignore
AGENTS.md
CLAUDE.md
build_knowledge_base.py       # 核心: 知识库构建 (imports normalizers)
character_merger.py            # 库: 人物别名解析
cultivation_normalizer.py      # 库: 境界标准化
faction_normalizer.py          # 库: 势力标准化 (含白名单自动加载)
item_normalizer.py             # 库: 物品标准化
location_normalizer.py         # 库: 地点标准化
relation_normalizer.py         # 库: 关系类型标准化 (含反向关系翻转)
generate_top_characters.py     # 生产: Top20 人物生成
icon.jpg                       # 应用图标
chapters/                      # 1222 章原文
config/                        # Nginx 配置文件
data/
  ├── build/                   # 构建产物 (characters, items, factions, etc.)
  │   ├── faction_whitelist.json   # 权威势力白名单 (NotebookLM 校验)
  │   ├── faction_corrections.json # 重点人物势力修正 (210人)
  │   └── relation_type_map.json   # 权威关系类型映射 (400条精确+25条子串)
  ├── dist/                    # 前端使用的最终数据
  ├── raw/                     # 提取的原始 JSON 数据
  └── images/                  # 人物图片资源
docs/                          # 项目文档 (有索引 docs/README.md)
openspec/                      # 架构规范和变更提案
scripts/
  ├── review_ugc.py            # 生产: UGC 审核
  ├── build_frontend_data.py   # 生产: 前端数据打包 (含 quote_tags 合并)
  ├── build_graph_layout.py    # 生产: 关系图谱布局预计算
  ├── classify_quotes.py       # 生产: 金句情感分类 (Gemini 批量)
  ├── api_ugc.py               # 生产: UGC API
  ├── ugc_data/                # UGC 本地数据
  └── archive/                 # 45+ 已完成的一次性脚本
taro-app/                      # Taro 微信小程序 (gitignored)
```

## 常用命令

### 生产流程

```bash
# 构建知识库 (合并+标准化所有数据)
python build_knowledge_base.py

# 打包前端数据 (自动合并 quote_tags)
python scripts/build_frontend_data.py

# 生成 Top20 人物
python generate_top_characters.py

# 生成关系图谱布局 (依赖 dist/factions.json)
python scripts/build_graph_layout.py

# 金句情感分类 (幂等，跳过已分类)
python scripts/classify_quotes.py

# UGC 审核
python scripts/review_ugc.py
```

### 前端开发

```bash
# 微信小程序 (Taro)
cd taro-app
pnpm install
pnpm run build:weapp     # 构建微信小程序
```

### 已归档的脚本 (在 scripts/archive/)

```bash
# 数据提取 (已完成全部1218章): scripts/archive/extract_pipeline.py
# AI清洗 (已完成): scripts/archive/summarize_bio.py 等
# 图片生成 (已完成): scripts/archive/batch_generate_images.py 等
# 分析工具 (一次性): scripts/archive/check_rows.py 等
```

## 关键机制

### 1. 人物别名解析系统

**文件**: `character_merger.py` 中的 `CHARACTER_ALIASES` 字典

**规模**: 318 条别名映射（6 个分类）

**分类**:
1. 陈平安的化名/分身 (7条)
2. 落魄山/骊珠洞天核心成员 (~60条)
3. 剑气长城与蛮荒天下 (~15条)
4. 青冥天下与道门 (~10条)
5. 其他重要人物 (~20条)
6. AI清洗标识的别名 (~207条) — profiles_v3 内部name与原始提取名的映射

**机制**:
- 所有提取的人物名先通过 `get_canonical_name()` 解析为标准名
- `build_knowledge_base.py` 在合并阶段自动解析别名 + 修正关系引用
- **禁止链式别名**: 别名目标不能自身也是别名（如 `火蟒→陈暖树`，不能 `火蟒→暖树→陈暖树`）
- sync 到 profiles_v3 时通过 aliases 反查匹配（支持 raw name ≠ profile filename）

### 2. 双端点容错机制

**文件**: `scripts/archive/extract_pipeline.py`

**配置**:
```python
API_CONFIGS = [
    ("http://127.0.0.1:7861/v1", "gemini-3-pro-preview"),           # 主端点
    ("http://127.0.0.1:7861/antigravity/v1", "gemini-3-pro-low")   # 备用端点
]
```

**容错逻辑**:
- 遇到 429 (速率限制) → 自动切换端点
- 遇到超时/错误 → 自动重试备用端点
- 所有请求均有超时控制 (60-180秒)

### 3. 动态上下文注入

**机制**: 每次提取章节数据时，自动注入:
- 已识别的 400+ 主要人物名单
- 章节前后文线索
- 当前章节的特殊背景 (如时间跨度、主要事件)

**目的**: 提高 AI 对实体的识别准确率

### 4. 外貌提取四维度

**文件**: `openspec/changes/optimize-data-extraction/prompt_template.md` 模块4

**维度**:
1. **面相与精气神**: 五官、眼神、神态、年龄变化
2. **衣冠服饰细节**: 颜色、材质、款式、配饰
3. **关键器物与法宝**: 武器、法宝、随身物品
4. **气象与意境描述**: 气质、氛围、威压感

**原则**: 忠于原文、禁止编造、细节优先、动态追踪

### 5. 关系类型标准化系统

**文件**: `relation_normalizer.py` + `data/build/relation_type_map.json`

**规模**: 400 条精确映射 + 25 条子串兜底规则 → 12 个语义类别，边级覆盖率 94.9%

**机制**:
- 两层匹配: exact_map 精确匹配（拆 "/" 后逐原子查找）→ fallback_patterns 子串匹配
- 反向关系翻转: `get_reverse_types()` 将师徒→弟子、父子→子女等有方向性类型语义翻转
- 模块级自动加载 JSON（与 `faction_normalizer.py` 同模式）
- `build_graph_layout.py` 和 `generate_relations_graph.py` 均从此模块导入，不再硬编码

**12 个语义类别**: 情感、师徒、友谊、敌对、血亲、主从、同门、击杀、上下级、合作、敬畏、对抗 + 其他

## 核心数据结构

### JSON Schema (单章提取)

```json
{
  "characters": [
    {
      "name": "陈平安",
      "appearance": "早期皮肤黝黑消瘦，眼神沉稳...",
      "experience_description": "在本章的经历...",
      "aliases": ["草鞋少年", "陈先生"],
      "state_snapshot": {
        "realm": "止境武夫 + 飞升境剑修",
        "location": "剑气长城",
        "mental_state": "平静",
        "injuries": "无"
      }
    }
  ],
  "relations": [
    {
      "source": "陈平安",
      "target": "宁姚",
      "type": ["爱慕", "师徒情"],
      "正向强度": 10,
      "反向强度": 10,
      "evidence": "原文引用..."
    }
  ],
  "items": [],
  "locations": [],
  "factions": [],
  "quotes": [],
  "events": []
}
```

### 修真境界 & 领域知识

详见 `docs/domain.md`（人物、地点、核心概念、修真境界体系）。
境界标准化定义：`openspec/changes/optimize-data-extraction/prompt_template.md` 模块2。

### data/dist/ 产物清单

`build_frontend_data.py` 生成并维护以下前端数据文件:

| 文件 | 来源 | 消费者 |
|------|------|--------|
| `characters_lite.json` | profiles_v3/ 聚合 | 人物列表 (含 quotes/aliases 数组) |
| `characters_top.json` | 从 lite 提取 Top20 | 首页热门人物 + 每日金句 |
| `chars/*.json` | profiles_v3/ 完整复制 | 人物详情页 |
| `quotes.json` | 从 chars/ 聚合 + quote_tags 合并 | 语录库 (含情感标签) |
| `quotes_top.json` | 从 quotes.json 提取 Top50 | 首页金句快速加载 (含 tags) |
| `quote_tags.json` | classify_quotes.py 生成 | 金句标签持久化 (build/) |
| `factions.json` | build/ + 预计算 score/members | 势力页 |
| `locations.json` | build/ 直接复制 | 地点页 |
| `items.json` | build/ 直接复制 | 法宝图鉴(完整) |
| `items_lite.json` | build/ 直接复制 | 法宝列表(精简) |
| `items/*.json` | build/items/ 直接复制 | 法宝详情页 |
| `search_index.json` | build/ 直接复制 | 全局搜索 |
| `timeline.json` | build/ 直接复制 | 时间线 |
| `relations.json` | taro-app/src/data/ 复制 | 关系图谱 |

**热更新**: `review_ugc.py` 审核通过后自动上传上述全局文件 + 变更的个体文件至 CDN。curl 上传带 `--fail` 标志校验 HTTP 状态码。

## 开发工作流

### 完整数据处理流程

```bash
# 1. 构建知识库 (生成 build/ 下所有聚合文件)
python build_knowledge_base.py

# 2. 打包前端数据 (从 build/ → dist/，包括 characters_lite, quotes, factions, items, search_index, timeline 等)
python scripts/build_frontend_data.py

# 3. 生成首页 Top20 人物
python generate_top_characters.py

# 4. 金句分类 (首次或增量)
python scripts/classify_quotes.py

# 5. 前端查看结果
cd taro-app && pnpm run build:weapp
```

### 增量更新流程

如果只需重新提取部分章节:

1. 删除 `data/raw/` 中对应的 JSON 文件
2. 运行 `python scripts/archive/extract_pipeline.py` (会自动跳过已存在的文件)
3. 重新运行构建脚本

### 调试 AI 提取质量

1. 查看 `data/raw/` 中的 JSON 文件，检查提取结果
2. 如果发现问题，修改 `openspec/changes/optimize-data-extraction/prompt_template.md`
3. 删除对应章节的 JSON 文件，重新提取
4. 对比前后结果

## OpenSpec 变更管理

### 目录结构

```
/openspec/
  ├── project.md                      # 项目总览
  └── changes/
      ├── optimize-data-extraction/   # 数据提取优化提案
      │   ├── prompt_template.md     # AI 提示词模板
      │   └── tasks.md               # 任务清单
      └── implement-graph-f6/         # 图表可视化方案
```

### 创建新提案

```bash
mkdir openspec/changes/your-proposal-name/
touch openspec/changes/your-proposal-name/tasks.md
```

在 `tasks.md` 中记录:
- [ ] 待办任务
- [x] 已完成任务

## 重要约定

### 代码规范

- **Python**: 遵循 PEP 8，使用 snake_case
- **路径**: 所有脚本使用绝对路径 (避免 `cd` 导致的路径问题)
- **数据语言**: 所有提取的数据必须是中文 (人名、对话、描述等)

### 文件命名

- 章节文件: `chapters/第X章 标题.txt`
- 提取结果: `data/raw/XXX_第X章 标题.json` (XXX 为三位数序号)
- 处理结果: `data/build/characters.json`

### Git 工作流

当前分支: `main`

**提交规范**:
- 数据提取相关: `feat: extract chapters 001-050`
- 脚本优化: `refactor: optimize character merging logic`
- 前端开发: `feat(frontend): add character detail page`

## 本地环境

- **操作系统**: macOS (Darwin 25.2.0)
- **本地 LLM**: 运行在 `http://127.0.0.1:7861` (Gemini API 兼容接口)
- **Python 版本**: Python 3.x
- **Node.js**: 用于前端开发

## 前端应用

### 微信小程序 (taro-app/)

- **技术**: Taro 3.x
- **构建命令**: `pnpm run build:weapp`
- **开发工具**: 微信开发者工具
- **页面数**: 18 个页面 + 4 Tab 底部导航（首页/关系图谱/地图/时间线）

**已完成功能**（详见 `docs/taro_features.md`）：
- SEO 动态标题、人物/金句卡片分享
- 法宝/势力卡片生成器 (`itemCardGenerator.ts`, `factionCardGenerator.ts`)
- 人物 VS 对比页 (`pages/compare/`) + 专属底图对比卡片 (7维度: 修为/势力/功法/语录/关系/共同关系人/金句)
- 金句情感标签筛选 (6 类: 励志/感伤/豪气/幽默/哲理/温情)
- 全页面分享 (含 Tab 页 graph/timeline/map)
- 数据埋点 (`utils/analytics.ts`, 6 个事件)
- 首页金句渐入动效

## 故障排查 & 数据质量

详见 `docs/troubleshooting.md`（提取失败、合并错误、前端加载、数据质量检查点）。

## Design Context

### Users

剑来小说的忠实读者（书粉），使用场景是查阅人物关系、重温经典语录、理清复杂剧情线索。核心需求是"快速找到想看的内容"，而非沉浸式阅读体验。

### Brand Personality

**雅致 · 清透 · 留白**

像翻开一幅卷轴——不是金碧辉煌的宫廷画，而是文人书房中淡墨山水的气质。产品应让人感到安静、舒适、有文化底蕴，而非花哨或游戏化。

**参考方向**: 传统文化类 App（如故宫博物院、国家博物馆），强调文化质感而非信息密度。

### Aesthetic Direction

**水墨画意境 (Ink & Wash)**

- 大量留白，内容之间充分呼吸
- 色彩克制，以墨色层次为主，点缀色极少量使用
- 圆角卡片 + 极轻阴影，不争夺注意力
- 宋体/衬线体用于标题和文化感文字，系统字体用于功能性文本
- 动效应该是"墨在宣纸上晕开"的感觉——缓慢、自然、不突兀

### Design Principles

1. **留白即设计**: 宁可空着也不要塞满。间距宁大勿小，信息密度宁低勿高。
2. **墨分五色**: 用灰度层次（焦/浓/重/淡/清）建立视觉层级，而不是靠多种颜色区分。
3. **克制点缀**: 点缀色（朱砂红、靛青蓝、竹青绿、赭石黄）仅用于语义化场景（强调/链接/成功/警告），绝不大面积铺陈。
4. **内容至上**: UI 是画框，不是画本身。让小说内容（人物、语录、关系）成为视觉焦点。
5. **触感温润**: 交互反馈柔和（轻按缩放、渐入渐出），避免弹跳、闪烁等激烈动效。

### Design Tokens (Taro 小程序)

**定义文件**: `taro-app/src/styles/theme.scss`

**色彩**:
| Token | 值 | 用途 |
|-------|------|------|
| `$ink-dark` | #1a1a1a | 焦墨 - 标题、强调 |
| `$ink-main` | #333333 | 浓墨 - 正文 |
| `$ink-medium` | #666666 | 重墨 - 次要信息 |
| `$ink-light` | #999999 | 淡墨 - 辅助信息 |
| `$ink-faint` | #e0e0e0 | 清墨 - 分割线、边框 |
| `$paper-white` | #f7f6f2 | 宣纸白 - 页面背景 |
| `$paper-light` | #ffffff | 纯白 - 卡片背景 |
| `$cinnabar` | #b03a2e | 朱砂 - 印章、高亮、错误 |
| `$indigo` | #485a6c | 靛青 - 链接、品牌色 |
| `$bamboo` | #5d7a5d | 竹青 - 成功、特定标签 |
| `$ochre` | #b8860b | 赭石 - 警告、法宝 |

**注意**: taro-app/src/ 中已无 `#3b82f6` 硬编码（已统一为 `$indigo`）。

**字体**:
- 标题/文化感: `"Songti SC", serif` (宋体)
- 正文/功能性: `"PingFang SC", "Hiragino Sans GB", serif` (系统字体)

**间距**: 8px 步进 (8/16/24/32/48/64px Taro 单位)

**圆角**: sm=8px, md=24px, lg=32px, round=999px

**阴影**: 极轻 (opacity 0.04~0.08)，水墨风不依赖阴影建立层次

### 前端说明

- `frontend/` 已删除（旧版 React+Vite Web 应用，不再使用）
- **唯一活跃前端为 `taro-app/`**（Taro 微信小程序）
- 无障碍: 不做特别要求，优先视觉体验

---

**最后更新**: 2026-03-24
**项目路径**: `/Users/shushu/剑来`
