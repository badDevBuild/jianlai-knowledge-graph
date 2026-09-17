# Tasks: Build Knowledge Base

- [x] **Setup**
    - [x] Create `data/build/` directory.

- [x] **Builder Script (`build_knowledge_base.py`)**
    - [x] **Skeleton**: Create script to iterate `data/raw/` in sorted order.
    - [x] **Entity Logic**: Implement merging of Characters, Aliases, and Factions.
    - [x] **Cultivation Logic**: Implement `cultivation_log` tracking.
    - [x] **Timeline Logic**: Aggregate events into a sorted list.
    - [x] **Index Logic**: Generate `search_index.json`.

- [x] **Validation**
    - [x] Run builder on existing extracted chapters (e.g. Chapter 6, 7).
    - [x] Verify `characters.json` correctly merges duplicate entries.
    - [x] Verify `timeline.json` ordering.
