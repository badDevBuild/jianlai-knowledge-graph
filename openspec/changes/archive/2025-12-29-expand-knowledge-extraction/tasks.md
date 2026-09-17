# Tasks: Expand Knowledge Extraction

- [x] **Setup**
    - [x] Create `data/raw/` directory to store per-chapter JSONs.
    - [x] Verify local API connectivity with `gemini-3-pro-preview`.

- [x] **Pipeline Refactoring (`extract_pipeline.py`)**
    - [x] **Prompt Update**: Rewrite `SYSTEM_PROMPT` to include instructions and JSON schema for Characters, Locations, Factions, Items, Quotes, Events.
    - [x] **Storage Logic**: Update `main()` to save `data/raw/{filename}.json` instead of appending to global file.
    - [x] **Resume Logic**: Update to check for existence of files in `data/raw/`.
    - [x] **JSON Parsing**: Ensure the `find('{') ... rfind('}')` logic handles the new object structure (previously array).

- [x] **Verification**
    - [x] Run extraction on Chapter 1 (006_xxx.txt) and verify output JSON structure.
    - [x] Verify "Character" fields (Aliases, Cultivation).
    - [x] Verify "Item" extraction (e.g. identifying a sword).
