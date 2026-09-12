---
name: entity-fact-audit
description: Audit machine-extractable brand identity, facts, structural ambiguity, and intent anchor pages from read-only crawl artifacts.
license: MIT
allowed-tools:
  - Bash
  - Read
---

# Entity & Fact Audit

## When to use

Use after a compliant crawl has supplied public HTML artifacts. Use it to assess whether a machine can identify a brand, quote its basic facts, and resolve core intents to a canonical page. Do not use it for open-web corroboration, freshness, engagement, or any site mutation.

## Inputs

- A directory of sampled HTML files, usually the orchestrator's shared crawl cache.
- Stable local relative paths for evidence locators.

## Prerequisites

The caller must enforce robots, caps, and public read-only collection before this skill runs. The scripts perform no HTTP requests and never authenticate or submit data.

## Procedure

1. Run `python scripts/extract_facts.py <html-dir> > entity-fact.json`.
2. Treat `twin_patch` as a partial AI Brand Twin patch; retain raw `findings` unchanged for the orchestrator.
3. Run `python scripts/entity_disambiguation.py --name "<name>" <html-files>` only to inspect structural signals in isolation.
4. Run `python scripts/anchor_page.py <html-dir>` to inspect detected intent coverage independently.
5. Preserve sorted output exactly. Pass unavailable inputs through as `insufficient_evidence`; do not infer missing facts.

## Gating rules

- Entity collision risk is structural only: a common single-word name, missing `sameAs`, and no distinguishing one-liner qualifier. It never asserts a real-world name collision.
- An anchor-page finding requires two or more partial sampled pages and no page covering all required signal groups for that intent.
- Missing `llms.txt` is a proactive opportunity, never a defect or finding.
- Every emitted finding has a stable `EF-###` ID, count, and local URL locator.

## Emits

`{ "twin_patch": { "identity", "facts", "quoteable_facts", "gaps", "check_execution" }, "findings": [...] }`.

Facts include source URLs and normalized values. The orchestrator assigns final `F-###` IDs after it clusters findings; this skill intentionally leaves `identity.evidence_refs` empty.

## Out of scope

Cross-web search, verifying social profiles, fact-conflict severity, freshness, renders, scores, and all writes to an audited site.
