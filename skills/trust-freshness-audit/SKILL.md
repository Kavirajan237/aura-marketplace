---
name: trust-freshness-audit
description: Audit internal claim consistency, freshness, sourcing, and link resilience from read-only crawl artifacts.
license: MIT
allowed-tools: [Bash, Read]
---
# Trust & Freshness Audit
## When to use
Use on a shared, compliant HTML crawl to test whether quoted facts are internally consistent and maintainable.
## Inputs
A directory of sampled HTML artifacts; `--extended` is explicit and remains unavailable unless a future approved implementation provides it.
## Prerequisites
The caller has already performed robots-compliant, public, read-only collection. Scripts never make network requests.
## Procedure
1. Run `python scripts/fact_conflict.py <html-dir> > conflicts.json`.
2. Run `python scripts/freshness_scan.py <html-dir> > freshness.json`.
3. Merge only returned Twin patches and sorted findings. Preserve the default TF-005 insufficiency entry.
## Gating rules
TF-001 requires two canonical values for the same vocabulary key. TF-003 requires exactly one sampled source. TF-007 only evaluates local sampled targets; an unavailable target is not assumed dead on the live site.
## Emits
Partial `facts`, `quoteable_facts`, `gaps`, and `check_execution` Twin fields, plus stable TF findings with counts and locators.
## Out of scope
Live verification, open-web corroboration by default, legal truth determination, authentication, and writes.
