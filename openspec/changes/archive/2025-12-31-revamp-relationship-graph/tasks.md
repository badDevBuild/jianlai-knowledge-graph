## 1. Preparation
- [ ] 1.1 Install `d3` and `@types/d3` in frontend.
- [ ] 1.2 Create `ForceGraph` component structure in `frontend/components/ForceGraph.tsx` (or similar).

## 2. Core Implementation
- [ ] 2.1 Implement D3 simulation initialization (link, charge, center, collision forces).
- [ ] 2.2 Implement SVG rendering of nodes (circles/images) and edges (lines).
- [ ] 2.3 Add Zoom and Pan behavior using `d3-zoom`.
- [ ] 2.4 Add Drag behavior using `d3-drag`.

## 3. Data Integration
- [ ] 3.1 Refactor `RelationshipGraph` page to load full character data.
- [ ] 3.2 Transform `CharacterData` into Graph `nodes` and `links` format.
- [ ] 3.3 Implement filtering logic (e.g., "Top 50 by relations count") to prevent overcrowding.

## 4. Visuals & Interaction
- [ ] 4.1 Apply visual styles: Node size by degree, Link width by strength.
- [ ] 4.2 Implement "Hover" state: Fade out non-connected nodes.
- [ ] 4.3 Implement "Selected" state: Show Side Panel with details.

## 5. Cleanup
- [ ] 5.1 Remove old manual graph code from `frontend/pages/Characters.tsx`.
- [ ] 5.2 Verify layout on different screen sizes.
