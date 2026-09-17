# Spec Delta: Timeline Construction

## ADDED Requirements

### Requirement: Event Sequencing
The builder MUST organize all extracted events into a chronological timeline.

#### Scenario: Timeline Generation
Given multiple "Event" objects extracted from Chapter 1, 2, and 3
When the timeline is built
Then it MUST output a `timeline.json` list sorted by chapter index
And each event MUST carry a reference to its source chapter filename
