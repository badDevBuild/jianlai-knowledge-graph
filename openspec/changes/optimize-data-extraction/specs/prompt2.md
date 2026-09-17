你的直觉非常敏锐。之前的Prompt设计确实更像是一个“静态数据库填空”，而忽略了小说提取中最困难的**“指代消解”（Entity Resolution）**和**“剧情连续性”**。

你提出的三个痛点非常关键：
1.  **世界观没用在刀刃上**：单纯给名词解释不够，要告诉LLM这些设定如何影响人物判断。
2.  **动态上下文太窄**：不能只看主角属性，要看“天下大势”和“未解悬疑”。
3.  **通用称呼（指代消解）灾难**：这是知识图谱构建最大的脏数据来源。不能把“那个老人”当成一个新角色。

基于此，我重构了方案。这次的核心逻辑是：**“基于推理的提取” (Inference-based Extraction)** 而非简单的“基于匹配的提取”。

我们将引入一个**“未决实体缓冲区”（Pending Buffer）**的概念来解决第3点。

---

### 优化后的 Prompt 架构设计

#### 1. 系统指令与世界观逻辑 (System Prompt)
这里不再堆砌名词解释，而是转化为**推理逻辑**，帮助LLM理解上下文。

```markdown
# Role
你是一名《剑来》小说的**剧情逻辑分析师**与**知识图谱架构师**。你的核心能力不仅仅是提取信息，更是**还原剧情逻辑**和**消解指代歧义**。

# Knowledge & Inference Rules (世界观推理逻辑)
你必须基于以下《剑来》特有的逻辑来理解文本，而非仅作为名词参考：

1.  **战力与身份的映射逻辑**:
    *   若文中出现“缩地成寸”、“御风远游”，此人必为上五境（或武夫远游境）。
    *   若出现“本命瓷”、“碎裂”，特指骊珠洞天相关剧情。
    *   若某人能听到他人的“心声”，此人境界必高于对方，或拥有特殊法宝。
    *   **判断辅助**: 当遇到陌生角色时，利用上述逻辑推断其可能的身份范围。

2.  **人情世故与因果逻辑**:
    *   《剑来》中“欠债”是核心驱动力。金钱交易往往伴随着因果纠缠。
    *   注意“香火情”一词，它既是神灵的食粮，也是人情往来的代称。

3.  **指代消解逻辑 (核心任务)**:
    *   **严禁**将“青衫客”、“老道人”、“白衣女子”、“那少年”直接作为 `character.name` 输出。
    *   **Step 1**: 尝试根据上下文（Context）和输入中的【已知角色列表】进行匹配。例如：看到“青衫背剑”，且当前场景有陈平安，应归一化为“陈平安”。
    *   **Step 2**: 能够推断出身份但文中未点破（如“绣虎”即“崔瀺”），直接输出真名，并在 `aliases` 中记录代称。
    *   **Step 3**: **如果完全无法确定身份**，请将其放入 `unidentified_figures` 模块，不要放入 `characters`，以便后续人工清洗或回溯。
```

#### 2. 动态上下文输入 (Dynamic Context Input)
这里不再只是主角状态，而是输入**“世界状态”**和**“未决悬疑”**。

```markdown
# Dynamic Context (故事当前状态)
在阅读本章前，请知晓以下信息：

1.  **Global Events (天下大势)**:
    *   当前时间锚点：{{CURRENT_ERA}} (如：剑气长城守卫战期间)
    *   正在发生的重大事件：{{ACTIVE_EVENTS}} (如：正阳山问剑大典正在进行中)
    
2.  **Active Characters (在场/活跃人物)**:
    *   上一章结尾在场人物：{{CHARACTERS_ON_SCENE}} (如：陈平安, 刘羡阳, 搬山猿)
    *   *提示：若文中出现“那人”、“他”，大概率指代上述人物之一。*

3.  **Pending Mysteries (未解悬疑)**:
    *   此前章节出现的未确认身份者：{{UNKNOWN_ENTITIES_BUFFER}}
    *   *任务：如果本章揭示了这些人的真实身份，请在 `clues.identity_reveal` 中明确标注。*
```

#### 3. 提取任务与 JSON 结构 (Task & Output)

```markdown
# Task
请分析章节文本 {{CHAPTER_TEXT}}。
输出符合以下定义的 JSON 数据。

# Output JSON Structure Definition
{
  "meta": {
    "chapter_id": 123,
    "chapter_title": "...",
    "world_timestamp": {
       "season": "...", 
       "year_inference": "..." // 尝试推断年份
    }
  },

  // 1. 剧情大事件更新 (世界状态)
  "world_events": [ 
    {
      "name": "...", 
      "status": "Ongoing", // New, Ongoing, Ended
      "impact_scope": "Sect", // World, Continent, Dynasty, Sect, Individual
      "description": "正阳山护山大阵被破，宗门气运流失"
    }
  ],

  // 2. 角色提取 (仅确认识别的人物)
  "characters": [
    {
      "name": "陈平安", // 必须是标准真名
      "is_new_appearance": false, // 是否本章首次登场
      "role_in_chapter": "Protagonist", 
      "state_update": {
        "realm": "...", 
        "current_location": "...",
        "mental_state": "..."
      },
      "economics": [ // 经济活动挂在人物下
        { "action": "Spend", "item": "谷雨钱", "amount": 1, "target": "..." }
      ]
    }
  ],

  // 3. 未决人物 (无法识别的通用称呼) -> 供后续回溯
  "unidentified_figures": [
    {
      "reference_text": "那个戴斗笠的汉子", // 原文称呼
      "appearance_features": ["身材高大", "背刀"], // 特征
      "action_summary": "出手拦住了陈平安的飞剑",
      "suspected_identity": "阿良?" // 模型若有猜测可填，否则null
    }
  ],

  // 4. 势力动态 (独立字段)
  "factions": [
    {
      "name": "正阳山",
      "type": "Sect",
      "status_change": {
        "reputation": "Decline", // 声望下跌
        "formation": "Broken" // 护山大阵破碎
      }
    }
  ],

  // 5. 关系与因果
  "relations": [
    {
      "source": "陈平安",
      "target": "搬山猿",
      "type": "Hostility",
      "delta": -10, // 负数代表恶化
      "is_debt": true, // 是否涉及因果/债务
      "context": "..."
    }
  ],
  
  // 6. 伏笔与填坑 (处理悬疑)
  "plot_links": [
    {
      "type": "IdentityReveal", // 身份揭秘
      "content": "本章确认‘那个戴斗笠的汉子’就是阿良",
      "related_entity": "阿良"
    },
    {
      "type": "Foreshadowing", // 埋下伏笔
      "content": "崔东山留下了一颗棋子在棋盘外",
      "inference": "..."
    }
  ]
}
```

---

### 对你的疑问的深度回应与策略

#### 1. 关于“世界观是否有效”
在旧版中，世界观确实只是个“字典”。在新版 Prompt 中，我通过 **`Knowledge & Inference Rules`** 强制LLM进行推理。
*   **举例**：如果文本写“中年儒士言出法随，定住了飞剑”。
*   **旧版**：可能只提取一个“中年儒士”。
*   **新版**：因为规则里写了“儒家+言出法随”，LLM会推断此人大概率是“书院君子或圣人”，如果上下文里有“君倩”，它会尝试匹配；如果匹配不上，它会放入 `unidentified_figures` 并标注“疑似儒家圣人”，这比单纯提取一个“人”要有价值得多。

#### 2. 关于“动态上下文”
你说的对，上下文不应局限于某个人。新版增加了 **`Global Events`** 和 **`Active Characters`**。
*   **应用场景**：比如现在是“文庙议事”期间。如果你告诉LLM这个背景，当文中出现“那个老人”在主位讲话时，LLM就能大概率推断出这可能是“文圣”或者“礼圣”，而不是路人甲。

#### 3. 关于“通用称呼”的处理流程 (Human-in-the-loop)
这是工程落地的关键。**大模型不是万能的，必须结合代码逻辑。**

**建议的处理流程（回溯机制）：**

1.  **提取阶段**：
    *   Prompt 明确要求：确定的放 `characters`，不确定的放 `unidentified_figures`。
    *   `unidentified_figures` 记录了：`{"chapter": 100, "ref": "白衣人", "feature": "拿酒壶"}`。

2.  **存储阶段**：
    *   将 `unidentified_figures` 存入一个独立的数据库表 `PendingEntities`。

3.  **更新/回溯阶段 (Python代码逻辑)**：
    *   当读取到第105章，Prompt 输出 `plot_links`: `{"type": "IdentityReveal", "content": "白衣人是崔东山"}`。
    *   **触发回溯脚本**：程序自动去 `PendingEntities` 表里查找第100章左右、特征匹配“白衣/酒壶”的记录。
    *   **自动修正**：将第100章的 `unidentified_figures` 替换为 `characters: [{"name": "崔东山"}]`。

通过这种 **"Prompt 区分确信度" + "代码处理回溯"** 的方式，才能真正解决《剑来》这种伏笔千里、人物众多的小说的提取问题。