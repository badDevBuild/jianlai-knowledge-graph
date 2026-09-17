# Spec Delta: Entity Data

## ADDED Requirements

### Requirement: Entity Attributes
The system MUST extract detailed attributes for characters, items, locations, and factions based on the novel's text.

#### Scenario: Character Extraction
Given a chapter text containing character descriptions
When the LLM extracts characters
Then the output `characters` list MUST include objects with `name`, `aliases` (list), `bio`, `cultivation`, `faction`, and `tags` (list)
And `cultivation` MUST reflect the specific stage mentioned in the text (if any)

#### Scenario: Item Extraction
Given a chapter text mentioning specific named weapons or artifacts (e.g., "Sword Coming")
When the LLM extracts items
Then the output `items` list MUST include objects with `name` (e.g. "槐木剑"), `type` (e.g. "Weapon"), `owner`, `description`, and `rank` (if mentioned)

#### Scenario: Location and Faction Extraction
Given a chapter text mentioning locations or sects
When the LLM extracts data
Then the output `locations` list MUST include `name`, `type`, `description`, `parent`
And the output `factions` list MUST include `name`, `type`, `description`
