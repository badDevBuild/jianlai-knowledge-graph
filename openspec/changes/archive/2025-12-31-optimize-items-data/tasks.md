# Implementation Tasks

## Infrastructure
- [x] Create `item_normalizer.py` with initial rule sets (Mappings & Blocklist).
- [x] Implement `step1_aggregate.py` for normalization logic.
- [x] Implement `step2_ai_process.py` with Gemini Integrations.
    - [x] Optimize Batch Size (500) and Payload format.
- [x] Implement `step3_finalize.py` for data merging.

## Verification
- [ ] Run full pipeline on production data (2400+ items).
    - [x] Step 1
    - [x] Step 2
    - [x] Step 3
- [x] Verify `items_cleaned.json` schema validity.
- [x] Verify "Output Token Limit" issues are resolved.

## Integration
- [x] Update frontend `dataTypes.ts` to include `ItemGrade` and `ItemStatus`.
- [x] Update `Compendium.tsx` to render new attributes.
