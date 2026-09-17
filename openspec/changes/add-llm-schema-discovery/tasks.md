## 1. Specification
- [x] 1.1 Add OpenSpec proposal, design, tasks, and delta spec for full-text LLM schema discovery.
- [x] 1.2 Validate the OpenSpec change in strict mode.

## 2. Tests
- [x] 2.1 Add fake-provider tests for per-chapter schema signal extraction.
- [x] 2.2 Add synthesis tests for extension schema, relationship taxonomy, discovery report, and extraction contract.
- [x] 2.3 Add cache tests so reruns reuse chapter discovery responses.
- [x] 2.4 Add CLI parser coverage for `discover-schema`, `gemma4`, and max output tokens.

## 3. Implementation
- [x] 3.1 Add provider support for `max_output_tokens` and default `gemma4` model configuration.
- [x] 3.2 Add schema discovery prompts and extraction/synthesis module.
- [x] 3.3 Add CLI command to run schema discovery across parsed chapters.
- [x] 3.4 Feed generated schema package into second-pass LLM content extraction.
- [x] 3.5 Persist all schema discovery artifacts under `source/schema/`.

## 4. Documentation and Verification
- [x] 4.1 Document the two-pass workflow and generated schema artifacts.
- [x] 4.2 Run unit tests and compile checks.
- [x] 4.3 Record that local `gemma4` smoke was superseded by user-approved localLLM-geminicli runtime.
- [x] 4.4 Run a small real localLLM-geminicli `gemini-3.1-flash-lite-preview` two-pass smoke after gemma4 contention.
- [x] 4.5 Record completion audit with actual generated artifacts and runtime caveats.

## 5. Schema Consolidation
- [x] 5.1 Add an LLM-powered `consolidate-schema` command that reads the raw discovery report.
- [x] 5.2 Persist consolidated schema artifacts separately from the raw discovery output.
- [x] 5.3 Preserve merge maps, source candidate names, and evidence examples for audit.
- [x] 5.4 Run unit tests and OpenSpec validation.
- [x] 5.5 Add coverage audit, critic review, and `source/schema/final/` output.
- [x] 5.6 Run a real localLLM-geminicli `gemini-3.1-pro-preview` consolidation on the full schema output.

## 6. Schema Refinement Loop
- [x] 6.1 Add schema health diagnostics for coverage gaps, field shape, relationship directionality, and event granularity.
- [x] 6.2 Add LLM repair planning that emits structured operations instead of direct file edits.
- [x] 6.3 Add deterministic operation handlers and `source/schema/refined/` artifacts.
- [x] 6.4 Add CLI parser and unit tests for `refine-schema`.
- [x] 6.5 Run unit tests, compile checks, and OpenSpec validation.
- [x] 6.6 Run a real localLLM-geminicli refinement pass on the current full final schema candidate.
- [x] 6.7 Prefer refined schema artifacts for subsequent LLM extraction when available.
- [x] 6.8 Add drop guard and semantic coverage statuses for absorbed, converted, and content-layer outcomes.
- [x] 6.9 Add refined schema quality gates and include content-layer/needs-review records in the extraction contract.
- [x] 6.10 Allow schema refinement to iterate from the latest refined package.
- [x] 6.11 Add quality-gate repair rounds driven by gate blockers and explicit review resolution operations.
- [x] 6.12 Add source attach/detach repair operations that update coverage traceability and evidence.
