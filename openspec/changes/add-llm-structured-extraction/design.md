## Context
The truth-source layout and SQLite projection already exist, but the default extractor is a deterministic heuristic baseline. It treats surname-looking tokens as people and same-sentence co-occurrence as relationships, which is useful for scaffolding but too noisy for a trusted data layer.

## Goals
- Preserve the existing `source/` contract so SQLite and reports continue to work.
- Add an LLM path that is evidence-first and deterministic at the acceptance boundary.
- Make rejected LLM output inspectable, so quality work becomes a review task instead of silent data loss.
- Keep the heuristic extractor available as an offline baseline.

## Non-Goals
- This change does not guarantee perfect literary interpretation.
- This change does not add a full human review UI.
- This change does not merge cross-chapter aliases with global certainty; it creates stable canonical candidates and records evidence.

## Design
The pipeline gains an `extractor_mode` option. `heuristic` keeps the existing behavior. `llm` creates an `LLMStructuredExtractor` with an injected provider. Production CLI uses a `LocalGeminiProvider`; tests inject a fake provider.

For each chapter, the extractor sends:
- the chapter metadata and text,
- a strict JSON output schema,
- the relationship taxonomy,
- a compact existing entity index from previously accepted facts.

The LLM returns chapter-level facts. The acceptance layer is deterministic:
- every entity, relationship, and event must reference a quote;
- the quote must be found in the chapter text after whitespace normalization;
- relationships must resolve source and target entity names to accepted entities;
- malformed records are rejected.

Accepted records are normalized into the existing canonical JSONL schema. Rejected records are written as JSONL to `source/extraction/review_queue.jsonl` with the original fact, chapter ID, and rejection reason.

## Risks
- LLM output can still be incomplete; evidence gates improve precision more than recall.
- Very long chapters may need chunking later. This change keeps the chapter-level interface and can add chunking without changing canonical output.
- Local endpoint availability remains an operator concern; tests cover the extractor by injection instead of requiring a live LLM.
