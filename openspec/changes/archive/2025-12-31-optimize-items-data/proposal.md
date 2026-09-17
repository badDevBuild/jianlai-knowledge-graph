# Proposal: Optimize Item Data Pipeline

## Summary
Establish a comprehensive data cleaning pipeline for "Item" (物品) entities in the knowledge base. This change transforms raw, fragmented item mentions into standardized, high-quality records with canonical names, aggregated descriptions, and unified attributes (grade, type, status).

## Problem Statement
The current `items.json` contains:
1.  **Duplicate Entities**: Same item appears under multiple names (e.g., "养剑葫" vs "姜壶").
2.  **Inconsistent Attributes**: Types are chaotic (e.g., "兵器" vs "武器"), grades are missing.
3.  **Low Quality Data**: Descriptions are fragmented across chapters, lacking a holistic view.

## Goals
1.  **Deduplication**: Merge synonyms into canonical entities.
2.  **Standardization**: Enforce strict type/grade enums.
3.  **Enrichment**: Use AI to synthesize comprehensive descriptions and extract ownership history.
4.  **Integration**: Seamlessly serve cleaned data to the Frontend.

## Scope
-   **Backend**: 3-step Python pipeline (`step1_aggregate.py`, `step2_ai_process.py`, `step3_finalize.py`).
-   **Frontend**: Updates to `Compendium.tsx` and `dataTypes.ts` (Items View).
-   **Data**: Transformation of `items.json` -> `items_cleaned.json`.
