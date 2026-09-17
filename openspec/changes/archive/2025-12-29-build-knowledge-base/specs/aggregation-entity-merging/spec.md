# Spec Delta: Entity Merging

## ADDED Requirements

### Requirement: Character Aggregation
The builder script MUST aggregate character attributes from multiple chapter files into a single profile.

#### Scenario: Cultivation History Tracking
Given a character "Chen Ping'an" has cultivation "" in Chapter 1 and "Tier 1" in Chapter 100
When the builder processes the data
Then the output `characters.json` MUST contain a `cultivation_log` array recording both states with their respective chapters

#### Scenario: Alias Merging
Given "Chen Ping'an" is extracted with alias "Mud Bottle Alley Boy" in Chapter 5
When aggregating
Then the global entry for "Chen Ping'an" MUST include "Mud Bottle Alley Boy" in its `aliases` list

### Requirement: Item Ownership Tracking
The system MUST track item ownership changes across the timeline and merge item descriptions.

#### Scenario: Ownership Log
Given "Sword X" is owned by "User A" in Chapter 10 and "User B" in Chapter 20
When aggregating items
Then the item entry MUST record the ownership change event in `ownership_log`

### Requirement: Location and Faction Merging
The system MUST merge descriptions and hierarchy for Locations and Factions.

#### Scenario: Location Hierarchy merging
Given "Old Dragon City" is described as children of "Bottle Continent" in separate chapters
When aggregating
Then the Location entry MUST reflect this parent relationship

### Requirement: Relation and Quote Aggregation
The system MUST merge relationship evidence and link quotes to their speakers.

#### Scenario: Relation merging
Given Character A and B have a relationship in multiple chapters
When aggregating
Then the `relations` object MUST accumulate all evidence clips and store the maximum `strength` observed

#### Scenario: Quote Linking
Given a quote is attributed to "Chen Ping'an"
When processing
Then the quote MUST be added to Chen Ping'an's `quotes` list in their profile
