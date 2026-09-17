# Completion Audit

Audit time: 2026-05-07 21:52 CST

## Objective

Implement and try the approved two-pass novel workflow:

1. First pass: read the novel with an LLM to discover a book-specific schema.
2. Second pass: read the novel again and fill the graph using the discovered schema.
3. Initial runtime request was local `gemma4`, but the user later explicitly changed the runtime to `/Users/shushu/.claude/skills/localLLM-geminicli`.
4. Use `gemini-3.1-flash-lite-preview` through local gcli2api with the maximum requested output token setting.

## Checklist

| Requirement | Evidence | Status |
| --- | --- | --- |
| OpenSpec proposal for dynamic LLM schema discovery | `openspec/changes/add-llm-schema-discovery/{proposal.md,design.md,tasks.md,specs/...}` exists; `openspec validate add-llm-schema-discovery --strict` passes. | Done |
| First-pass schema discovery command | `novel_kg schema_discovery.py` implements `run_schema_discovery`; CLI exposes `discover-schema`. | Done |
| Schema artifacts persisted under `source/schema/` | Unit tests verify `schema_discovery_report.json`, `extensions/<slug>.schema.json`, `relationship_taxonomy.json`, and `extraction_contract.md`. | Done |
| Second-pass extraction uses discovered schema | `pipeline.py` loads `extraction_contract.md`, relationship taxonomy, and extension schema; tests verify prompt inclusion. | Done |
| Local gemma4 provider | `OllamaProvider` supports local Ollama API, maps `gemma4` to `gemma4:26b-a4b-it-q4_K_M`, supports `--llm-provider ollama`. | Implemented, not accepted as final runtime path until user confirms local model skill/rules |
| Maximum token setting | Ollama payload uses `num_ctx=262144` and caps JSON output at `num_predict=16384`; raw `1048576` output caused non-terminating/garbled JSON and is not a productive JSON schema setting. | Partially done; needs user-approved runtime policy |
| Real local gemma4 26B A4B smoke | Attempts using `dafeng_schema_gemma4_26b_smoke*` created project scaffolds but did not produce `source/schema/discovery/schema_signals.jsonl` or `schema_discovery_report.json`. User later replaced this requirement with localLLM-geminicli. | Superseded |
| Avoid interfering with user Ollama session | No separate `ollama serve` was started, but requests were sent to the user's existing Ollama service and `ollama stop` was used. User raised concern; no further Ollama calls should run without confirmation. | Blocked |
| Alternate localLLM-geminicli 3.1 flash smoke | Added `GcliOpenAIProvider` and ran `gemini-3.1-flash-lite-preview` via `http://127.0.0.1:7861/v1/chat/completions`. First pass and second pass both succeeded for 1 chapter. | Done for smoke |
| User acceptance of localLLM-geminicli as runtime | User explicitly said: "直接用localLLM-geminicli 就行". | Done |

## Verification Run

Commands that pass:

```bash
python3 -m unittest -v tests/test_novel_kg_pipeline.py
python3 -m compileall novel_kg
openspec validate add-llm-schema-discovery --strict
```

Latest observed test count: 19 tests passing.

## Generated Smoke Artifacts

The first accidental 31B smoke generated a complete first-pass schema artifact set under:

```text
知识图谱项目/outputs/dafeng_schema_gemma4_smoke/source/schema/
```

That result does not satisfy the user's corrected requirement because it used `gemma4:31b`, not `gemma4:26b-a4b-it-q4_K_M`.

The 26B A4B attempts generated only scaffolding and manifest files under:

```text
知识图谱项目/outputs/dafeng_schema_gemma4_26b_smoke/
知识图谱项目/outputs/dafeng_schema_gemma4_26b_smoke_v2/
知识图谱项目/outputs/dafeng_schema_gemma4_26b_smoke_v3/
```

They did not generate the required discovery artifacts:

```text
source/schema/discovery/schema_signals.jsonl
source/schema/schema_discovery_report.json
source/schema/extraction_contract.md
```

## Final Status

The implementation is present and unit-tested. The original gemma4 smoke did not succeed, but the user explicitly replaced the runtime with localLLM-geminicli. Under that accepted runtime, the two-pass smoke is complete.

The user redirected the smoke to `/Users/shushu/.claude/skills/localLLM-geminicli` with 3.1 flash. That alternate path succeeded:

```text
知识图谱项目/outputs/dafeng_schema_gcli_31_flash_smoke_v2/source/schema/schema_discovery_report.json
知识图谱项目/outputs/dafeng_schema_gcli_31_flash_smoke_v2/source/schema/extraction_contract.md
知识图谱项目/outputs/dafeng_schema_gcli_31_flash_smoke_v2/projections/sqlite/dafeng_schema_gcli_31_flash_smoke_v2.db
知识图谱项目/outputs/dafeng_schema_gcli_31_flash_smoke_v2/reports/quality_report.html
```

Validation summary for the 3.1 flash smoke:

```text
Validation OK
chapters=1, characters=1, organizations=3, relationships=1, evidence=6, review_queue=6
```

SQLite smoke for `许平志` passed with one relationship and two evidence records.
