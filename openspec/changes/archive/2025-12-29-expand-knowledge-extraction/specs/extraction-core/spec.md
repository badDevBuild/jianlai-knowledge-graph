# Spec Delta: Core Extraction

## ADDED Requirements

### Requirement: Extraction Logic
The extraction pipeline MUST save individual JSON files per chapter and handle errors gracefully.

#### Scenario: Per-Chapter JSON Storage
Given the extraction pipeline runs
When it processes a chapter named `006_第1章 惊蛰.txt`
Then it MUST save the output to `data/raw/006_第1章 惊蛰.json`
And it MUST NOT append to a single monolithic file
And the JSON content MUST be a dictionary matching the defined schema

#### Scenario: Resume Logic
Given `data/raw/006_第1章 惊蛰.json` already exists
When the extraction pipeline runs
Then it MUST skip processing `006_第1章 惊蛰.txt`
And it MUST log that the chapter was skipped

#### Scenario: Robust JSON Parsing
Given the LLM returns JSON wrapped in markdown or with trailing text
When the pipeline parses the response
Then it MUST extract only the valid JSON substring between the first `{` and the last `}`
And it MUST handle potential parsing errors gracefully by logging an error and continuing to the next chapter
