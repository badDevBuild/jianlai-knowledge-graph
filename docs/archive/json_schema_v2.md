# 《剑来》知识图谱 JSON Schema V2.0

## 概述

本文档定义了从《剑来》小说中逐章提取知识图谱数据的 JSON 结构规范。

**设计原则**：
1. **原子性**：单章提取的数据应自包含，聚合逻辑由后处理完成
2. **结构化**：关键字段使用枚举值，便于后续聚合与分析
3. **可追溯**：支持伏笔追踪、身份回溯等跨章节关联
4. **世界观适配**：字段设计贴合《剑来》的修行体系、经济系统、地理架构

---

## 完整 JSON 结构概览

```json
{
  "meta": {},
  "characters": [],
  "relations": [],
  "events": [],
  "economics": [],
  "plot_links": [],
  "items": [],
  "locations": [],
  "factions": [],
  "quotes": []
}
```

**字段说明**：
| 序号 | 字段 | 说明 |
|------|------|------|
| 1 | meta | 章节元信息 |
| 2 | characters | 人物 |
| 3 | relations | 人物关系 |
| 4 | events | 事件（通过 scope 区分宏观/中观/微观） |
| 5 | economics | 经济活动 |
| 6 | plot_links | 伏笔与回调 |
| 7 | items | 物品 |
| 8 | locations | 地点 |
| 9 | factions | 势力 |
| 10 | quotes | 金句 |

---

## 1. `meta` - 章节元信息

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| chapter_id | Integer | 是 | 章节序号 |
| chapter_title | String | 是 | 章节标题 |

**示例**：
```json
{
  "meta": {
    "chapter_id": 1,
    "chapter_title": "第1章 惊蛰"
  }
}
```

---

## 2. `characters` - 人物

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | String | 是 | 人物名称（真名或特定称呼，不可使用通用称呼，如“少年”、“少女”等） |
| is_identified | Boolean | 是 | 是否确认真实身份。`true`=确认真名，`false`=无法确认 |
| aliases | Array[String] | 否 | 本章出现的别名/称呼 |
| bio | String | 否 | 简短身份介绍 |
| appearance | Object | 否 | 外貌描写 |
| cultivation | Object | 否 | 修为境界 |
| techniques | Array[Object] | 否 | 功法/武学 |
| faction | String | 否 | 所属势力 |
| tags | Array[String] | 否 | 标签 |
| chapter_experience | String | 否 | 本章经历概述 |
| state_snapshots | Array[Object] | 否 | 状态快照数组（人物状态可能变化） |
| unidentified_info | Object | 条件必填 | 当 `is_identified=false` 时必填 |

### 2.1 `appearance` - 外貌描写

提取原文中对人物**视觉方面**和**气质方面**的描写。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| facial | String | 否 | **面部特征**：五官、肤色、表情、眼神。如"眉心朱砂痣"、"双鬓微白"、"眼神凌厉" |
| physique | String | 否 | **体型体态**：身材、肌肉、姿态。如"身形单薄"、"身材高大魁梧"、"佝偻老者" |
| attire | String | 否 | **衣着装扮**：服饰、配饰、兵器。如"青衫背剑"、"白袍飘飘"、"头戴斗笠" |
| aura | String | 否 | **气质气场**：整体感觉、威压。如"杀气凛然"、"仙风道骨"、"返璞归真" |

**提取原则**：
- 只提取原文明确描述的内容，无描述则留空
- 区分具体描写（facial/physique/attire）与抽象感受（aura）
- 独特标识性特征优先提取（如"眉心朱砂痣"、"左手六指"）

### 2.2 `cultivation` - 修为境界

《剑来》修行体系分为**纯粹武夫**（向内求）与**炼气士**（向外求）两条道路。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| path | String | 否 | 修行道路（见枚举） |
| realm | String | 否 | 境界层级：如"二境"、"十一境" |
| realm_name | String | 否 | 境界名称（见境界表） |
| stage | String | 否 | 细分阶段：如止境的"气盛/归真/神到" |

#### `path` 枚举值
- 纯粹武夫
- 炼气士
- 剑修
- 纯粹剑修
- 儒家
- 佛家
- 道家
- 妖族
- 鬼修
- 神灵
- 凡人
- 其他

#### 纯粹武夫境界表（十一境）

| 境界 | 名称 | 层级 | 
|------|------|------|
| 一境 | 泥胚境 | 下三境（炼体） | 
| 二境 | 木胎境 | 下三境（炼体） | 
| 三境 | 水银境 | 下三境（炼体） | 
| 四境 | 英魂境 | 中三境（炼气） | 
| 五境 | 雄魄境 | 中三境（炼气） | 
| 六境 | 武胆境 | 中三境（炼气） | 
| 七境 | 金身境 | 上三境（炼神） | 
| 八境 | 羽化境 | 上三境（炼神） | 
| 九境 | 山巅境 | 上三境（炼神） | 
| 十境 | 止境 | 巅峰，细分：气盛/归真/神到 | 
| 十一境 | 武神境 | 传说 | 

#### 炼气士境界表（十五境）

| 境界 | 名称 | 层级 |
|------|------|------|
| 一境 | 铜皮境 | 下五境（筑基） | 
| 二境 | 草根境 | 下五境（筑基） | 
| 三境 | 柳筋境 | 下五境（筑基） | 
| 四境 | 骨气境 | 下五境（筑基） | 
| 五境 | 铸庐境 | 下五境（筑基） | 
| 六境 | 洞府境 | 中五境（神仙） | 
| 七境 | 观海境 | 中五境（神仙） | 
| 八境 | 龙门境 | 中五境（神仙） | 
| 十境 | 元婴境 | 中五境（神仙） | 
| 十一境 | 玉璞境 | 上五境 | 
| 十二境 | 仙人境 | 上五境 | 
| 十三境 | 飞升境 | 上五境 | 
| 十四境 | 合道境 | 上五境 | 
| 十五境 | 仙君境 | 上五境 | 

### 2.3 `techniques` - 功法/武学

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | String | 是 | 功法/武学名称 |
| type | String | 是 | 类型（见枚举） |
| category | String | 否 | 细分类别（见枚举） |
| relation | String | 是 | 人物与功法的关系（见枚举） |
| description | String | 否 | 简要描述 |

#### `type` 枚举值
- 武学
- 剑术
- 雷法
- 水法
- 符箓
- 阵法
- 身法
- 炼体功法
- 秘术
- 其他

#### `category` 枚举值
- 拳法
- 掌法
- 腿法
- 步法
- 桩功
- 剑招
- 剑诀
- 刀法
- 符咒
- 口诀
- 其他

#### `relation` 枚举值

| 值 | 说明 |
|------|------|
| 学习 | 本章首次习得该功法 |
| 练习 | 日常修炼该功法 |
| 使用 | 在战斗或特定场景中施展 |
| 教授 | 向他人传授该功法 |
| 领悟 | 有所感悟或突破 |
| 创造 | 自创该功法 |
| 提及 | 仅在对话或描述中提及，未实际施展 |

#### 常见功法参考

**武学类**：
- 撼山拳（走桩、立桩/剑炉、睡桩/千秋、天地桩）
- 神人擂鼓式、云蒸大泽式、铁骑凿阵式
- 猿形、惊蛰（朱敛自创）
- 撞心关（崔公壮绝学）
- 校大龙（正脊骨法门）

**剑术类**：
- 剑气十八停（运气法门）
- 剑术正经（雪崩式、镇神头、山岳式、披甲式）
- 指剑术（裴旻所创）
- 梦游剑术（刘羡阳家传）
- 白猿背剑术、拖刀式
- 大工斩玉（韩槐子成名剑术）
- 片月、湍流（陈平安自创）

**炼气士功法**：
- 五雷正法（龙虎山不传之秘）
- 云上琅琅书、上上玄玄集（雷法秘典）
- 祈雨碑道诀（水法）
- 云水身、水精境界
- 丹书真迹（符箓）
- 缝衣术、分道散躯、恣意化形（秘术）

### 2.4 `state_snapshots` - 状态快照

人物在本章中的状态可能发生变化，因此使用数组记录多个状态。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| location | String | 否 | 当前位置 |
| injuries | String | 否 | 伤势 |
| description | String | 否 | 状态描述 |

### 2.5 `unidentified_info` - 未识别人物信息

当 `is_identified=false` 时必填。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| reference_text | String | 是 | 原文中的称呼，如"锦衣少年"、"白衣剑修" |
| appearance_features | Array[String] | 否 | 外貌特征列表 |
| suspected_identity | String | 否 | LLM推测的真实身份（可为null） |
| confidence | Float | 否 | 推测置信度（0-1） |

### 人物完整示例

```json
{
  "characters": [
    {
      "name": "陈平安",
      "is_identified": true,
      "aliases": ["少年", "泥瓶巷少年", "草鞋少年"],
      "bio": "居住在泥瓶巷的孤儿，父母早逝，曾是龙窑学徒。",
      "appearance": {
        "facial": "眼神清澈，面容清瘦",
        "physique": "身形单薄，肌肉紧实",
        "attire": "草鞋布衣",
        "aura": "气质坚韧，目光沉稳"
      },
      "cultivation": {
        "path": "纯粹武夫",
        "realm": "二境",
        "realm_name": "草根",
        "stage": ""
      },
      "techniques": [
        {
          "name": "撼山拳·走桩",
          "type": "武学",
          "category": "桩功",
          "relation": "练习",
          "description": "撼山拳基础桩功，需练习百万次"
        }
      ],
      "faction": "",
      "tags": ["孤儿", "窑匠"],
      "chapter_experience": "被苻南华轻视，错失与仙家结交的机缘。",
      "state_snapshots": [
        {
          "location": "泥瓶巷",
          "injuries": "无",
          "description": "在家中生活"
        }
      ]
    },
    {
      "name": "锦衣少年",
      "is_identified": false,
      "aliases": [],
      "bio": "外乡来的富家少年，出手阔绰。",
      "appearance": {
        "facial": "",
        "physique": "",
        "attire": "锦衣华服",
        "aura": "气度不凡"
      },
      "cultivation": {
        "path": "",
        "realm": "",
        "realm_name": "",
        "stage": "",
        "visual_traits": ""
      },
      "techniques": [],
      "faction": "",
      "tags": ["外乡人", "富贵"],
      "chapter_experience": "夜间来到泥瓶巷，买走金色鲤鱼，赠予陈平安金钱。",
      "state_snapshots": [
        {
          "location": "泥瓶巷",
          "injuries": "",
          "description": ""
        }
      ],
      "unidentified_info": {
        "reference_text": "锦衣少年",
        "appearance_features": ["锦衣华服", "出手阔绰", "有随从老者"],
        "suspected_identity": null,
        "confidence": 0.0
      }
    }
  ]
}
```

---

## 3. `relations` - 人物关系

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| source | String | 是 | 关系发起方 |
| target | String | 是 | 关系接收方 |
| type | Array[String] | 是 | 关系类型（见枚举，可多选） |
| positive_delta | Integer | 否 | 正面关系变化，正数表示增强 |
| negative_delta | Integer | 否 | 负面关系变化，正数表示增强 |
| evidence | String | 否 | 原文证据 |

### `type` 枚举值（按类别分组）

#### 血缘/家族关系
| 值 | 说明 |
|------|------|
| 父母 | 父母与子女 |
| 子女 | 子女与父母 |
| 兄弟姐妹 | 同辈血亲 |
| 祖孙 | 隔代血亲 |
| 宗族 | 同宗同族 |

#### 师承/传道关系
| 值 | 说明 |
|------|------|
| 师徒 | 正式的师徒关系 |
| 同门 | 同一师门 |
| 传道 | 非正式的指点、传授（亦师亦友） |
| 再传 | 徒孙与师祖的关系 |

#### 情感/羁绊关系
| 值 | 说明 |
|------|------|
| 道侣 | 修行伴侣、爱人 |
| 挚友 | 至交好友 |
| 故交 | 旧识、老朋友 |
| 恩人 | 有恩于己 |
| 仇人 | 有仇于己 |

#### 社会/从属关系
| 值 | 说明 |
|------|------|
| 主仆 | 主人与仆从 |
| 同僚 | 同事、同一势力 |
| 邻居 | 邻里关系 |
| 上下级 | 上司与下属 |

#### 利益/博弈关系
| 值 | 说明 |
|------|------|
| 盟友 | 合作关系 |
| 敌对 | 敌人、对立 |
| 劲敌 | 势均力敌的对手，可能惺惺相惜 |
| 交易 | 买卖、交换关系 |
| 因果 | 涉及因果/债务/香火情 |

#### 特殊关系
| 值 | 说明 |
|------|------|
| 护道 | 为他人保驾护航 |
| 供奉 | 记名供奉、护卫 |
| 宿敌 | 命运纠缠的长期对手 |
| 其他 | 其他关系 |

### 关系示例

```json
{
  "relations": [
    {
      "source": "陈平安",
      "target": "宁姚",
      "type": ["道侣"],
      "positive_delta": 5,
      "negative_delta": 0,
      "evidence": "陈平安望向宁姚的眼神温柔"
    },
    {
      "source": "崔诚",
      "target": "陈平安",
      "type": ["传道"],
      "positive_delta": 3,
      "negative_delta": 0,
      "evidence": "崔诚向陈平安传授神人擂鼓式等拳法"
    },
    {
      "source": "陈平安",
      "target": "曹慈",
      "type": ["劲敌"],
      "positive_delta": 1,
      "negative_delta": 0,
      "evidence": "两人多次问拳，惺惺相惜"
    }
  ]
}
```

---

## 4. `events` - 事件

统一记录章节内发生的所有事件，通过 `scope` 字段区分事件层级（宏观大事件 vs 章节小事件）。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | String | 是 | 事件名称 |
| type | String | 否 | 事件类型（见枚举） |
| scope | String | 是 | 事件层级（见枚举） |
| status | String | 否 | 状态（见枚举），宏观事件建议填写 |
| location | Object | 否 | 地理层级 |
| participants | Array[Object] | 否 | 参与者及角色 |
| causality | Object | 否 | 因果/溯源链（宏观事件适用） |
| systemic_change | Object | 否 | 规矩/法则演化（宏观事件适用） |
| consequences | String | 否 | 直接后果/影响 |
| power_system_tags | Array[String] | 否 | 修行流派标签（见枚举） |
| resource_tags | Array[String] | 否 | 资源与气运标签（见枚举） |
| is_foreshadowing | Boolean | 否 | 是否为伏笔 |
| description | String | 否 | 详细描述 |

### 4.1 `type` - 事件类型枚举

| 值 | 说明 |
|------|------|
| 战斗 | 打斗、问剑、问拳 |
| 对话 | 重要对话 |
| 修炼 | 修行、练功 |
| 突破 | 境界突破 |
| 旅行 | 行程、游历 |
| 日常 | 日常生活 |
| 回忆 | 回忆往事 |
| 剧情 | 剧情推进 |
| 政治 | 王朝/宗门政策变动 |
| 天灾 | 自然灾害、天象异变 |
| 战争 | 大规模冲突 |
| 其他 | 其他类型 |

### 4.2 `scope` - 事件层级枚举

| 值 | 说明 | 示例 |
|------|------|------|
| 宏观 | 跨天下/跨大陆的重大事件 | 剑气长城守卫战、蛮荒入侵 |
| 中观 | 王朝/宗门级别的事件 | 官窑关闭、正阳山问剑大典 |
| 微观 | 章节内的具体事件 | 泥瓶巷探查、锦衣少年夜访 |

### 4.3 `status` - 状态枚举

| 值 | 说明 |
|------|------|
| 新发生 | 本章首次发生 |
| 进行中 | 持续进行 |
| 已结束 | 已经结束 |
| 关键转折 | 出现重大转折 |
| 暂时搁置 | 暂时中断 |

### 4.4 `location` - 地理层级

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| world | String | 否 | 所属天下（见枚举） |
| continent | String | 否 | 大陆/洲 |
| region | String | 否 | 区域（王朝/洞天福地） |
| specific_site | String | 否 | 具体地点 |

#### `world` 枚举值
- 浩然天下
- 蛮荒天下
- 青冥天下
- 西方佛国
- 五彩天下

### 4.5 `participants` - 参与者

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | String | 是 | 参与者名称 |
| role | String | 是 | 角色（见枚举） |

#### `role` 枚举值
- 发起者
- 决策者
- 执行者
- 受影响者
- 旁观者
- 阻止者
- 受益者
- 受害者

### 4.6 `causality` - 因果/溯源链

适用于中观/宏观事件，记录事件的因果脉络。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| root_cause | String | 否 | 根本原因（远古因果、规矩背景） |
| direct_trigger | String | 否 | 直接诱因 |
| related_events | Array[String] | 否 | 关联事件名称 |

### 4.7 `systemic_change` - 规矩/法则演化

适用于中观/宏观事件，记录事件对世界规则的影响。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| rule_affected | String | 否 | 受影响的规矩/法则 |
| luck_transfer | String | 否 | 气运流转变化 |

### 4.8 标签枚举

#### `power_system_tags` - 修行流派标签
- 纯粹武夫
- 炼气士
- 剑修
- 儒家
- 佛家
- 道家
- 兵家
- 墨家
- 妖族
- 鬼修
- 神灵
- 其他

#### `resource_tags` - 资源与气运标签
- 气运
- 功德
- 香火
- 神仙钱
- 本命瓷
- 飞剑
- 山头
- 大渎
- 其他

### 事件示例

```json
{
  "events": [
    {
      "name": "官窑关闭",
      "type": "政治",
      "scope": "中观",
      "status": "已发生",
      "location": {
        "world": "浩然天下",
        "continent": "宝瓶洲",
        "region": "骊珠洞天",
        "specific_site": "小镇"
      },
      "participants": [
        {"name": "陈平安", "role": "受影响者"},
        {"name": "大骊宋氏", "role": "决策者"}
      ],
      "causality": {
        "root_cause": "万年契约期满，真龙遗蜕气运释放，洞天即将落地",
        "direct_trigger": "大骊朝廷勒令关闭",
        "related_events": []
      },
      "systemic_change": {
        "rule_affected": "本命瓷体系终结",
        "luck_transfer": "个人气运回归个体，不再受外部掌控"
      },
      "consequences": "数十座窑炉关闭，匠人失业，小镇从封闭转向开放",
      "power_system_tags": [],
      "resource_tags": ["气运", "本命瓷"],
      "is_foreshadowing": false,
      "description": "小镇失去官窑造办资格，标志着大骊开始正式接管并改变此地规则。"
    },
    {
      "name": "泥瓶巷探查",
      "type": "剧情",
      "scope": "微观",
      "status": "已结束",
      "location": {
        "world": "浩然天下",
        "continent": "宝瓶洲",
        "region": "骊珠洞天",
        "specific_site": "泥瓶巷"
      },
      "participants": [
        {"name": "苻南华", "role": "发起者"},
        {"name": "蔡金简", "role": "执行者"},
        {"name": "陈平安", "role": "受影响者"},
        {"name": "宋集薪", "role": "受益者"}
      ],
      "causality": null,
      "systemic_change": null,
      "consequences": "陈平安错失与仙家结交的机缘",
      "power_system_tags": ["炼气士"],
      "resource_tags": [],
      "is_foreshadowing": false,
      "description": "苻南华与蔡金简结盟进入泥瓶巷寻找机缘对象。"
    },
    {
      "name": "锦衣少年夜访",
      "type": "剧情",
      "scope": "微观",
      "status": "已结束",
      "location": {
        "world": "浩然天下",
        "continent": "宝瓶洲",
        "region": "骊珠洞天",
        "specific_site": "泥瓶巷"
      },
      "participants": [
        {"name": "锦衣少年", "role": "发起者"},
        {"name": "陈平安", "role": "受益者"},
        {"name": "宋集薪", "role": "旁观者"}
      ],
      "causality": null,
      "systemic_change": null,
      "consequences": "陈平安获得一袋金钱",
      "power_system_tags": [],
      "resource_tags": [],
      "is_foreshadowing": true,
      "description": "锦衣少年夜间来到泥瓶巷，赠予陈平安金钱作为买走鲤鱼的酬谢。"
    }
  ]
}
```

---

## 5. `economics` - 经济活动

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| actor | String | 是 | 行为主体 |
| target | String | 否 | 对象（交易对方/受益方） |
| action | String | 是 | 行为类型（见枚举） |
| item | String | 是 | 物品/资产名称 |
| amount | Number | 否 | 数量 |
| currency | Object | 否 | 货币信息 |
| asset_category | String | 否 | 资产性质（见枚举） |
| terms | Object | 否 | 契约条款（适用于借贷/投资） |
| social_capital_impact | String | 否 | 人情/因果影响 |
| context | String | 否 | 上下文说明 |

### 5.1 `currency` - 货币信息

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| type | String | 是 | 货币类型（见枚举） |
| level | String | 是 | 货币位阶：凡俗、仙家 |
| quantity | Number | 否 | 货币数量 |

#### 货币类型枚举

**凡俗货币**：
- 铜钱
- 银两
- 金锭

**仙家货币（神仙钱三级体系）**：
| 类型 | 兑换比例 | 说明 |
|------|----------|------|
| 雪花钱 | 基础单位 | 最小单位 |
| 小暑钱 | 1:100雪花钱 | 中等单位 |
| 谷雨钱 | 1:10000雪花钱 | 大额单位 |

**特殊货币**：
| 类型 | 说明 |
|------|------|
| 金精铜钱 | 蕴含气运，有价无市 |
| 压胜钱 | 金精铜钱一种，用于压制气运 |
| 供养钱 | 金精铜钱一种，用于供奉 |
| 迎春钱 | 金精铜钱一种，用于迎接气运 |

### 5.2 `asset_category` - 资产性质枚举

| 值 | 说明 |
|------|------|
| 实物 | 具体物品（兵器、丹药、法宝等） |
| 货币 | 钱财本身 |
| 地产 | 山头、店铺、渡口等不动产 |
| 权益 | 经营权、收益权、名额等 |
| 气运 | 气运、功德、香火等无形资产 |
| 信息 | 情报、秘闻、道法传承等 |

### 5.3 `terms` - 契约条款

适用于借贷/投资/长期合作。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| interest_rate | String | 否 | 利息（如"3%"、"年息三分"） |
| settlement_period | String | 否 | 结算周期（如"每年"、"三年"） |
| repayment_condition | String | 否 | 偿还条件 |
| collateral | String | 否 | 抵押物 |

### 5.4 `action` - 行为类型枚举

| 值 | 说明 |
|------|------|
| 购买 | 以货币换取物品/资产 |
| 出售 | 出售物品/资产换取货币 |
| 赠予 | 无偿给予 |
| 交易 | 以物易物 |
| 借贷 | 借入或借出（涉及利息） |
| 偿还 | 归还借贷 |
| 投资 | 注资参与项目 |
| 分红 | 获得投资收益 |
| 失去 | 非自愿失去 |
| 抢夺 | 强行夺取 |
| 盗取 | 偷窃 |
| 供奉 | 向神灵/势力供奉 |
| 收租 | 收取租金/供奉 |

### 5.5 `social_capital_impact` - 人情/因果影响

常见值：
- 建立香火情
- 偿还香火情
- 因果债
- 结下因果
- 了结因果
- 无

### 经济活动示例

```json
{
  "economics": [
    {
      "actor": "陈平安",
      "target": "阮邛",
      "action": "购买",
      "item": "铁剑",
      "amount": 1,
      "currency": {
        "type": "谷雨钱",
        "level": "仙家",
        "quantity": 1
      },
      "asset_category": "实物",
      "terms": null,
      "social_capital_impact": "建立香火情",
      "context": "陈平安向阮邛购买铁剑"
    },
    {
      "actor": "郑居中",
      "target": "陈平安",
      "action": "借贷",
      "item": "金精铜钱",
      "amount": 300,
      "currency": {
        "type": "金精铜钱",
        "level": "仙家",
        "quantity": 300
      },
      "asset_category": "货币",
      "terms": {
        "interest_rate": "3%",
        "settlement_period": "每年",
        "repayment_condition": "本金叠加，利息逐年结算",
        "collateral": ""
      },
      "social_capital_impact": "因果债",
      "context": "用于陈平安提升本命飞剑井中月品秩"
    }
  ]
}
```

---

## 6. `plot_links` - 伏笔与回调

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| type | String | 是 | 类型（见枚举） |
| content | String | 是 | 内容描述 |
| related_entity | String | 否 | 相关实体名称 |
| entity_type | String | 否 | 实体类型：人物、物品、地点、生物、事件 |
| chapter_introduced | Integer | 是 | 伏笔首次出现的章节 |
| status | String | 是 | 状态：未解决、已解决、部分解决 |
| clues | Array[String] | 否 | 线索列表（便于后续匹配） |
| inference | String | 否 | 推断/推测 |
| resolved_in_chapter | Integer | 否 | 解决章节（如已解决） |
| resolution | String | 否 | 解决内容（揭秘详情） |

### `type` 枚举值

| 值 | 说明 |
|------|------|
| 伏笔 | 埋下线索，尚未揭晓 |
| 身份揭秘 | 某人/某物的真实身份被揭示 |
| 回调 | 回应前文伏笔，填坑 |
| 矛盾 | 与前文描述存在冲突 |
| 暗示 | 模糊的暗示，不确定是否为伏笔 |

### 动态注入提示词机制

由于逐章提取时LLM只能看到当前章节，需要将历史伏笔动态注入提示词：

**后处理流程**：
1. **提取阶段**：每章提取时，将 `status="未解决"` 的伏笔收集到 `pending_plot_links.json`
2. **注入阶段**：提取下一章时，将相关伏笔注入提示词的动态上下文
3. **更新阶段**：当检测到 `type="身份揭秘"` 或 `type="回调"` 时，更新对应伏笔的 `status`

**提示词注入格式示例**：
```
【未解决的伏笔】
1. 第1章：四脚蛇额头隆起似要生角 [线索：额头隆起、被丢弃后自己跑回] → 推测：龙蛇类灵物
2. 第1章：锦衣少年身份不明 [线索：锦衣华服、有随从吴爷爷] → 推测：某大势力公子
3. 第50章：戴斗笠的汉子 [线索：戴斗笠、背刀、剑气冲天] → 推测：可能是阿良

【任务】如果本章揭示了上述伏笔的真相，请在 plot_links 中记录 type="身份揭秘" 或 type="回调"。
```

### 伏笔示例

```json
{
  "plot_links": [
    {
      "type": "伏笔",
      "content": "四脚蛇额头隆起，似要生角",
      "related_entity": "四脚蛇",
      "entity_type": "生物",
      "chapter_introduced": 1,
      "status": "未解决",
      "clues": ["额头隆起", "被宋集薪丢弃后自己跑回"],
      "inference": "可能是龙蛇类灵物，后续可能化龙",
      "resolved_in_chapter": null,
      "resolution": null
    },
    {
      "type": "身份揭秘",
      "content": "确认'戴斗笠的汉子'就是阿良",
      "related_entity": "阿良",
      "entity_type": "人物",
      "chapter_introduced": 50,
      "status": "已解决",
      "clues": ["戴斗笠", "背刀", "剑气冲天"],
      "inference": "",
      "resolved_in_chapter": 105,
      "resolution": "戴斗笠的汉子摘下斗笠，露出真容，正是阿良"
    }
  ]
}
```

---

## 7. `items` - 物品

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | String | 是 | 物品名称 |
| original_name | String | 否 | 原名（如有改名） |
| type | String | 是 | 类型（见枚举） |
| subtype | String | 否 | 细分类型 |
| holder | String | 否 | 当前持有者 |
| holder_relation | String | 否 | 持有者与物品的炼化关系（见枚举） |
| previous_holders | Array[Object] | 否 | 历任持有者 |
| rank | String | 否 | 品秩（见枚举） |
| rank_potential | String | 否 | 潜力/可成长性 |
| supernatural_ability | String | 否 | 本命神通/特殊能力 |
| evolution | Object | 否 | 演化信息 |
| visual | Object | 否 | 视觉描述 |
| provenance | Object | 否 | 因果渊源 |
| action | String | 否 | 本章行为（见枚举） |
| description | String | 否 | 描述 |

### 7.1 `type` - 物品类型枚举

| 值 | 说明 |
|------|------|
| 本命飞剑 | 剑修根本，与性命相连 |
| 仙剑 | 非本命的高品秩剑 |
| 法宝 | 可催动神通的宝物 |
| 灵器 | 有灵性的器物 |
| 重器 | 重型兵器 |
| 匠器 | 普通打造的器物 |
| 方寸物 | 储物空间类 |
| 丹药 | 丹丸类 |
| 典籍 | 功法秘籍 |
| 符箓 | 符纸类 |
| 货币 | 钱财类 |
| 灵物 | 有灵性的生物/植物 |
| 材料 | 炼器/炼丹材料 |
| 其他 | 其他物品 |

### 7.2 `holder_relation` - 炼化关系枚举

| 值 | 说明 |
|------|------|
| 大炼 | 本命物，与性命相连，失去则重伤或死亡 |
| 中炼 | 初步掌控，可随意驱使 |
| 小炼 | 可收入气府，但易被抢夺 |
| 持有 | 仅持有，未炼化 |
| 寄托 | 暂时寄托于此人 |

### 7.3 `previous_holders` - 历任持有者

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | String | 是 | 持有者名称 |
| relation | String | 是 | 关系：原主、赠予者、曾持有、夺取自、继承自 |

### 7.4 `rank` - 品秩枚举（从高到低）

| 值 | 说明 |
|------|------|
| 仙兵 | 最高品秩，可斩杀仙人 |
| 半仙兵 | 接近仙兵，或可成长为仙兵 |
| 法宝 | 高品秩，可催动神通 |
| 灵器 | 中品秩，有灵性 |
| 重器 | 物理属性强大 |
| 匠器 | 普通器物 |

### 7.5 `evolution` - 演化信息

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| current_form | String | 否 | 当前形态 |
| materials_consumed | Array[String] | 否 | 已吞噬/炼化的材料 |
| potential_evolution | String | 否 | 潜在演化方向 |

### 7.6 `visual` - 视觉描述

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| static | String | 否 | 静止态外观 |
| active | String | 否 | 运动态/施展时外观 |

### 7.7 `provenance` - 因果渊源

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| origin | String | 否 | 来源/出处 |
| karma_link | String | 否 | 因果关联（涉及的大势/人物/道统） |

### 7.8 `action` - 本章行为枚举

| 值 | 说明 |
|------|------|
| 获得 | 首次获得 |
| 祭炼 | 进行炼化 |
| 使用 | 施展/动用 |
| 赠予 | 赠送他人 |
| 失去 | 失去持有 |
| 损毁 | 被破坏 |
| 升级 | 品秩提升 |
| 吞噬 | 吞噬材料 |
| 提及 | 仅提及，未实际动用 |

### 物品示例

```json
{
  "items": [
    {
      "name": "初一",
      "original_name": "小酆都",
      "type": "本命飞剑",
      "subtype": "剑胚",
      "holder": "陈平安",
      "holder_relation": "大炼",
      "previous_holders": [
        {"name": "穗山真人", "relation": "原主"},
        {"name": "离真", "relation": "曾持有"}
      ],
      "rank": "半仙兵",
      "rank_potential": "可成长至仙兵",
      "supernatural_ability": "极致速度，锋锐，针对神性有压胜效果",
      "evolution": {
        "current_form": "剑胚",
        "materials_consumed": ["斩龙石"],
        "potential_evolution": "完整飞剑"
      },
      "visual": {
        "static": "微缩如白毫，藏于养剑葫",
        "active": "金色长虹，轨迹如流水不滞"
      },
      "provenance": {
        "origin": "穗山遗物",
        "karma_link": "与持剑者、陈清都及蛮荒大势深度挂钩"
      },
      "action": "祭炼",
      "description": "陈平安的第一把本命飞剑，得自穗山，后经剑气长城多年砥砺。"
    }
  ]
}
```

---

## 8. `locations` - 地点

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | String | 是 | 地点名称 |
| tier | String | 否 | 地理层级：宏观、中观、微观 |
| type | String | 否 | 类型（见枚举） |
| hierarchy | Object | 否 | 空间层级结构 |
| metaphysical | Object | 否 | 山水官场属性 |
| connectivity | Object | 否 | 连接属性 |
| visual | Object | 否 | 视觉描述 |
| historical_status | Array[Object] | 否 | 历史演变状态 |
| description | String | 否 | 描述 |

### 8.1 `tier` - 地理层级枚举

| 值 | 说明 |
|------|------|
| 宏观 | 天下级别、跨界枢纽 |
| 中观 | 洲陆、王朝、洞天福地 |
| 微观 | 城镇、山头、街道 |

### 8.2 `type` - 地点类型枚举

| 值 | 说明 |
|------|------|
| 天下 | 四座天下之一 |
| 大陆 | 洲陆 |
| 洞天福地 | 小洞天、福地 |
| 王朝 | 世俗王朝 |
| 城池 | 城市 |
| 宗门 | 宗门山头 |
| 书院 | 儒家书院 |
| 山岳 | 山峰 |
| 湖泊 | 水域 |
| 街道 | 巷弄街道 |
| 跨界枢纽 | 连接不同天下/大陆的门户 |
| 仙都 | 仙家圣地 |
| 战场 | 战略要地 |
| 其他 | 其他 |

### 8.3 `hierarchy` - 空间层级结构

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| world | String | 否 | 所属天下 |
| continent | String | 否 | 所属大陆/洲 |
| region | String | 否 | 所属区域（王朝/洞天） |
| sub_region | String | 否 | 次级区域 |
| parent | String | 否 | 直接上级地点 |

#### `world` 枚举值
- 浩然天下
- 蛮荒天下
- 青冥天下
- 西方佛国
- 五彩天下

### 8.4 `metaphysical` - 山水官场属性

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| site_type | String | 否 | 地点性质：世俗、福地、仙家、妖域、鬼蜮、神域 |
| luck_trait | String | 否 | 气运/道痕特征 |
| officialdom | String | 否 | 神位/官职（如五岳山君、城隍、江神） |
| authority | String | 否 | 管辖权归属 |

### 8.5 `connectivity` - 连接属性

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| is_hub | Boolean | 否 | 是否为交通枢纽 |
| connections | Array[String] | 否 | 连接的地点列表 |

### 8.6 `visual` - 视觉描述

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| texture | String | 否 | 质感描述 |
| atmosphere | String | 否 | 气象/氛围 |

### 8.7 `historical_status` - 历史演变状态

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| era | String | 是 | 时代/时期 |
| status | String | 是 | 该时期的状态 |

### 地点示例

```json
{
  "locations": [
    {
      "name": "泥瓶巷",
      "tier": "微观",
      "type": "街道",
      "hierarchy": {
        "world": "浩然天下",
        "continent": "宝瓶洲",
        "region": "龙泉郡",
        "sub_region": "小镇",
        "parent": "小镇"
      },
      "metaphysical": {
        "site_type": "世俗",
        "luck_trait": "真龙龙须（一隐一显）",
        "officialdom": null,
        "authority": "大骊律法"
      },
      "connectivity": {
        "is_hub": false,
        "connections": []
      },
      "visual": {
        "texture": "泥土颗粒感，黄土夯筑墙体",
        "atmosphere": "阴暗狭窄，低饱和度"
      },
      "historical_status": [
        {"era": "洞天时期", "status": "受四方圣人镇压"},
        {"era": "落地后", "status": "大骊版图，气运释放"}
      ],
      "description": "小镇中的一条阴暗巷弄，陈平安祖宅所在地。"
    },
    {
      "name": "白玉京",
      "tier": "宏观",
      "type": "仙都",
      "hierarchy": {
        "world": "青冥天下",
        "continent": "",
        "region": "",
        "sub_region": "",
        "parent": "青冥天下"
      },
      "metaphysical": {
        "site_type": "道教祖庭",
        "luck_trait": "道祖道场",
        "officialdom": "三位掌教",
        "authority": "道家最高权力中心"
      },
      "connectivity": {
        "is_hub": true,
        "connections": ["青冥天下诸天", "浩然天下"]
      },
      "visual": {
        "texture": "云海之上，高悬天际",
        "atmosphere": "仙气缭绕，流动性极强"
      },
      "historical_status": [],
      "description": "青冥天下道教祖庭，云海之上的最高仙都。"
    }
  ]
}
```

---

## 9. `factions` - 势力

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | String | 是 | 势力名称 |
| type | String | 否 | 类型（见枚举） |
| tier | String | 否 | 宗门等级（仅宗门适用）：祖庭/祖宗、正宗、下宗 |
| location | String | 否 | 势力所在地 |
| leader | String | 否 | 掌门/领袖 |
| parent_faction | String | 否 | 上级势力（如下宗的祖宗） |
| description | String | 否 | 描述 |
| status_change | Object | 否 | 状态变化 |

### 9.1 `type` - 势力类型枚举

| 值 | 说明 |
|------|------|
| 王朝 | 世俗王朝 |
| 宗门 | 修行宗门 |
| 家族 | 世家大族 |
| 书院 | 儒家书院 |
| 神灵体系 | 神灵势力 |
| 妖族势力 | 妖族势力 |
| 城池 | 城池势力 |
| 其他 | 其他 |

### 9.2 `tier` - 宗门等级枚举

仅宗门类型适用。《剑来》中，唯有拥有"上五境"修士坐镇的山头，才有资格在名号后挂上"宗"字。

| 值 | 说明 |
|------|------|
| 祖庭 | 祖宗级别，一派之源头 |
| 正宗 | 正统宗门 |
| 下宗 | 附属于正宗的下级宗门 |

### 9.3 `status_change` - 状态变化

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| reputation | String | 否 | 声望变化：上升、下降、无变化 |
| strength | String | 否 | 实力变化：增强、削弱、无变化 |

### 势力示例

```json
{
  "factions": [
    {
      "name": "落魄山",
      "type": "宗门",
      "tier": "正宗",
      "location": "宝瓶洲龙州",
      "leader": "陈平安",
      "parent_faction": null,
      "description": "由陈平安建立，底蕴惊人，汇聚多位止境武夫和上五境剑修，门风以诚待人。",
      "status_change": {
        "reputation": "上升",
        "strength": "增强"
      }
    },
    {
      "name": "青萍剑宗",
      "type": "宗门",
      "tier": "下宗",
      "location": "桐叶洲仙都山",
      "leader": "崔东山",
      "parent_faction": "落魄山",
      "description": "落魄山的下宗，纯粹剑道宗门，建立了三府六司八局行政架构。",
      "status_change": {
        "reputation": "",
        "strength": ""
      }
    }
  ]
}
```

---

## 10. `quotes` - 金句

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| content | String | 是 | 引文内容 |
| speaker | String | 是 | 说话者 |
| context | String | 否 | 上下文 |

### 金句示例

```json
{
  "quotes": [
    {
      "content": "天雨虽宽不润无根之草。",
      "speaker": "苻南华",
      "context": "苻南华对陈平安说的话，暗讽陈平安没有根骨福缘。"
    },
    {
      "content": "大道可期，阻我前路，仙佛可杀！",
      "speaker": "苻南华",
      "context": "苻南华心中默念，展现为证道不惜一切的狠辣。"
    }
  ]
}
```

---

## 附录：完整 JSON 示例

```json
{
  "meta": {
    "chapter_id": 1,
    "chapter_title": "第1章 惊蛰"
  },

  "characters": [
    {
      "name": "陈平安",
      "is_identified": true,
      "aliases": ["少年", "泥瓶巷少年"],
      "bio": "居住在泥瓶巷的孤儿，曾是龙窑学徒。",
      "appearance": {
        "facial": "眼神清澈，面容清瘦",
        "physique": "身形单薄",
        "attire": "草鞋布衣",
        "aura": "气质坚韧"
      },
      "cultivation": {
        "path": "凡人",
        "realm": "",
        "realm_name": "",
        "stage": ""
      },
      "techniques": [],
      "faction": "无",
      "tags": ["孤儿", "窑匠"],
      "chapter_experience": "被苻南华轻视，错失与仙家结交的机缘。",
      "state_snapshots": [
        {"location": "泥瓶巷", "injuries": "无", "description": ""}
      ]
    }
  ],

  "relations": [
    {
      "source": "陈平安",
      "target": "宋集薪",
      "type": ["邻居"],
      "positive_delta": 0,
      "negative_delta": 2,
      "evidence": "宋集薪鄙夷嘲讽陈平安"
    }
  ],

  "events": [
    {
      "name": "官窑关闭",
      "type": "政治",
      "scope": "中观",
      "status": "已发生",
      "location": {
        "world": "浩然天下",
        "continent": "宝瓶洲",
        "region": "骊珠洞天",
        "specific_site": "小镇"
      },
      "participants": [
        {"name": "陈平安", "role": "受影响者"}
      ],
      "causality": {
        "root_cause": "万年契约期满",
        "direct_trigger": "大骊朝廷勒令关闭",
        "related_events": []
      },
      "systemic_change": {
        "rule_affected": "本命瓷体系终结",
        "luck_transfer": "气运回归个体"
      },
      "consequences": "匠人失业",
      "power_system_tags": [],
      "resource_tags": ["气运"],
      "is_foreshadowing": false,
      "description": "小镇失去官窑造办资格。"
    },
    {
      "name": "锦衣少年夜访",
      "type": "剧情",
      "scope": "微观",
      "status": "已结束",
      "location": {
        "world": "浩然天下",
        "continent": "宝瓶洲",
        "region": "骊珠洞天",
        "specific_site": "泥瓶巷"
      },
      "participants": [
        {"name": "锦衣少年", "role": "发起者"},
        {"name": "陈平安", "role": "受益者"}
      ],
      "causality": null,
      "systemic_change": null,
      "consequences": "陈平安获得一袋金钱",
      "power_system_tags": [],
      "resource_tags": [],
      "is_foreshadowing": true,
      "description": "锦衣少年夜间来到泥瓶巷，赠予陈平安金钱。"
    }
  ],

  "economics": [
    {
      "actor": "锦衣少年",
      "target": "陈平安",
      "action": "赠予",
      "item": "绣袋",
      "amount": 1,
      "currency": {"type": "银两", "level": "凡俗", "quantity": null},
      "asset_category": "实物",
      "terms": null,
      "social_capital_impact": "",
      "context": "买走鲤鱼的酬谢"
    }
  ],

  "plot_links": [
    {
      "type": "伏笔",
      "content": "四脚蛇额头隆起似要生角",
      "related_entity": "四脚蛇",
      "entity_type": "生物",
      "chapter_introduced": 1,
      "status": "未解决",
      "clues": ["额头隆起"],
      "inference": "可能是龙蛇类灵物",
      "resolved_in_chapter": null,
      "resolution": null
    }
  ],

  "items": [
    {
      "name": "金黄鲤鱼",
      "original_name": "",
      "type": "灵物",
      "subtype": "",
      "holder": "锦衣少年",
      "holder_relation": "持有",
      "previous_holders": [],
      "rank": "",
      "rank_potential": "",
      "supernatural_ability": "",
      "evolution": null,
      "visual": {"static": "金灿灿，巴掌长短", "active": ""},
      "provenance": {"origin": "", "karma_link": ""},
      "action": "获得",
      "description": "陈平安想买但被锦衣少年截胡。"
    }
  ],

  "locations": [
    {
      "name": "泥瓶巷",
      "tier": "微观",
      "type": "街道",
      "hierarchy": {
        "world": "浩然天下",
        "continent": "宝瓶洲",
        "region": "骊珠洞天",
        "sub_region": "",
        "parent": "小镇"
      },
      "metaphysical": {
        "site_type": "世俗",
        "luck_trait": "",
        "officialdom": null,
        "authority": ""
      },
      "connectivity": {"is_hub": false, "connections": []},
      "visual": {"texture": "泥土夯筑", "atmosphere": "阴暗狭窄"},
      "historical_status": [],
      "description": "陈平安祖宅所在地。"
    }
  ],

  "factions": [
    {
      "name": "大骊宋氏",
      "type": "王朝",
      "tier": "",
      "location": "宝瓶洲",
      "leader": "",
      "parent_faction": null,
      "description": "国力强盛的王朝。",
      "status_change": {"reputation": "", "strength": ""}
    }
  ],

  "quotes": [
    {
      "content": "天雨虽宽不润无根之草。",
      "speaker": "苻南华",
      "context": "暗讽陈平安没有根骨福缘。"
    }
  ]
}
```


