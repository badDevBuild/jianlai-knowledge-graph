# Design: Knowledge Graph Expansion

## Schema Definition
The new extraction unit (per chapter) will be a JSON object with the following top-level keys:
- `characters`: List of objects `{ name, aliases, bio, cultivation, faction, tags }`
- `locations`: List of objects `{ name, type, description, parent }`
- `factions`: List of objects `{ name, type, description }`
- `items`: List of objects `{ name, type, owner, description, rank }`
- `relations`: List of objects `{ source, target, relation, strength, evidence }` (Existing, but part of the larger object)
- `quotes`: List of objects `{ content, speaker, context }`
- `events`: List of objects `{ name, type, participants, description }`

## Storage Pattern
**Old**: `relations_full.json` (List of relation objects).
**New**: `data/raw/{chapter_filename}.json`.
- Each chapter's extraction is saved individually.
- `extract_pipeline.py` checks for existence of the JSON file to skip processing (resume logic).

## Aggregation Logic (Future Scope)
A separate `build_knowledge_base.py` (evolution of `process_data.py`) will:
1. Iterate all `.json` files in `data/raw/`.
2. Aggregate entities by name/aliases.
3. Construct the timeline of events.
4. Merge attributes (e.g., collect all "Cultivation" updates into a timeline: `[Chapter 1: Tier 1, Chapter 100: Tier 2]`).

## Pipeline Changes
1. **Prompt**: massive update to `SYSTEM_PROMPT` to define strict JSON schema for all the above.
2. **Parsing**: Enhanced robustness to handle large JSON objects.
3. **resume**: logic updated to check `data/raw/`.
