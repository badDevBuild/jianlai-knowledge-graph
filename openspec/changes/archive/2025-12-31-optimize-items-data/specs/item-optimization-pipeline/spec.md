# Spec Delta: Item Optimization Pipeline

## ADDED Requirements

### Requirement: Rule-Based Normalization
The system MUST perform rule-based normalization on raw item names before storage.

#### Scenario: Synonym Merging
Given a raw item named "姜壶" and a mapping rule `{"姜壶": "养剑葫"}`,
When the normalization process runs,
Then the item data MUST be aggregated under the canonical key "养剑葫".

#### Scenario: Generic Filtering
Given a raw item named "长剑" effectively representing a generic noun,
When the validation process runs,
Then the item MUST be excluded from the final dataset.

### Requirement: AI Attribute Enrichment
The system MUST utilize LLM to enrich item metadata that is implicit in the text.

#### Scenario: Grade Classification
Given an item description implying it is a "Semi-Celestial Weapon" (半仙兵),
When the AI process runs,
Then the `grade` field MUST be set to "半仙兵".

#### Scenario: Status Tracking
Given an item that was destroyed in the story,
When the AI process runs,
Then the `status` field MUST be set to "损毁".

### Requirement: Batch Processing Efficiency
The AI processing module MUST support batched execution to handle large datasets (>2000 items) within reasonable time (<10 mins).

#### Scenario: Batch Execution
Given a dataset of 2500 items,
When processed with a batch size of 500,
Then the operation MUST complete successfully without API `400` errors or token truncation.
