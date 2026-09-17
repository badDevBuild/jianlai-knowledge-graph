## ADDED Requirements

### Requirement: Universal Core Schema
The system SHALL define a universal core schema for long-form novel knowledge graphs that can represent canonical entities, aliases, relationships, events, chapters, evidence, and timeline entries independent of a specific novel.

#### Scenario: Core entity coverage
- **GIVEN** a new long-form novel is onboarded
- **WHEN** the truth source is initialized
- **THEN** the core schema MUST support at least `character`, `organization`, `location`, `event`, `item`, `concept`, `chapter`, and `evidence` records
- **AND** each canonical entity record MUST include a stable ID, type, canonical name, aliases, description, first seen chapter, last seen chapter, evidence references, and extension facets

#### Scenario: Core relationship coverage
- **GIVEN** extracted facts mention relationships among entities
- **WHEN** those facts are written into the truth source
- **THEN** the relationship schema MUST support at least aliasing, organization membership, event participation, ownership or usage, affinity, enmity, intimacy, mentorship, bloodline, location hierarchy, event causality, and timeline ordering
- **AND** each relationship MUST preserve direction when the relationship semantics are directional

### Requirement: Dynamic Novel Extensions
The system SHALL allow each novel to generate a novel-specific extension schema without changing the universal core schema.

#### Scenario: Genre-specific field extension
- **GIVEN** a xianxia novel requires cultivation realms and sect ranks
- **WHEN** the novel profile is generated
- **THEN** those fields MUST be declared in `source/schema/extensions/<work_slug>.schema.json`
- **AND** those fields MUST be stored under entity or event `facets`
- **AND** the core schema MUST remain reusable for a non-xianxia novel

#### Scenario: Extension validation
- **GIVEN** a canonical entity contains novel-specific facet fields
- **WHEN** the validator checks the truth source
- **THEN** it MUST validate core fields against the universal schema
- **AND** it MUST validate facet fields against the novel extension schema when one is present

### Requirement: Truth Source Folder Structure
The system SHALL use a fixed truth-source folder structure as the durable source of truth for every novel project.

#### Scenario: Source folders are initialized
- **GIVEN** a novel project slug `<work_slug>`
- **WHEN** the truth-source template is created
- **THEN** it MUST create `source/manifest.json`, `source/schema/`, `source/corpus/`, `source/extraction/`, and `source/canonical/`
- **AND** canonical records MUST be separated into entity files, aliases, relationships, evidence, and timeline files
- **AND** generated databases MUST be placed under `projections/`, not edited as canonical source files

#### Scenario: Database is only a projection
- **GIVEN** a SQLite or Neo4j artifact exists under `projections/`
- **WHEN** a canonical source file changes
- **THEN** the projection MUST be considered stale until regenerated from `source/`
- **AND** the projection manifest MUST record source hashes or equivalent freshness evidence

### Requirement: Chapter Evidence Traceability
The system SHALL require evidence-first traceability from canonical facts back to chapters and text spans.

#### Scenario: Relationship evidence
- **GIVEN** a relationship is recorded between two entities
- **WHEN** the relationship is persisted
- **THEN** it MUST reference one or more evidence records unless it is explicitly marked as inferred
- **AND** each evidence record MUST reference a chapter ID and the supporting text or text span metadata

#### Scenario: Event evidence
- **GIVEN** an event is recorded in the timeline
- **WHEN** the event is persisted
- **THEN** it MUST reference chapter evidence
- **AND** its participants MUST reference canonical entity IDs

### Requirement: SQLite Query Projection
The system SHALL generate a query-ready SQLite database from the truth-source folder for lightweight application and content workflows.

#### Scenario: SQLite export
- **GIVEN** a valid truth-source folder
- **WHEN** the SQLite exporter runs
- **THEN** it MUST create a SQLite database under `projections/sqlite/`
- **AND** the database MUST include normalized tables for works, chapters, entities, aliases, relationships, relationship evidence, events, event participants, timeline entries, and projection metadata
- **AND** the exporter MUST not require Neo4j or any frontend build output

#### Scenario: Application query support
- **GIVEN** the SQLite projection has been generated
- **WHEN** a consumer needs App, Mini Program, social content, or adaptation-assistance queries
- **THEN** the database MUST support alias lookup, entity detail lookup, relationship expansion, event chronology, location hierarchy traversal, item ownership or usage lookup, and evidence lookup

### Requirement: Optional Neo4j Export
The system SHALL provide an optional Neo4j export from the same truth-source folder without making Neo4j the source of truth.

#### Scenario: Neo4j artifacts
- **GIVEN** a valid truth-source folder
- **WHEN** the Neo4j exporter runs
- **THEN** it MUST emit importable Neo4j artifacts under `projections/neo4j/`
- **AND** it MUST map canonical entities to graph nodes, relationship taxonomy entries to graph edges, events to event nodes, and evidence to traceability nodes or properties

### Requirement: One-Week Novel Onboarding Workflow
The system SHALL document and support a one-week workflow for using the data layer with a different long-form novel.

#### Scenario: New novel data layer delivery
- **GIVEN** a different long-form novel and its chapter text are available
- **WHEN** the workflow is followed for seven days
- **THEN** the operator MUST be able to initialize the truth source, generate the novel-specific extension schema, extract and review core entities and relationships, validate evidence coverage, and generate SQLite
- **AND** the optional Neo4j export MUST be available when graph database exploration is needed
