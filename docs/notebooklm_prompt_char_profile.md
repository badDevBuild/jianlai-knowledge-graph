请基于《剑来》全书内容（包括最新章节），为‘陈平安’生成符合 下述 JSON格式的 数据。

**请求要点**：
**严格遵循以下字段定义**。

### 字段定义详解

#### 2.1 `appearance` - 外貌描写
| 字段     | 说明           |
| -------- | -------------- |
| facial   | **面部特征**   |
| physique | **体型体态**： |
| attire   | **衣着装扮**： |
| aura     | **气质气场**： |

#### 2.2 `cultivation` - 修为境界 (数组，兼修武夫与炼气士)

**纯粹武夫境界参考**：
- 一境泥胚 -> 二境木胎 -> 三境水银（炼体）
- 四境英魂 -> 五境雄魄 -> 六境武胆（炼气）
- 七境金身 -> 八境羽化 -> 九境山巅（炼神）
- 十境止境（气盛/归真/神到）
- 十一境武神（传说）

**炼气士境界参考**：
- 下五境：铜皮、草根、柳筋、骨气、铸庐
- 中五境：洞府、观海、龙门、金丹、元婴
- 上五境：十一境玉璞、十二境仙人、十三境飞升、十四境合道、十五境

**提取要求**：
- `path`: 填写 "纯粹武夫" 或 "炼气士"
- `realm`: 填写全书达到的最高稳定境界
- `realm_name`: 境界专有名称（如“止境”、“合道”）
- `stage`: 细分阶段（如“归真层”）
- `notes`: 详细备注（若有特殊情况，请在这里说明）

#### 2.3 `techniques` - 功法/武学
| 字段        | 说明                                |
| ----------- | ----------------------------------- |
| name        | 名称                                |
| type        | 类型：武学/剑术/符箓/阵法/雷法...   |
| category    | 细分：拳法/剑招/剑诀/符咒...        |
| description | 简述（如“撼山拳包含走桩、立桩...”） |

---

**返回格式（JSON）**：

> [!IMPORTANT]
> **Strictly VALID JSON (RFC 8259)** required.
> - Do **NOT** use unescaped newlines inside strings. Convert paragraphs to single lines or use `\n`.
> - Escape all inner double quotes `"` as `\"`.
> - Do not wrap the JSON in markdown blocks (just raw JSON if possible).


```json
{
  "name": "陈平安",
  "aliases": ["别名1", "别名2"],
  "bio": "全书生平简介...",
  "appearance": {
    "facial": "...",
    "physique": "...",
    "attire": "...",
    "aura": "..."
  },
  "cultivation": [
    {
      "path": "纯粹武夫",
      "realm": "...",
      "realm_name": "...",
      "stage": "...",
      "notes": "..."
    },
    {
      "path": "炼气士",
      "realm": "...",
      "realm_name": "...",
      "stage": "...",
      "notes": "..."
    }
  ],
  "techniques": [
    {
      "name": "...",
      "type": "...",
      "category": "...",
      "description": "..."
    }
  ],
  "factions": ["..."],
  "tags": ["..."]
}
```
