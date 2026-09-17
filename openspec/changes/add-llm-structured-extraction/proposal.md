# Change: Add LLM Structured Extraction With Evidence Gates

## Why
The current generic novel KG flow produces a runnable data layer, but its heuristic extractor over-creates noisy entities and co-occurrence relationships. That makes the graph queryable but not trustworthy enough for reviewing a novel's real world model.

## What Changes
- Add an LLM extraction mode that calls the local Gemini-compatible endpoint and writes per-chapter structured facts.
- Accept canonical entities, relationships, events, and evidence only when the quoted evidence is present in the chapter text.
- Route invalid, unsupported, or malformed LLM facts into an operator review queue instead of canonical JSONL files.
- Surface extractor mode, accepted/rejected counts, and review queue statistics in pipeline status and quality reporting.

## Impact
- Affected specs: `llm-structured-extraction`, `novel-content-os-data-layer`
- Affected code: `知识图谱项目/novel_kg/pipeline.py`, `cli.py`, new LLM provider/extractor modules, tests, README, quality report
