# Graph Visualization Specification

## Overview

This specification defines the interactive relationship graph feature for the Sword Coming mini-program using AntV F6.

---

## ADDED Requirements

### Requirement: Ego-Centric Graph Visualization

The system MUST render a force-directed graph focused on a specific character node, displaying only that character and their immediate connections (1st degree).

#### Scenario: Initial Load
- **GIVEN**: User enters the "Relationship Graph" page
- **WHEN**: The page loads
- **THEN**: The graph centers on "陈平安" (default protagonist)
- **AND**: Only Chen Ping'an and his direct connections are visible
- **AND**: A loading indicator is shown while fetching data

#### Scenario: Switch Center (Re-center)
- **GIVEN**: The graph is focused on "Character A"
- **AND**: "Character B" is visible as a neighbor
- **WHEN**: User taps on "Character B"
- **THEN**: "Character B" becomes the new center node
- **AND**: The graph updates to show "Character B" and B's neighbors
- **AND**: The layout smoothly transitions or updates

---

### Requirement: Graph Interaction

The system MUST capture user gestures for navigating the graph.

#### Scenario: Drag Canvas
- **GIVEN**: The graph is displayed
- **WHEN**: User drags on the empty area
- **THEN**: The viewport pans following the finger

#### Scenario: Zoom Canvas
- **GIVEN**: The graph is displayed
- **WHEN**: User pinches with two fingers
- **THEN**: The graph zooms in or out centered on the midpoint of fingers

---

### Requirement: Relationship Filtering (V1.1)

The system MUST allow filtering displayed relationships by type.

#### Scenario: Filter by Relationship Type
- **GIVEN**: The graph displays various relationship types (Teacher, Enemy, Friend)
- **WHEN**: User selects "Teacher" filter
- **THEN**: Only edges marked as "Teacher" (师承) are visible
- **AND**: Nodes with no visible edges are hidden or dimmed
