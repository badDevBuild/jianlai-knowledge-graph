# Change: Optimize Data Extraction Schema

## Why
The current data extraction schema (v1) provides basic entity and relationship data but lacks the depth required for the "Jianlai" Mini Program's advanced features. Specifically:
- **Cultivation History**: Current `cultivation` field is unstructured strings, making the "Growth Curve" chart impossible to check.
- **Event Context**: Events lack location binding, hindering the "World Map" event overlay.
- **Item Flow**: Item ownership transfer is implicit; explicit tracking is needed for the "Heritage" feature.
- **Quote Retrieval**: Quotes lack metadata (tags/emotion) for the "Mood" filter in the "Golden Quotes" module.

## What Changes
- **Refined JSON Schema**:
    - `meta`: Added `chapter_title`, `world_timestamp` (season, year_inference).
    - `characters`: Structured `cultivation`, added `role_in_chapter` and `is_new_appearance`.
    - `unidentified_figures`: New buffer for ambiguous entities (e.g., "The man in the bamboo hat") to be resolved later.
    - `world_events`: Track global world state (e.g., "War in Sword Edge Great Wall").
    - `plot_links`: Explicitly track identity reveals and foreshadowing for backtracking.
    - `events`: Added `location` reference, `time_of_day`, and `impact_scope`.
    - `items`: Added `previous_owner` and `acquisition_method`.
    - `relations`: Standardized `type` and added `is_debt` (causality) flag.
- **Inference-Based Extraction**:
    - **Context Injection**: dynamically inject `Global Events` and `Active Characters` into the prompt to aid coreference resolution.
    - **Inference Rules**: Use known world laws (e.g., "Shrinking Earth into Inches" implies Upper Five Realms) to infer attributes.
- **Backtracking Mechanism**: Use `IdentityReveal` events to trigger code-level updates to previous chapters' `unidentified_figures`.

## Impact
- **Affected Specs**: `extraction-core`
- **Affected Code**: `extract_pipeline.py` (Prompt templates), `process_data.py` (Validation logic).
- **Data Migration**: Requires re-processing all raw chapter files (User explicitly requested re-extraction).
