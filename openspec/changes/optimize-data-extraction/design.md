# design.md - Data Optimization Schema

## 1. Core Principles
- **Atomicity**: Data extracted from a chapter must be purely local to that chapter. Aggregation logic handles the rest.
- **Structure**: Prefer Enums and Objects over free text for key fields (Cultivation, Relation Type).
- **Context**: Every entity/event must try to anchor itself to a Location.
- **AI-Native Normalization**: Shift normalization (Faction names, Entity types) "left" to the LLM extraction phase where context is richest, reducing reliance on brittle regex in post-processing.

## 2. Updated JSON Schema Definition

### 2.1 Meta & World Context (New)
```json
{
  "meta": {
    "chapter_id": "Integer",
    "chapter_title": "String",
    "world_timestamp": {
       "season": "String", 
       "year_inference": "String"
    }
  },
  "world_events": [ 
    {
      "name": "String", 
      "status": "Enum(New|Ongoing|Ended)",
      "impact_scope": "Enum(World|Continent|Dynasty|Sect|Individual)",
      "description": "String"
    }
  ]
}
```

### 2.2 Characters (Refined)
```json
{
  "name": "String (Canonical Name)",
  "is_new_appearance": "Boolean",
  "role_in_chapter": "Enum(Protagonist|Supporting|Antagonist|background)",
  "aliases": ["String", "List"],
  "bio": "String",
  "cultivation": {
    "system": "Enum(武夫|练气士|剑修|纯粹剑修|儒家|佛家|道家|妖族|...)",
    "realm": "String",
    "stage": "String"
  },
  "faction": "String",
  "tags": ["String"],
  "economics": [{"action": "Spend", "item": "String", "amount": "Number", "target": "String"}]
}
```

### 2.3 Unidentified Figures (New Buffer)
```json
{
  "reference_text": "String (e.g. '那个戴斗笠的汉子')",
  "appearance_features": ["String"],
  "action_summary": "String",
  "suspected_identity": "String (Optional LLM Guess)"
}
```

### 2.4 Relations (Refined)
```json
{
  "source": "String",
  "target": "String",
  "type": "Enum(Kinship|MasterDisciple|Friendship|Hostility|Romance|Colleague|Other)",
  "delta": "Integer (Negative for worsening, Positive for improving)",
  "is_debt": "Boolean (Involves causality/favors)",
  "context": "String"
}
```

### 2.5 Plot Links & Foreshadowing (New)
```json
{
  "type": "Enum(IdentityReveal|Foreshadowing)",
  "content": "String (e.g. 'The man in the bamboo hat revealed to be A Liang')",
  "related_entity": "String",
  "inference": "String"
}
```

### 2.6 Events (Enhanced)
```json
{
  "name": "String",
  "type": "Enum(Battle|Dialogue|Travel|Epiphany|PlotTwist|Flashback)",
  "location": "String",
  "participants": ["String"],
  "description": "String",
  "impact": "String"
}
```

### 2.7 Items (Enhanced)
```json
{
  "name": "String",
  "type": "Enum(Weapon|Artifact|Consumable|Book|Other)",
  "holder": "String",
  "action": "Enum(Acquire|Use|Lose|Gift|Destroy)",
  "previous_holder": "String",
  "rank": "String"
}
```

### 2.8 Factions (Enhanced)
```json
{
  "name": "String",
  "type": "Enum(Dynasty|Sect|Academy|Other)",
  "status_change": {
    "reputation": "String",
    "formation": "String"
  }
}
```

### 2.9 Locations (Hierarchy Support)
```json
{
  "name": "String",
  "type": "Enum(Town|Mountain|Sect|Dungeon|Wilderness)",
  "parent": "String (Containing location, e.g. 这里的parent是骊珠洞天)",
  "description": "String"
}
```


1.  **Prompt Engineering (Inference-Based)**:
    -   Adopt the `Role - Knowledge Rules - Dynamic Context - Task` prompt structure.
    -   Implement `unidentified_figures` and `plot_links` in the JSON schema.
2.  **Context Management Logic**:
    -   (Stub) Develop a `ContextManager` class in `extract_pipeline.py`.
    -   It maintains a rolling window of `Active Characters` and `Global Events` to inject into the next chapter's prompt.
3.  **Backtracking System (Human-in-the-Loop)**:
    -   Create a `pending_entities.json` (or SQLite table) to store all `unidentified_figures`.
    -   Implement a `backtrack_resolver.py` that listens for `IdentityReveal` events and updates historical data.
4.  **Validation**: Update `process_data.py` to warn if `cultivation` is a string instead of an object, or if `type` is invalid.
