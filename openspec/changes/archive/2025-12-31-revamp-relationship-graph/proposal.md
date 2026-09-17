# Change: Revamp Relationship Graph

## Why
The current relationship graph page is a static, non-interactive demo that only displays a hardcoded subset (top 10) of characters in a simple circle. It lacks the ability to visualize the complex, clustered social networks of "Sword Coming" (剑来), making it difficult for users to explore the rich connections between characters, factions, and events.

## What Changes
- **Replace** the custom SVG implementation with `d3-force` (D3.js) for a physics-based force-directed graph.
- **Implement** dynamic data loading to support larger datasets (50-100+ core nodes initially, expandable).
- **Add** advanced interactions: Zoom/Pan, Node Dragging, Hover Highlighting (neighbors), and Click-to-Select.
- **Improve** visual hierarchy: Node size based on connection count/importance, edge thickness based on relationship strength.
- **Add** a side panel (overlay) for selected node details and quick actions.

## Impact
- **Affected Specs**: `visualization-graph` (New Capability)
- **Affected Code**: `frontend/pages/Characters.tsx` (Logic replacement), `frontend/package.json` (New dependencies: `d3`, `d3-force`, etc.)
