---
name: audit-orchestrator
description: Run the deterministic AURA website audit entrypoint and compose four read-only skill patches into validated reports.
license: MIT
allowed-tools: [Bash, Read]
---
# AURA Audit Orchestrator
## When to use
Use as the sole marketplace entrypoint for a public-site audit.
## Inputs
A URL or local crawl artifact directory, output directory, and deterministic seed.
## Prerequisites
Use only read-only crawl artifacts. Default extended corroboration remains disabled.
## Procedure
1. Run `python scripts/run_audit.py <target> --out <output> --seed 0`.
2. Submit `report.json` and `report.md`; validate with `python scripts/validate_report.py <report.json>`.
## Gating rules
Every final finding needs a URL/selector-like locator and a count. Otherwise it becomes insufficient evidence. Runtime is capped at five minutes.
## Emits
Full AI Brand Twin plus validated JSON and Markdown reports.
## Out of scope
Site writes, authentication, analytics, and external corroboration by default.
