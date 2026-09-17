## Context
The current implementation has a universal core schema and a placeholder extension schema. LLM content extraction already exists, but it still uses a generic extraction prompt. The requested workflow is a two-pass full-book process: first read the full text to discover the book's schema, then read again to fill content.

## Goals
- Use every parsed chapter for schema discovery; no sampling-only path.
- Keep the universal core schema stable and reusable.
- Generate a book-specific schema package that can be audited and reused.
- Make long runs resumable through per-chapter cached discovery facts.
- Support local `gemma4` with max output token configuration.

## Non-Goals
- This change does not require a full-book extraction run during tests.
- This change does not allow LLM output to mutate canonical facts without evidence gates.
- This change does not make extension fields mandatory unless the synthesized schema marks them as required.

## Data Flow
1. Parse and split the novel into chapters.
2. Pass 1: for each chapter, call the LLM to emit schema signals:
   - world systems
   - candidate entity attributes
   - relationship types
   - event types
   - evidence examples
3. Cache each raw response in `source/schema/discovery/chapter_signals/<chapter_id>.json`.
4. Normalize accepted signals into `source/schema/discovery/schema_signals.jsonl`.
5. Synthesize:
   - `source/schema/schema_discovery_report.json`
   - `source/schema/extensions/<work_slug>.schema.json`
   - `source/schema/relationship_taxonomy.json`
   - `source/schema/extraction_contract.md`
6. Consolidate: run an LLM-powered compression pass over the synthesized candidates to merge semantic duplicates, choose canonical field names or labels, and preserve a merge map.
7. Pass 2: LLM content extraction receives the frozen schema package in its prompt.

## Consolidation Output
The raw synthesized schema remains untouched. The consolidation pass writes a separate package under `source/schema/consolidated/`:
- `schema_consolidation_report.json`
- `merge_map.json`
- `extensions/<work_slug>.schema.json`
- `relationship_taxonomy.json`
- `extraction_contract.md`

The report keeps source candidate names and evidence examples so the operator can compare the curated schema against the raw discovery output.

When final output is enabled, the same consolidated result is promoted to `source/schema/final/` with additional audit artifacts:
- `final_schema_report.json`
- `coverage_audit.json`
- `critic_report.json`
- `extensions/<work_slug>.schema.json`
- `relationship_taxonomy.json`
- `extraction_contract.md`

The extraction prompt builder prefers the most audited available package: `source/schema/refined/`, then `source/schema/final/`, then `source/schema/consolidated/`, then raw discovery artifacts.

## Refinement Loop
Final schema generation is not treated as a one-shot step. The refinement workflow consumes the final schema candidate plus its audits and produces a new refined candidate:
1. Build a `schema_health_report.json` from:
   - uncovered raw candidates, especially high-evidence items;
   - critic issues grouped by severity, category, and type;
   - boolean/is-field density;
   - reference-like fields that should become relationships;
   - event-type granularity clusters.
2. Ask the LLM for structured repair operations only. Free-form prose does not mutate the schema.
3. Apply supported operations deterministically:
   - merge items;
   - add missing items;
   - drop noisy items only after an LLM drop guard confirms they are true schema noise;
   - update descriptions or directionality;
   - merge entity fields;
   - convert entity fields into relationship types;
   - attach source candidates to an existing final item.
   - detach source candidates from an incorrectly merged final item.
   - move over-specific schema candidates to the content layer when their semantics should be preserved but not kept as schema types.
4. Classify non-final raw candidates as `merged`, `converted_to_relationship`, `absorbed`, `content_layer_only`, `dropped`, `needs_review`, or `uncovered`.
5. Write `schema_quality_gates.json` so the workflow can distinguish a candidate schema from a reviewed schema.
6. Write `source/schema/refined/` artifacts and a review HTML.
7. Subsequent LLM extraction uses the refined schema package automatically when it exists.

The drop guard is intentionally generic. It receives the proposed drops, current schema candidates, deletion reasons, and evidence examples, then returns structured decisions. The deterministic code does not use book-specific keyword lists; it validates and applies the returned decision types.

The quality gate is also generic. It does not repair schema content directly; it reports whether the current refined schema is blocked by stale critic review, high-severity critic issues, high-evidence uncovered candidates, unresolved needs-review records, reference-like fields, system-style relation names, or content-layer records that must be reflected in the extraction contract.

Refinement can start from either the final package or the latest refined package. Starting from the refined package allows the workflow to consume the fresh critic report and quality gates from the previous pass, then produce another audited refined package without manual schema edits.

When quality gates remain blocked, the operator can request additional gate-repair rounds. A gate-repair round uses the current refined schema plus the gate blockers, high-severity critic issues, high-evidence uncovered candidates, needs-review records, warnings, and content-layer records as the LLM input. The LLM still returns only structured operations, and the deterministic pipeline applies those operations, resolves review records explicitly, reruns coverage, reruns critic review when requested, and writes the same refined artifacts. This makes quality improvement a repeatable workflow step instead of a manual schema patch.

This keeps the workflow auditable: the model proposes operations, the code applies only known operation types, and every refined output can be compared to the previous final candidate.

## Validation
Discovery output is not canonical graph data, but it still needs validation:
- fields must have stable snake_case names, applies_to, type, description, and evidence examples;
- evidence examples must reference source chapters;
- relationship types must be Chinese labels with directionality;
- extraction contract must mention generated entity fields, relationship types, and event categories.
