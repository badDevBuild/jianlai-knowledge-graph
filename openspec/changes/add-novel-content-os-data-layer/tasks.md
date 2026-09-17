## 1. Specification and Templates
- [x] 1.1 Create the generic schema documentation for entities, relationships, events, evidence, and dynamic novel extensions.
- [x] 1.2 Create JSON Schema files for the core truth-source records.
- [x] 1.3 Create the fixed truth-source folder template under a reusable project/template path.
- [x] 1.4 Document the one-week workflow for adapting the pipeline to a new long-form novel.

## 2. Validation
- [x] 2.1 Add a small fixture novel truth source that exercises all required core entity and relationship types.
- [x] 2.2 Implement a truth-source validator for JSON schema conformance and required folder presence.
- [x] 2.3 Extend validation to check referential integrity across entities, aliases, relationships, events, evidence, chapters, and timeline entries.
- [x] 2.4 Add verification commands and expected outputs to the workflow documentation.

## 3. SQLite Projection
- [x] 3.1 Implement a SQLite exporter that reads only the truth-source folder.
- [x] 3.2 Create normalized tables and indexes for App / Mini Program queries, social content generation, and adaptation assistance.
- [x] 3.3 Add smoke queries covering entity lookup, alias lookup, relationship expansion, event chronology, evidence lookup, and chapter traceability.
- [x] 3.4 Write a projection manifest containing schema version, source hashes, generated time, and command metadata.

## 4. Optional Neo4j Projection
- [ ] 4.1 Implement a Neo4j CSV/Cypher exporter that reads only the truth-source folder.
- [ ] 4.2 Map core entity types to labels and relationship taxonomy entries to graph edge types.
- [ ] 4.3 Include evidence and chapter traceability in the graph export.
- [ ] 4.4 Document import commands and verification queries.

## 5. 《剑来》 Example Mapping
- [x] 5.1 Map existing `data/build` and `data/raw` outputs into the generic truth-source template as an example.
- [x] 5.2 Verify the example includes characters, organizations/factions, locations, events, items, concepts, chapter evidence, aliases, and core relationships.
- [x] 5.3 Generate SQLite projection from the example and run smoke queries.
- [ ] 5.4 Generate optional Neo4j export artifacts from the example.

## 6. Completion Audit
- [x] 6.1 Build a prompt-to-artifact checklist for every explicit requirement in the user objective.
- [x] 6.2 Verify each checklist item against real files, command output, and query results.
- [x] 6.3 Record any gaps before claiming the objective is complete.
