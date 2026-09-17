## MODIFIED Requirements
### Requirement: Extraction Logic
The extraction pipeline MUST save individual JSON files per chapter, handle errors gracefully, and adhere to the Enhanced v2 Schema.

#### Scenario: Per-Chapter Rich JSON Storage
- **WHEN** the pipeline processes a chapter
- **THEN** it MUST save a JSON file to `data/raw/` with fields including `cultivation` objects, `event` locations, and `relation` types.

#### Scenario: AI-Native Normalization
- **WHEN** extraction encounters an ambiguous entity (e.g., "Da Li")
- **THEN** it MUST attempt to resolve it to the full canonical name (e.g., "Da Li Dynasty") in the `faction` field.

## ADDED Requirements
### Requirement: Dynamic Context Injection
The extraction pipeline MUST inject dynamic world state and active participant lists into the prompt context.

#### Scenario: Inference based on Active Characters
- **WHEN** the "Active Characters" list includes "Chen Pingan" but not "Song Jixin"
- **THEN** an ambiguous reference like "The young man in the alley" SHOULD be inferred as "Chen Pingan" if context matches.

### Requirement: Ambiguity Buffering
The system SHALL separate clearly identified characters from ambiguous figures into distinct output fields.

#### Scenario: Unidentified Figure
- **WHEN** the text mentions "a mysterious white-robed swordsman" without naming them
- **THEN** the output MUST place this entity in `unidentified_figures` with features and actions, NOT in `characters`.

### Requirement: Plot Link Backtracking
The system SHALL extract identity reveal events to support retroactive data correction.

#### Scenario: Identity Reveal
- **WHEN** the text reveals "The man in the bamboo hat is actually A Liang"
- **THEN** the JSON output MUST include a `plot_links` entry of type `IdentityReveal` linking the alias to the canonical name.

### Requirement: Structured Cultivation
The system SHALL extract cultivation levels as structured objects rather than free text.

#### Scenario: Cultivation Change
- **WHEN** a character breaks through a realm (e.g., "Five Realms")
- **THEN** the JSON output for `characters.cultivation` MUST contain `{"realm": "Five Realms", "stage": "..."}`.

### Requirement: Event Contextualization
The system SHALL link events to specific locations and time contexts.

#### Scenario: Battle Event
- **WHEN** a battle occurs in "Mud Bottle Alley"
- **THEN** the `events` entry MUST include `"location": "Mud Bottle Alley"` and `"type": "Battle"`.

### Requirement: Item Provenance
The system SHALL track the flow of item ownership.

#### Scenario: Gifted Item
- **WHEN** Character A gives an item to Character B
- **THEN** the `items` entry MUST record `holder: "Character B"`, `previous_holder: "Character A"`, and `action: "Gift"`.
