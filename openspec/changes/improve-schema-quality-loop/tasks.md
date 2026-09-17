## 1. Specification and Baseline
- [x] 1.1 Review the proposal and confirm scope before implementation.
- [x] 1.2 Snapshot current Da Feng and Xue Zhong refined metrics as benchmark baselines.
- [x] 1.3 Record baseline coverage status counts, dropped counts, content-layer counts, high critic counts, and direction-contract failures.

## 2. Discovery Metadata
- [x] 2.1 Extend the discovery prompt with `layer_hint`, `kind_hint`, `parent_hint`, and `confidence`.
- [x] 2.2 Preserve discovery hints in normalized chapter signals and `schema_discovery_report.json`.
- [x] 2.3 Add tests or fixtures proving missing hints do not drop otherwise valid candidates.

## 3. Layered Consolidation
- [x] 3.1 Extend consolidation prompts and output normalization for `layer`, `parent_name`, `content_type`, and content-layer records.
- [x] 3.2 Include content-layer records and subsystem mappings in consolidated/final schema reports.
- [x] 3.3 Render layered schema and content-layer sections in extraction contracts and review HTML.
- [x] 3.4 Ensure coverage audit counts merged, attached, subsystem, and content-layer outcomes correctly.
- [x] 3.5 Add fixtures proving content-layer records use the stable `category/name/target_category/target/content_type/reason/source_ids/source_names/evidence_examples` shape.

## 4. Refinement Gates and Operations
- [x] 4.1 Add blocking quality gates for missing parent on subsystems, missing direction contracts, field-as-relation issues, content-layer contract gaps, and source absorption gaps.
- [x] 4.2 Add deterministic operation handlers for `assign_layer`, `attach_subsystem`, `add_direction_contract`, and enhanced `move_to_content_layer`.
- [x] 4.3 Update gate-repair prompts to use layered schema metadata and the new operation types.
- [x] 4.4 Recompute coverage, critic, and quality gates after every gate repair round.
- [x] 4.5 Add fixtures for each new operation and for blocked/passed gate outcomes.
- [x] 4.6 Extend direction-contract handling to directional event types.
- [x] 4.7 Block and repair undirected relationships that still carry source/target direction contracts.

## 5. Benchmark Reporting
- [x] 5.1 Add a `schema-benchmark` CLI command that accepts multiple project paths.
- [x] 5.2 Write JSON benchmark reports with per-book metrics and pass/fail status.
- [x] 5.3 Include Da Feng and Xue Zhong in the benchmark run instructions.
- [x] 5.4 Include coverage status counts and dropped/content-layer/subsystem outcomes so coverage ratio cannot hide semantic loss.
- [x] 5.5 Treat top-level world-system inflation as a benchmark warning/metric in the first implementation, not a hard blocker.

## 6. Verification
- [x] 6.1 Run OpenSpec validation.
- [x] 6.2 Run schema benchmark before and after implementation.
- [x] 6.3 Confirm both benchmark projects have zero high critic issues or document remaining blockers.
