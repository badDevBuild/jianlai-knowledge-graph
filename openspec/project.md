# Project Context

## Purpose
The goal of this project is to build a comprehensive, interactive **Character Relationship Graph** for the Chinese novel **"Sword Coming" (剑来)**.
The system extracts relationships from raw novel text using a local Large Language Model (LLM), processes and cleans the data to resolve entities and merging logic, and visualizes the network in a browser.

## Tech Stack
- **Core Logic**: Python 3 (Scripts for splitting, extracting, processing)
- **LLM Integration**: Local Gemini API (Custom HTTP wrapper via `httpx`)
- **Frontend**: HTML5, JavaScript (ES6+)
- **Visualization Library**: `force-graph` (via CDN)
- **Data Format**: JSON (`full` for raw extraction, `clean` for visualization)

## Project Conventions

### Code Style
- **Python**: PEP 8. Snake_case for functions and variables.
- **Data**: All extraction output MUST be in **Chinese**. NO English in relationship data.
- **Paths**: Use absolute paths for file operations to ensure stability.

### Architecture Patterns
**Pipeline Architecture**:
1.  **Preprocessing**: `split_demo.py` splits the single large TXT into individual chapter files.
2.  **Extraction**: `extract_pipeline.py` iterates chapters, calls Local Gemini API, and incrementally saves to `relations_full.json`.
3.  **Data Cleaning**: `process_data.py` aggregates raw data, resolves aliases (e.g., "草鞋少年" -> "陈平安"), and calculates link curvature/weights, outputting `relations_clean.json`.
4.  **Visualization**: `graph_view.html` fetches `relations_clean.json` and renders an interactive Force Directed Graph.

### Naming Conventions
- **Raw Data**: `relations_full.json` (Incremental, redundant)
- **Production Data**: `relations_clean.json` (Aggregated, normalized)
- **Chapter Files**: `chapters/{id}_{title}.txt`

## Domain Context
- **Source Material**: "Sword Coming" (剑来), a long-running Xianxia novel.
- **Entities**: Characters often have multiple aliases (e.g., nicknames, titles, disguises) which change over time.
- **Relationships**: Complex and evolving (e.g., Enemy -> Friend -> Master/Disciple).
- **Directionality**: Relationships are **Directed**. (A->B is distinct from B->A).

## Important Constraints
- **Local Environment**: Run on user's Mac. Visualization served via `python3 -m http.server`.
- **API Stability**: The local API is prone to timeouts or `Extra data` errors; extraction scripts must be robust (resume logic, robust JSON parsing).
- **Performance**: Visualization must handle hundreds of nodes without freezing (use optimized mouse listeners).

## External Dependencies
- **LLM Server**: Local endpoint at `http://127.0.0.1:7861`; credentials are supplied through environment variables and are never committed.
- **Visual Lib**: `https://unpkg.com/force-graph`
