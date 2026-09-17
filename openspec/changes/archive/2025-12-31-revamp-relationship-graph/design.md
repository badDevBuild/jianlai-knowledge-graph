## Context
The project processes novel text into structured relationship data (`relations_clean.json`). Users need a way to explore this data visually. The current implementation is a placeholder. D3.js is the industry standard for custom data visualization and offers the flexibility needed for a "social network" style graph where clustering (e.g., factions) is important.

## Goals / Non-Goals
- **Goals**:
    - Visualize "Sword Coming" character relationships as a force-directed graph.
    - Auto-cluster characters by connection density (implicitly revealing factions).
    - Smooth, 60fps interaction (Zoom, Pan, Drag).
    - Clear visual distinction of relationship types and strengths.
- **Non-Goals**:
    - Full WebGL rendering (Canvas/SVG is sufficient for <500 visible nodes).
    - 3D visualization (2D is clearer for reading text labels).
    - Real-time editing of relationships by the user (Read-only view).

## Decisions
- **Decision**: Use `d3-force` engine with SVG rendering.
    - **Rationale**: SVG allows CSS styling, easy text rendering, and accessibility better than Canvas for this scale (<1000 elements). `d3-force` provides the physics simulation needed for clustering.
- **Decision**: Client-side computation.
    - **Rationale**: The dataset size (few MBs JSON) is small enough to process in the browser, avoiding complex backend graph serving logic.

## Risks / Trade-offs
- **Risk**: Performance with too many nodes.
    - **Mitigation**: Implement a "Focus Mode" or limit initial render to top 100 characters, allowing expansion on demand.
- **Risk**: Label clutter.
    - **Mitigation**: Only show labels for high-importance nodes or on hover/zoom.

## Open Questions
- None.
