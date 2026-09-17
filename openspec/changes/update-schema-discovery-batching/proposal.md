# Change: Batch schema discovery calls

## Why

Current schema discovery calls the LLM once per chapter. For long novels such as Xue Zhong, this creates hundreds of calls and gives the model too little cross-chapter context to distinguish durable schema from one-off details.

## What Changes

- Add optional batched schema discovery with configurable `discovery_batch_size` and `discovery_batch_max_chars`.
- Keep single-chapter discovery as the default-compatible path.
- Require batch discovery outputs to include per-evidence `chapter_id`, `chapter_title`, and `quote`.
- Cache batch responses under a parameterized batch cache directory to avoid mixing cache modes.
- Add fallback behavior that splits failed batches into smaller batches and eventually falls back to single chapters.

## Impact

- Affected specs: `llm-schema-discovery`
- Affected code:
  - `知识图谱项目/novel_kg/schema_discovery.py`
  - `知识图谱项目/novel_kg/cli.py`
  - `知识图谱项目/tests/test_novel_kg_pipeline.py`
  - `知识图谱项目/docs/schema_quality_loop_implementation_log.md`
