# Change: Improve Schema Quality Loop

## Why
The current LLM schema workflow can achieve high recall across full novels, but two benchmark runs expose repeatable quality failures: top-level schema inflation, weak boundaries between fields and relationships, missing source absorption, and content-layer semantics that are detected but not fully carried into downstream extraction.

## What Changes
- Add semantic layer hints to schema discovery without filtering raw candidates.
- Upgrade consolidation to produce a layered schema package with top-level systems, subsystems, and content-layer records.
- Extend refinement and quality gates to validate schema boundaries, relation direction contracts, content-layer coverage, and source absorption.
- Add deterministic repair operations for layer assignment, subsystem attachment, direction contract repair, and coverage attachment.
- Add a schema benchmark report that compares the current workflow against the Da Feng and Xue Zhong schema runs.
- Keep canonical content extraction output changes out of this first pass; this change makes content-layer semantics visible in schema artifacts and extraction contracts so the later extraction phase can consume them.

## Impact
- Affected specs: `llm-schema-discovery`
- Affected code:
  - `知识图谱项目/novel_kg/schema_discovery.py`
  - `知识图谱项目/novel_kg/schema_consolidation.py`
  - `知识图谱项目/novel_kg/schema_refinement.py`
  - `知识图谱项目/novel_kg/cli.py`
  - `知识图谱项目/novel_kg/pipeline.py`
  - schema review/report rendering under `知识图谱项目/novel_kg/`
- Benchmark projects:
  - `知识图谱项目/outputs/dafeng_schema_gcli_31_flash_full_schema`
  - `知识图谱项目/outputs/xuezhong_schema_gcli_31_flash_full_schema`
