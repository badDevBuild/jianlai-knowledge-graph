# Generic Novel Content OS Data Layer Design

## Context
The current project already extracts 《剑来》 chapter JSON, merges entities, normalizes names, and compiles frontend JSON. That pipeline proves the value of the data, but its persistent structures are tied to one novel and one frontend. The new architecture treats a novel's structured knowledge as a truth source that can be projected into SQLite, Neo4j, static JSON, or downstream generation prompts.

## Goals / Non-Goals
- Goals: fix the universal core schema, fix the truth-source folder structure, support novel-specific extensions, and generate SQLite plus optional Neo4j outputs from the truth source.
- Goals: preserve evidence-first extraction so every entity fact and relationship can point back to chapters and text spans.
- Goals: support at least characters, organizations/factions, locations, events, items, setting concepts, chapters, aliases, ownership/usage, participation, membership, affinity/enmity/intimacy, mentorship, bloodline, location hierarchy, event causality, and timeline relationships.
- Non-Goals: automatically solve perfect entity resolution for every genre in the first version.
- Non-Goals: make Neo4j the source of truth.
- Non-Goals: replace the existing Taro frontend in this change.

## Architecture
The canonical project layout is `novel-os/<work_slug>/source/`. That folder stores stable JSONL/JSON files for corpus metadata, chapters, canonical entities, relationships, evidence, events, timeline entries, extraction batches, and schema extensions. Generated outputs live under `novel-os/<work_slug>/projections/` and are safe to delete and rebuild.

The universal schema is deliberately typed but extensible. Every entity has a stable `entity_id`, `entity_type`, `canonical_name`, `aliases`, `description`, `facets`, `first_seen_chapter_id`, `last_seen_chapter_id`, and `evidence_ids`. Novel-specific fields live under `facets` and are governed by the generated `schema/extensions/<work_slug>.schema.json`, so xianxia cultivation, detective clues, royal titles, or sci-fi technology can be added without changing the core schema.

Relationships use a stable relationship taxonomy plus `relationship_type`, `source_entity_id`, `target_entity_id`, optional `event_id`, `confidence`, temporal bounds, and evidence links. Event causality is represented as relationships between event records, not by ad hoc prose embedded in event descriptions.

## Truth-Source Layout
```text
novel-os/<work_slug>/
  README.md
  source/
    manifest.json
    schema/
      core.schema.json
      relationship_taxonomy.json
      entity_taxonomy.json
      extensions/<work_slug>.schema.json
    corpus/
      chapters.jsonl
      chapter_text/
    extraction/
      batches.jsonl
      chapter_facts/
      unresolved_entities.jsonl
      review_queue.jsonl
    canonical/
      entities/
        characters.jsonl
        organizations.jsonl
        locations.jsonl
        events.jsonl
        items.jsonl
        concepts.jsonl
      aliases.jsonl
      relationships.jsonl
      evidence.jsonl
      timeline.jsonl
  projections/
    sqlite/<work_slug>.db
    neo4j/
    app_json/
```

## Projection Rules
SQLite is the default query library because it is portable for local tooling, App APIs, Mini Program packaging, and social-material scripts. The exporter reads only `source/`, creates normalized tables, adds indexes for entity lookup and evidence traversal, and writes a projection manifest with schema version and source file hashes.

Neo4j export is optional and generated from the same files. It should emit CSV plus Cypher import scripts, mapping entities to labeled nodes, relationships to typed edges, and evidence chapters to traceable evidence nodes.

## Validation Strategy
The implementation should include a small fixture novel and validators that check schema conformance, referential integrity, evidence coverage, projection freshness, and query smoke tests. Passing projection commands alone is not enough; validation must prove the projections came from the truth source and preserve the core relationships.

## Risks / Trade-offs
- JSONL truth files are easier to review and regenerate than one giant database, but they require strict validators to prevent broken references.
- A universal core schema cannot encode every genre detail directly; the extension schema mechanism is required to avoid hard-coding 《剑来》 concepts into the core.
- SQLite is weaker for graph traversal than Neo4j, but it is the right default for shipping lightweight query layers.

## Migration Plan
1. Create the generic templates and validators.
2. Map existing 《剑来》 build outputs into the new truth-source structure as an example project.
3. Generate SQLite and app JSON from the new truth source.
4. Add Neo4j export artifacts as an optional command.
5. Keep existing frontend outputs until consumers are explicitly migrated.
