## ADDED Requirements

### Requirement: Force-Directed Visualization
The system SHALL render character relationships using a physics-based force-directed graph layout to naturally reveal clusters and connection densities.

#### Scenario: Auto-clustering
- **WHEN** the graph loads with character data
- **THEN** characters with many mutual connections (e.g., same faction) naturally group together due to link forces.

### Requirement: Graph Interaction
The system SHALL provide standard graph interactions including Zoom, Pan, and Node Dragging.

#### Scenario: Zooming
- **WHEN** the user scrolls the mouse wheel or pinches the trackpad
- **THEN** the graph view zooms in/out centered on the cursor.

#### Scenario: Dragging
- **WHEN** the user clicks and drags a character node
- **THEN** the node follows the cursor, and the physics simulation updates to accommodate the new position (elastic tether).

### Requirement: Contextual Highlighting
The system SHALL visually emphasize the direct connections of a focused entity.

#### Scenario: Hover Highlighting
- **WHEN** the user hovers over a character node (e.g., "Chen Pingan")
- **THEN** that node and its direct neighbors remain opaque, while all unrelated nodes and links fade to low opacity.
