# Spec Delta: Cultural Data

## ADDED Requirements

### Requirement: Cultural Content
The system MUST identify and extract significant quotes and major timeline events.

#### Scenario: Quote Extraction
Given a chapter text containing significant dialogue or philosophical statements (Golden Sentences)
When the LLM extracts cultural content
Then the output `quotes` list MUST include `content` (the quote), `speaker`, and `context` (brief situation)

#### Scenario: Event Extraction
Given a chapter text describing a specific occurrence
When the LLM extracts events
Then the output `events` list MUST include `name` (summary title), `type` (e.g. Battle, Meeting), `participants` (list of names), and `description`
