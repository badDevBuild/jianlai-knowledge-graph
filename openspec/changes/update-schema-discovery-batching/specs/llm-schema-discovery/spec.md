## ADDED Requirements

### Requirement: Batched Schema Discovery
The system SHALL support grouping multiple parsed chapters into one schema discovery LLM call.

#### Scenario: Batch discovery respects size and character caps
- **GIVEN** a novel has multiple parsed chapters
- **AND** the operator configures `discovery_batch_size` and `discovery_batch_max_chars`
- **WHEN** schema discovery builds LLM inputs
- **THEN** each batch MUST contain no more than `discovery_batch_size` chapters
- **AND** each batch SHOULD remain at or below `discovery_batch_max_chars` unless a single chapter exceeds the cap
- **AND** an oversized single chapter MUST form its own batch.

#### Scenario: Batch discovery preserves evidence locations
- **GIVEN** a schema discovery batch contains multiple chapters
- **WHEN** the LLM emits schema candidates
- **THEN** every accepted evidence example MUST include `chapter_id`, `chapter_title`, and `quote`
- **AND** discovery MUST reject evidence examples whose `chapter_id` is not in the current batch
- **AND** synthesized schema candidates MUST preserve the evidence examples.

#### Scenario: Batch discovery cache is parameterized
- **GIVEN** schema discovery runs with batched mode enabled
- **WHEN** a batch response is written to cache
- **THEN** the cache path MUST include the batch size and max character settings
- **AND** rerunning with different batch settings MUST NOT reuse incompatible batch responses.

#### Scenario: Batch discovery falls back on failures
- **GIVEN** a batched discovery call fails or returns unusable data
- **WHEN** the batch contains more than one chapter
- **THEN** discovery MUST retry smaller batches or single-chapter calls
- **AND** if a single-chapter retry fails, discovery MUST record the error and continue processing remaining chapters.

### Requirement: Single-Chapter Discovery Compatibility
The system SHALL preserve the existing single-chapter schema discovery behavior when batched discovery is not requested.

#### Scenario: Default discovery remains chapter-based
- **GIVEN** the operator runs schema discovery without batch options
- **WHEN** schema discovery processes the novel
- **THEN** it MUST call or reuse cache per chapter as before
- **AND** it MUST write `source/schema/discovery/schema_signals.jsonl`
- **AND** it MUST synthesize the same schema package artifact set.
