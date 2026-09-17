# api-search-index Specification

## Purpose
TBD - created by archiving change build-knowledge-base. Update Purpose after archive.
## Requirements
### Requirement: Search Index Generation
The builder MUST generate a lightweight inverted, key-value index for client-side search.

#### Scenario: Index Creation
Given entities "Chen Ping'an" (Character) and "Great Wall" (Location)
When building the index
Then `search_index.json` MUST contain keys "Chen Ping'an" and "Great Wall" pointing to their respective IDs/Types

