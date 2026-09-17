## Context

Schema discovery is a first-pass LLM workflow. It should identify book-specific schema signals, not extract canonical facts. Single-chapter calls are resumable but produce weak global judgment because each request sees only local context.

Xue Zhong currently splits into 983 chapters/segments. Chapter sizes are uneven: the median is about 4,049 characters, the average is about 4,656 characters, and the maximum single chapter is about 89,917 characters. A fixed 10-chapter batch is usually reasonable but unsafe without a character cap.

## Goals

- Reduce discovery calls from hundreds to roughly one call per batch.
- Give LLM enough context to judge repeated systems, subsystems, relationship types, and event types.
- Preserve exact evidence traceability after batching.
- Keep discovery resumable through cache.
- Avoid breaking existing single-chapter tests and workflows.

## Non-Goals

- Do not change consolidation, refinement, or extraction JSON contracts in this change.
- Do not hand-edit final schema outputs.
- Do not introduce tokenizer dependencies; use character count as a simple safety proxy.

## Design

### Batch Construction

The batch builder SHALL add chapters until either:

- `batch_size` chapters are included, or
- adding the next chapter would exceed `batch_max_chars`.

If the next chapter alone exceeds `batch_max_chars`, it SHALL form a single oversized batch and record a warning.

### Prompt Shape

Batch prompts SHALL provide a list of chapter records:

- `chapter_id`
- `chapter_title`
- `text`

LLM output SHALL use `evidence_examples` with explicit `chapter_id`, `chapter_title`, and `quote`. The normalizer SHALL only keep evidence whose `chapter_id` belongs to the current batch.

### Cache

Batch cache paths SHALL include the batch parameters:

```text
source/schema/discovery/batch_signals/b<size>_m<max_chars>/batch_0001.json
```

Single-chapter cache remains unchanged.

### Fallback

If a batch LLM call fails or returns no usable object, discovery SHALL split that batch into smaller batches. If a single-chapter batch still fails, discovery SHALL record the error and continue.

Fallback should preserve successful cache results and avoid rerunning already completed batches.
