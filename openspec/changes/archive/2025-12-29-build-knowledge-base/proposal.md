# Proposal: Build Knowledge Base (Reconstruction)

## Why
We currently have raw, per-chapter extracted data in `data/raw/`. To power a WeChat Mini Program (Wiki, Map, Timeline), we must reconstruct this fragmented information into a cohesive, structured Knowledge Base. Validating this reconstruction experimentally now permits us to iterate on the schema before processing the full novel.

## What
We will create a `build_knowledge_base.py` script to:
1.  **Merge Entities**: Consolidate characters (Bio, Aliases, Factions) and resolve identity across chapters.
2.  **Construct Timelines**: Sequence extraction events and character attribute changes (e.g., Cultivation growth) by chapter.
3.  **Generate Indices**: Produce optimized JSONs (`index.json`, `minigram_data.json`) ready for frontend consumption.

## How
- **Input**: `data/raw/*.json`
- **Logic**: 
    - Auto-merge by exact name match.
    - Semi-auto resolve aliases (log potential matches).
    - Aggregate "Strength" lists for relations.
- **Output**: `data/build/` directory containing:
    - `characters.json`: Full profile registry.
    - `timeline.json`: Global event stream.
    - `search_index.json`: Keyword mapping.
