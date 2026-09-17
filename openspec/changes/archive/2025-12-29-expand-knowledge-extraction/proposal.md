# Proposal: Expand Knowledge Extraction

## Why
The current relationship extraction is limited to simple node links. The user wants a comprehensive "World Knowledge Graph" for *Sword Coming*, capturing complex entity attributes (Cultivation, Factions), geography, items (Swords), and cultural elements (Quotes). This requires a significant schema expansion to better represent the novel's depth.

## What
We will expand the extraction schema to output a multi-faceted JSON object for each chapter, containing:
1.  **Entities**: Characters (with Bio, Cultivation, Faction), Locations, Factions, Items.
2.  **Relations**: Existing directed relationship logic.
3.  **Culture**: Quotes and Events.

We will also refactor the storage strategy to use per-chapter JSON files in `data/raw/` to manage the increased data size and complexity, enabling safer incremental processing and resume logic.

## How
1.  **Refactor Extraction**: Update `extract_pipeline.py` with a new, complex `SYSTEM_PROMPT` tailored for the V2 Schema.
2.  **Storage Update**: Change file writing logic to save `data/raw/{chapter}.json`.
3.  **Verification**: Test extraction on a subset of chapters to ensure schema compliance and JSON validity.

