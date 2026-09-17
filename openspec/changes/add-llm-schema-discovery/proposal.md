# Change: Add LLM Full-Text Schema Discovery

## Why
The current novel KG uses a stable generic core schema plus a permissive extension schema. That is safe, but it does not let each novel's own world systems drive extraction. Different books need different attributes, relationship types, event categories, and extraction rules.

## What Changes
- Add a first-pass LLM schema discovery flow that scans every parsed chapter and records schema signals instead of canonical facts.
- Add a schema synthesis step that aggregates all chapter signals into a book-specific extension schema, relationship taxonomy, extraction contract, and discovery report.
- Configure the local LLM path to support the requested `gemma4` model and maximum output tokens.
- Feed the frozen book-specific schema and extraction contract into the second-pass LLM content extractor.
- Cache chapter-level schema discovery responses so long full-book runs can resume.

## Impact
- Affected specs: `llm-schema-discovery`, `llm-structured-extraction`, `novel-content-os-data-layer`
- Affected code: `知识图谱项目/novel_kg/llm.py`, `schema_discovery.py`, `pipeline.py`, `cli.py`, prompts, tests, docs
