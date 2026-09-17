# Tasks

## 1. Design & Protocol
- [x] Create `proposal.md` and `design.md` covering new schema
- [x] Validated proposal with User <!-- id: 10 -->

## 2. Implementation (Extraction Pipeline)
- [ ] Update Prompt Template in `extract_pipeline.py` (or equivalent config) <!-- id: 11 -->
  - [ ] Add `cultivation` object structure
  - [ ] Add `relation.type` Enum
  - [ ] Add `events.location` field
  - [ ] Inject Dynamic Context (Active Characters, World Events)
- [ ] Implement `unidentified_figures` buffer logic <!-- id: 18 -->
- [ ] Implement `ContextManager` for rolling window state <!-- id: 19 -->
- [ ] Run test extraction on Chapter 6 (Sample) <!-- id: 12 -->
- [ ] Verify JSON output matches new schema <!-- id: 13 -->

## 3. Implementation (Data Processing)
- [ ] Update `process_data.py` (if aggregation logic exists) to handle new fields <!-- id: 14 -->
- [ ] Implement `backtrack_resolver.py` for Identity Reveal handling <!-- id: 20 -->
- [ ] Re-run batch extraction (User initiated) <!-- id: 15 -->

## 4. Documentation
- [x] Update `openspec/specs/extraction-core/spec.md` with new requirements <!-- id: 16 -->
