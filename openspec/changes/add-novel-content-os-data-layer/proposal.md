# Change: Add Generic Novel Content OS Data Layer

## Why
The project currently treats the 《剑来》 dataset as the primary asset and compiles it into frontend JSON projections. To turn the work into a reusable long-form novel knowledge-graph workflow, the durable asset must become a fixed truth-source folder structure plus a universal core schema, with SQLite and Neo4j generated as replaceable projections.

## What Changes
- Define a generic long-form novel knowledge graph schema covering characters, organizations/factions, locations, events, items, setting concepts, chapters, evidence, aliases, and core relationship types.
- Define a fixed truth-source folder structure that can hold any novel's canonical entities, relationships, chapter evidence, timeline, extraction state, and novel-specific schema extensions.
- Add a dynamic novel profile mechanism so genre-specific concepts and entity facets can be generated per novel without changing the universal core schema.
- Add a SQLite projection flow for App / Mini Program querying, social content generation, and adaptation assistance.
- Add an optional Neo4j export flow that emits graph database import artifacts from the same truth source.
- Establish a one-week operating workflow for replacing 《剑来》 with another long novel and producing a query-ready data layer.

## Impact
- Affected specs: novel-content-os-data-layer
- Affected code after approval: new schema docs/templates, truth-source templates, SQLite export scripts, optional Neo4j export scripts, validation fixtures, and README workflow docs
- Existing 《剑来》 extraction and frontend data files remain source inputs or projections; they do not become the new canonical data contract.
