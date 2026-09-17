# Design: Schema Quality Loop

## Context
The schema workflow currently has three main stages:

1. `discover-schema` reads every chapter and emits raw schema signals.
2. `consolidate-schema` merges raw candidates into a final schema package.
3. `refine-schema` uses diagnostics, critic reports, and LLM-generated operations to repair the schema.

This structure is sound and should remain. The quality problem is that layer and content semantics are discovered too late or only as repair side effects. The workflow should carry those semantics from discovery through consolidation and refinement.

## Goals
- Keep the existing three-stage workflow.
- Make layer and content semantics first-class metadata across all stages.
- Preserve full recall: discovery hints must not delete candidates.
- Use LLMs for semantic judgment and deterministic code for execution, gates, and regression reporting.
- Use Da Feng and Xue Zhong as benchmark projects for workflow-level quality.

## Non-Goals
- Do not rewrite the extraction pipeline in this change.
- Do not hand-edit either benchmark schema as the primary solution.
- Do not introduce book-specific keyword rules.
- Do not require perfect schema output from a single LLM pass.
- Do not change canonical extraction JSON output shape in this change; content-layer semantics are carried through schema artifacts and extraction contracts first.

## Data Model
Schema candidates and consolidated items may carry the following optional metadata:

- `layer_hint`: Discovery-stage hint: `top_level`, `subsystem`, `content_detail`, or empty.
- `kind_hint`: Discovery-stage hint: `world_system`, `entity_field`, `relationship_type`, `event_type`, `content_layer`, or empty.
- `parent_hint`: Discovery-stage parent system suggestion.
- `layer`: Consolidated/refined decision: `top_level`, `subsystem`, or `content_detail`.
- `parent_name`: Required when `layer` is `subsystem` or when a content-layer record attaches to a schema item.
- `content_type`: Content-layer classification such as skill, technique, custom, title, object_detail, social_detail, or event_detail.
- `direction_contract`: Required for directed relationship types. It is an object with `source_role`, `target_role`, and `text`.

Content-layer records use one stable shape across consolidation and refinement:

- `category`: original source category.
- `name`: original candidate name or field key.
- `target_category`: schema category or `content_layer`.
- `target`: parent schema item, field key, or content-layer target.
- `content_type`: coarse content type; the first implementation may keep this as `unspecified`.
- `reason`: why this candidate is not a top-level schema item.
- `source_ids`, `source_names`, `evidence_examples`: audit trace.

## Stage Changes

### Discovery
Discovery prompts ask the LLM to emit layer/kind/parent hints. Normalization preserves hints if present, but must not reject candidates solely because hints are missing or inconsistent.

### Consolidation
Consolidation prompts and normalizers carry layer metadata. The LLM may place candidates into top-level schema items, attach them as subsystems, or move them to content-layer records. Consolidation still writes source IDs, source names, merge maps, dropped records, coverage audit, and review HTML.

### Refinement
Refinement quality gates validate layered schema structure and source absorption. Gate repair may emit structured operations such as `assign_layer`, `attach_subsystem`, `move_to_content_layer`, `add_direction_contract`, and `attach_sources`. Deterministic handlers apply only supported operations and recompute coverage and gates after each repair round.

### Benchmark
A schema benchmark command reads one or more projects and writes a report comparing:

- quality status
- coverage
- high critic issue count
- top-level world system count
- subsystem/content-layer count
- high-evidence uncovered count
- needs-review count
- relation direction-contract failures
- schema count deltas
- coverage status counts, including dropped/content-layer/subsystem outcomes

Top-level world-system inflation is a benchmark metric and warning in the first implementation, not a hard blocker by default. Missing subsystem parents, missing content-layer targets, missing directed relationship contracts, high critic issues, high-evidence uncovered candidates, and needs-review records remain blockers.

## Risks
- Layer metadata can create false precision if the LLM guesses. Mitigation: discovery emits hints only; consolidation/refinement decide.
- Content layer can become a dumping ground. Mitigation: content-layer records must appear in extraction contracts and benchmark metrics.
- Additional gates may block more schemas initially. Mitigation: benchmark output should show which blockers are structural and which are semantic.
