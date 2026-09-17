# 《剑来》人物全书档案 JSON Schema V3.0

## 概述
本文档定义了**全书汇总**视角的单个角色档案数据结构。
数据来源组合：
1. **AI 生成 (NotebookLM)**：生平 (Bio)、外貌 (Appearance)、修为 (Cultivation - 数组)、功法 (Techniques)、势力 (Factions - 数组)、标签 (Tags)。
2. **原文提取 (Existing DB)**：金句 (Quotes)、关系 (Relations)。

## JSON 结构
```json
{
  "name": "String", // 角色真名
  "aliases": ["String"], // 别名列表
  "bio": "String", // 全书生平简介
  "appearance": {
    "facial": "String", // 面部特征（涵盖多时期）
    "physique": "String", // 体型体态
    "attire": "String", // 标志性衣着
    "aura": "String" // 气质气场
  },
  "cultivation": [ // 数组：支持多条修行路径
    {
      "path": "String", // 途径：纯粹武夫/炼气士/剑修...
      "realm": "String", // 境界：如“十境”、“玉璞境”
      "realm_name": "String", // 专有名称：如“止境”、“山巅”
      "stage": "String", // 细分阶段：如“气盛”、“归真”
      "notes": "String" // 备注：如“跌境重修”、“最强气盛”
    }
  ],
  "techniques": [ // 功法武学
    {
      "name": "String",
      "type": "String", // 拳法/剑术/符箓/阵法...
      "description": "String" // 简要描述
    }
  ],
  "factions": ["String"], // 所属势力列表（包含曾加入的）
  "tags": ["String"], // 身份标签
  "quotes": [ // 复用 V1/V2 数据
    {
      "content": "String",
      "context": "String",
      "chapter": "String"
    }
  ],
  "relations": { // 复用 V1/V2 数据结构
    "TargetName": {
      "type": ["String"],
      "strength": "Integer",
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
