# Design: Knowledge Base Aggregation

## Schema Definition (Output)

The builder will produce a `data/build/` folder structured for the Mini Program:

### 1. `characters.json` (The Wiki Database)
Map of `CharacterID` -> Profile Object.
```json
{
  "陈平安": {
    "name": "陈平安",
    "aliases": ["泥瓶巷少年", "陈先生"],
    "bio_summary": "Merged bio...",
    "cultivation_log": [
      {"chapter": 1, "state": "凡人"},
      {"chapter": 100, "state": "二境武夫"}
    ],
    "factions": ["落魄山", "文圣一脉"],
    "quotes": [
       {"content": "...", "chapter": "001"}
    ],
    "relations": {
      "宁姚": {
         "type": "爱慕", 
         "strength": 9,
         "evidence": [
             {"chapter": "001", "text": "..."},
             {"chapter": "100", "text": "..."}
         ]
      }
    }
  }
}
```

### 2. `items.json` (Artifact Registry)
Map of `ItemID` -> Item Object.
```json
{
  "长气": {
    "name": "长气",
    "type": "飞剑",
    "description": "Merged description...",
    "ownership_log": [
      {"chapter": 10, "owner": "User A"},
      {"chapter": 20, "owner": "User B"}
    ]
  }
}
```

### 3. `locations.json` & `factions.json`
Similar structure, merging descriptions and parent hierarchies.
*   **Locations**: `parent` field should track hierarchy (e.g. "Bottle Continent" -> "Old Dragon City").
*   **Factions**: Track `members` (derived from character `faction` fields).

### 4. `timeline.json` (The Chronicle)
Ordered list of events (Time-based view).

## Merging Logic Strategy

1.  **Relation Merging**:
    *   If `A -> B` exists in Ch1 (Strength 2) and Ch5 (Strength 5), merge:
        *   `strength`: Take the maximum (5).
        *   `evidence`: Append new evidence to list.
2.  **Item Merging**:
    *   Track `owner` changes across chapters to build `ownership_log`.
3.  **Quote Attribution**:
    *   Move extracted "Quotes" into the `quotes` list of the corresponding speaker in `characters.json`.
    *   Also maintain a global `quotes.json` index for random daily quotes.
