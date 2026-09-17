# Character Profile Schema (Global)

此 Schema 用于描述单个角色的全局信息汇总（非分章节）。

```json
{
  "name": "String", // 角色真名
  "aliases": ["String"], // 别名/绰号列表
  "bio": "String", // 人物生平简介
  "appearance": {
    "facial": "String", // 面部特征
    "physique": "String", // 体型体态
    "attire": "String", // 衣着打扮
    "aura": "String" // 气质
  },
  "cultivation": [ // 修行体系（数组，支持兼修）
    {
      "path": "String", // 途径：纯粹武夫/炼气士/剑修/儒家...
      "realm": "String", // 境界：如“十境”、“玉璞境”
      "realm_name": "String", // 境界别名：如“止境”
      "stage": "String", // 细分阶段：如“气盛”、“归真”
      "visual_traits": "String", // 视觉表现
      "notes": "String" // 备注
    }
  ],
  "techniques": [ // 功法武学
    {
      "name": "String",
      "type": "String", // 拳法/剑术/符箓/阵法...
      "description": "String"
    }
  ],
  "factions": ["String"], // 所属势力列表（包含曾加入的）
  "tags": ["String"], // 身份标签
  "quotes": [ // 金句（数据源：原文提取）
    {
      "content": "String",
      "context": "String",
      "chapter": "String"
    }
  ],
  "relations": { // 人物关系（数据源：原文提取）
    "TargetName": {
      "type": ["String"], // 关系类型列表
      "strength": "Integer", // 关系强度
      "evidence": [
        {
          "chapter": "String",
          "text": "String"
        }
      ]
    }
  }
}
```

## 变更说明
1. **全局汇总**：移除 `chapter_experience` 等单章字段。
2. **Cultivation 数组化**：支持武夫+炼气士双修。
3. **Factions 数组化**：支持多重势力归属。
4. **移除冗余字段**：`unidentified_info`, `plot_links`, `events`, `economics`, `locations`。
5. **保留原始数据**：`quotes` 和 `relations` 字段结构复用现有数据。
