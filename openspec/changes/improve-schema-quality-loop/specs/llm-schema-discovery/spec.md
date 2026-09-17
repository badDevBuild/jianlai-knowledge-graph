## ADDED Requirements

### Requirement: Discovery Semantic Hints
The system SHALL preserve semantic classification hints for raw schema candidates discovered from chapter text.

#### Scenario: Discovery keeps layer and kind hints
- **GIVEN** schema discovery processes a chapter with LLM-discovered candidates
- **WHEN** the LLM emits `layer_hint`, `kind_hint`, `parent_hint`, or `confidence` for a candidate
- **THEN** the normalized chapter signal MUST preserve those hint fields
- **AND** `source/schema/schema_discovery_report.json` MUST preserve those hint fields in the synthesized raw candidates
- **AND** the candidate MUST still include source evidence.

#### Scenario: Missing hints do not drop valid candidates
- **GIVEN** the LLM emits a candidate with a valid name or field and valid evidence
- **WHEN** the candidate has no layer, kind, parent, or confidence hint
- **THEN** discovery MUST keep the candidate
- **AND** downstream stages MUST treat the missing hint as unknown rather than noise.

### Requirement: Layered Schema Consolidation
The system SHALL consolidate raw schema candidates into a layered schema package that distinguishes top-level schema, subsystems, and content-layer records.

#### Scenario: Consolidation writes layered schema metadata
- **GIVEN** `source/schema/schema_discovery_report.json` contains raw schema candidates
- **WHEN** schema consolidation writes consolidated or final schema artifacts
- **THEN** every non-field schema item in those artifacts MUST include a `layer` value of `top_level`, `subsystem`, or `content_detail`
- **AND** any item with `layer` equal to `subsystem` MUST include a non-empty `parent_name`
- **AND** source IDs, source names, and evidence examples MUST remain auditable.

#### Scenario: Content details are retained outside top-level schema
- **GIVEN** a raw candidate is judged too specific for top-level schema but still semantically useful for extraction
- **WHEN** consolidation processes that candidate
- **THEN** the candidate MUST be represented in `content_layer_records`
- **AND** the record MUST include `category`, `name`, `target_category`, `target`, `content_type`, `reason`, `source_ids`, `source_names`, and `evidence_examples`
- **AND** the candidate MUST NOT be counted as uncovered solely because it moved to the content layer.

#### Scenario: Extraction contract exposes content layer
- **GIVEN** consolidated, final, or refined schema artifacts include content-layer records
- **WHEN** the extraction contract is rendered
- **THEN** the contract MUST include a content-layer section
- **AND** that section MUST describe how downstream extraction should preserve those details.

### Requirement: Schema Quality Gates
The system SHALL block schema packages that violate structural quality gates after refinement.

#### Scenario: Gate blocks unresolved high-risk schema issues
- **GIVEN** a refined schema package has a fresh critic report
- **WHEN** the critic report contains one or more high-severity issues
- **THEN** `schema_quality_gates.json` MUST set `quality_status` to `blocked`
- **AND** it MUST include blocker examples with category, issue type, item, reason, and suggestion.

#### Scenario: Gate blocks missing directed relationship contracts
- **GIVEN** a relationship type is marked directed
- **WHEN** its `direction_contract` is missing `source_role`, `target_role`, or `text`
- **THEN** quality gates MUST report a blocker or warning for the missing direction contract
- **AND** gate repair MUST be able to request an `add_direction_contract` operation.

#### Scenario: Gate blocks conflicting undirected relationship contracts
- **GIVEN** a relationship type is marked undirected
- **WHEN** it still carries a source/target `direction_contract`
- **THEN** quality gates MUST report a blocker for the conflicting direction contract
- **AND** gate repair MUST be able to request an `update_item` operation that clears the contract.

#### Scenario: Gate blocks missing directional event contracts
- **GIVEN** an event type description requires stable source/target roles such as actor/target, initiator/recipient, or actor/affected party
- **WHEN** its `direction_contract` is missing `source_role`, `target_role`, or `text`
- **THEN** quality gates MUST report a blocker for the missing event direction contract
- **AND** gate repair MUST be able to request an `add_direction_contract` operation for `event_types`.

#### Scenario: Gate blocks invalid schema layer structure
- **GIVEN** refined schema items include layered metadata
- **WHEN** a subsystem lacks a parent or a content-layer record lacks a downstream target
- **THEN** quality gates MUST report a blocker for the structural issue
- **AND** gate repair MUST be able to request `assign_layer`, `attach_subsystem`, `move_to_content_layer`, or `attach_sources` operations.

#### Scenario: Gate reports top-level world-system inflation
- **GIVEN** refined schema items include layered metadata
- **WHEN** top-level world systems exceed the configured benchmark threshold
- **THEN** quality gates or benchmark output MUST report the inflation as a warning or metric
- **AND** the first implementation MUST NOT block solely on this count unless explicitly configured.

#### Scenario: Gate blocks field and relationship boundary violations
- **GIVEN** an entity field stores entity-to-entity links such as member lists, leaders, social networks, romantic partners, or organization ownership
- **WHEN** the field is present in the refined schema
- **THEN** quality gates MUST flag the field as a field-as-relationship issue
- **AND** gate repair MUST be able to request conversion to a relationship or a content-layer record.

### Requirement: Deterministic Repair Operations
The system SHALL apply LLM repair suggestions only through supported deterministic operations.

#### Scenario: Layer operations are applied deterministically
- **GIVEN** an LLM repair plan contains `assign_layer`, `attach_subsystem`, `move_to_content_layer`, `update_item`, or `add_direction_contract`
- **WHEN** refinement applies the plan
- **THEN** deterministic handlers MUST update schema reports using only the structured operation payload
- **AND** the handlers MUST preserve source names, source IDs, evidence examples, merge maps, and audit records.

#### Scenario: Unsupported free-form edits are ignored
- **GIVEN** an LLM repair response contains narrative notes without supported operations
- **WHEN** refinement applies the response
- **THEN** the system MUST NOT directly mutate schema items from free-form text
- **AND** the unsupported response MUST be visible in the refinement plan or errors for audit.

### Requirement: Schema Benchmark Report
The system SHALL provide a repeatable benchmark report for comparing schema quality across projects.

#### Scenario: Benchmark compares multiple schema projects
- **GIVEN** two or more schema projects have refined schema artifacts
- **WHEN** the operator runs the schema benchmark command with those project paths
- **THEN** the system MUST read each project's refined schema report, coverage audit, critic report, and quality gates
- **AND** it MUST write a JSON benchmark report with per-project metrics and pass/fail status
- **AND** the report MUST identify missing artifacts instead of failing silently.

#### Scenario: Benchmark includes Da Feng and Xue Zhong baselines
- **GIVEN** the Da Feng and Xue Zhong schema projects exist under `outputs/`
- **WHEN** benchmark reporting runs for the current workflow
- **THEN** the report MUST include coverage ratio, coverage status counts, high critic issue count, top-level world-system count, subsystem count, content-layer count, dropped count, high-evidence uncovered count, needs-review count, and direction-contract failure count for each project
- **AND** the report MUST make regressions visible when a metric gets worse.
