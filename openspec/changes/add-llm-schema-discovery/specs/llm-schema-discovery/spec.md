## ADDED Requirements

### Requirement: Full-Text Schema Discovery Pass
The system SHALL provide a first-pass LLM workflow that scans every parsed chapter for schema signals before canonical content extraction.

#### Scenario: Discover schema from all parsed chapters
- **GIVEN** a novel input file and a work slug
- **WHEN** the operator runs schema discovery
- **THEN** the system MUST parse and split the novel into chapters
- **AND** it MUST call the LLM once per chapter unless a cached discovery response exists
- **AND** it MUST persist normalized chapter signals to `source/schema/discovery/schema_signals.jsonl`

### Requirement: Book-Specific Schema Synthesis
The system SHALL synthesize a book-specific schema package from all chapter schema signals.

#### Scenario: Synthesize schema package
- **GIVEN** schema signals exist for one or more chapters
- **WHEN** synthesis runs
- **THEN** the system MUST write `source/schema/schema_discovery_report.json`
- **AND** it MUST write `source/schema/extensions/<work_slug>.schema.json`
- **AND** it MUST write `source/schema/relationship_taxonomy.json`
- **AND** it MUST write `source/schema/extraction_contract.md`

### Requirement: Schema Signal Evidence
The system SHALL preserve evidence examples for generated schema fields, relationship types, and event types.

#### Scenario: Generated field has evidence
- **GIVEN** the LLM proposes a book-specific field
- **WHEN** the field is accepted into the discovery report
- **THEN** it MUST include at least one evidence example with chapter ID and quote
- **AND** the quote MUST be traceable to chapter text when available

### Requirement: Discovery Cache
The system SHALL cache per-chapter schema discovery responses for resumable full-book runs.

#### Scenario: Cached discovery response exists
- **GIVEN** `source/schema/discovery/chapter_signals/<chapter_id>.json` exists
- **WHEN** schema discovery is rerun
- **THEN** the system MUST reuse the cached raw response
- **AND** it MUST NOT call the provider for that chapter

### Requirement: Gemma4 Max Output Configuration
The system SHALL support running schema discovery with local model `gemma4` and maximum output token configuration.

#### Scenario: Operator selects gemma4
- **GIVEN** the operator runs schema discovery with model `gemma4`
- **WHEN** the local provider request is built
- **THEN** the request MUST include the configured model name
- **AND** it MUST include the configured maximum output token value when provided

### Requirement: Frozen Schema Used For Content Extraction
The system SHALL feed the generated book-specific schema package into the second-pass LLM content extraction prompt.

#### Scenario: LLM content extraction follows discovered schema
- **GIVEN** `source/schema/extraction_contract.md` exists
- **WHEN** the second-pass LLM extractor processes a chapter
- **THEN** the prompt MUST include the extraction contract
- **AND** it MUST include the generated relationship taxonomy and extension schema summary

### Requirement: LLM Schema Consolidation Pass
The system SHALL provide an LLM-powered consolidation pass that compresses the raw discovered schema into a curated book-specific schema package.

#### Scenario: Consolidate raw schema candidates
- **GIVEN** `source/schema/schema_discovery_report.json` exists
- **WHEN** the operator runs schema consolidation with an LLM provider and model
- **THEN** the system MUST read every raw world system, entity field, relationship type, and event type candidate from the discovery report
- **AND** it MUST ask the LLM to merge semantic duplicates and choose canonical schema labels or fields
- **AND** it MUST write `source/schema/consolidated/schema_consolidation_report.json`
- **AND** it MUST write `source/schema/consolidated/merge_map.json`
- **AND** it MUST write consolidated extension schema, relationship taxonomy, and extraction contract artifacts
- **AND** it MUST preserve source candidate names and evidence examples for auditability

#### Scenario: Final schema package is auditable
- **GIVEN** schema consolidation completes with final output enabled
- **WHEN** the final schema package is written
- **THEN** the system MUST write `source/schema/final/final_schema_report.json`
- **AND** it MUST write `source/schema/final/coverage_audit.json`
- **AND** it MUST write `source/schema/final/critic_report.json`
- **AND** it MUST write `reports/final_schema_review.html`
- **AND** the coverage audit MUST classify raw candidates as final, merged, dropped, or uncovered

#### Scenario: Extraction prefers final schema when refined output is absent
- **GIVEN** `source/schema/final/extraction_contract.md` exists
- **AND** `source/schema/refined/extraction_contract.md` does not exist
- **WHEN** the second-pass LLM extractor builds its schema context
- **THEN** it MUST use the final schema package before consolidated or raw schema artifacts

### Requirement: Iterative Schema Refinement Loop
The system SHALL provide a repeatable refinement workflow that improves a final schema candidate through diagnostics, LLM-generated repair operations, and audited output artifacts.

#### Scenario: Generate schema repair operations from diagnostics
- **GIVEN** `source/schema/final/final_schema_report.json`, `coverage_audit.json`, and `critic_report.json` exist
- **WHEN** the operator runs schema refinement
- **THEN** the system MUST compute a schema health report from coverage, critic issues, field shape, relationship directionality, and event granularity
- **AND** it MUST ask the LLM to return structured repair operations rather than free-form edits
- **AND** it MUST write `source/schema/refined/refinement_plan.json`
- **AND** it MUST write `source/schema/refined/schema_health_report.json`

#### Scenario: Apply repair operations without manual schema edits
- **GIVEN** a refinement plan with supported operations
- **WHEN** the system applies the plan
- **THEN** it MUST transform the schema using deterministic operation handlers
- **AND** it MUST write `source/schema/refined/refined_schema_report.json`
- **AND** it MUST write `source/schema/refined/coverage_audit.json`
- **AND** it MUST write `reports/refined_schema_review.html`
- **AND** it MUST preserve source IDs, source names, evidence examples, merge maps, and dropped records where applicable

#### Scenario: Guard dropped schema candidates
- **GIVEN** a refinement plan contains `drop_items`
- **WHEN** the system applies the plan
- **THEN** it MUST ask an LLM drop guard to distinguish true noise from candidates that should be merged, converted to relationships, absorbed into existing schema, or retained as content-layer facts
- **AND** it MUST record converted, absorbed, content-layer, needs-review, and true dropped outcomes separately
- **AND** the coverage audit MUST count converted, absorbed, and content-layer outcomes as covered rather than uncovered
- **AND** the deterministic code MUST apply only the structured decisions and MUST NOT depend on book-specific keyword lists

#### Scenario: Gate refined schema quality
- **GIVEN** refined schema artifacts have been generated
- **WHEN** the system writes the refined schema package
- **THEN** it MUST write `source/schema/refined/schema_quality_gates.json`
- **AND** the quality gates MUST classify the schema as passed, review_required, or blocked
- **AND** the gates MUST check fresh critic status, high-severity critic issues, high-evidence uncovered candidates, needs-review records, reference-like fields, system-style relation names, and content-layer records
- **AND** content-layer and needs-review records MUST be included in the refined extraction contract

#### Scenario: Iterate from refined schema
- **GIVEN** `source/schema/refined/refined_schema_report.json` exists
- **WHEN** the operator runs schema refinement with the refined base stage
- **THEN** the system MUST use the existing refined schema, critic report, coverage audit, drop guard records, and quality gates as the next refinement input
- **AND** it MUST write a new refined package through the same deterministic operation and audit pipeline

#### Scenario: Repair quality gate blockers
- **GIVEN** a refined schema candidate has quality gate blockers
- **WHEN** the operator runs schema refinement with one or more gate repair rounds
- **THEN** the system MUST pass the quality gate blockers, high-severity critic issues, high-evidence uncovered candidates, needs-review records, and current schema summary to the LLM
- **AND** the LLM MUST return structured repair operations rather than direct schema edits
- **AND** the deterministic pipeline MUST apply only supported operations, including explicit review resolution and source attach/detach operations
- **AND** it MUST recompute coverage, critic results when requested, quality gates, and refined output artifacts after every repair round

#### Scenario: Extraction prefers refined schema
- **GIVEN** `source/schema/refined/extraction_contract.md` exists
- **WHEN** the second-pass LLM extractor builds its schema context
- **THEN** it MUST use the refined schema package before final, consolidated, or raw schema artifacts
