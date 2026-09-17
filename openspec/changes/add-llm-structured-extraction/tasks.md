## 1. Specification
- [x] 1.1 Add OpenSpec proposal, design, tasks, and delta spec for evidence-gated LLM extraction.
- [x] 1.2 Validate the OpenSpec change in strict mode.

## 2. Tests
- [x] 2.1 Add fake-provider tests for accepted LLM entities, relationships, events, and evidence.
- [x] 2.2 Add rejection tests for hallucinated evidence and unresolved relationship endpoints.
- [x] 2.3 Add CLI-level coverage for selecting the LLM extractor without a live endpoint.

## 3. Implementation
- [x] 3.1 Add provider interfaces and local Gemini-compatible provider with robust JSON extraction.
- [x] 3.2 Add `LLMStructuredExtractor` with deterministic evidence verification and review queue output.
- [x] 3.3 Wire `run_pipeline` and CLI flags for `--extractor llm`, endpoint, model, API key, and timeout.
- [x] 3.4 Persist per-chapter raw LLM facts and review queue records under `source/extraction/`.
- [x] 3.5 Extend validation to independently reject evidence quotes that do not appear in chapter text.
- [x] 3.6 Reuse cached per-chapter LLM facts when rerunning the same project.

## 4. Inspection and Documentation
- [x] 4.1 Update the quality report to show extractor mode and accepted/rejected counts.
- [x] 4.2 Document the LLM command path, local endpoint defaults, and review queue workflow.

## 5. Verification
- [x] 5.1 Run the unit test suite.
- [x] 5.2 Run static compile checks for the package.
- [x] 5.3 Run a live local LLM smoke extraction and validate the generated truth source.
