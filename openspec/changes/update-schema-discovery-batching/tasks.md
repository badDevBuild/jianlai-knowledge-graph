## 1. Spec and Design
- [x] 1.1 Create and validate OpenSpec change.
- [x] 1.2 Confirm scope remains discovery-only.

## 2. Batch Discovery Implementation
- [x] 2.1 Add batch construction with `batch_size` and `batch_max_chars`.
- [x] 2.2 Add batch prompt that includes chapter IDs, titles, and text.
- [x] 2.3 Normalize batch outputs with explicit `evidence_examples`.
- [x] 2.4 Preserve single-chapter discovery compatibility.
- [x] 2.5 Add parameterized batch cache paths.
- [x] 2.6 Add split/fallback behavior for failed batches.

## 3. CLI and Docs
- [x] 3.1 Add CLI options for batch size and max chars.
- [x] 3.2 Update implementation log with the chosen batch command.

## 4. Tests and Verification
- [x] 4.1 Add unit tests for batch grouping and max-char behavior.
- [x] 4.2 Add unit tests for batch evidence normalization.
- [x] 4.3 Add unit tests for CLI options.
- [x] 4.4 Run pytest.
- [x] 4.5 Run OpenSpec validation.
