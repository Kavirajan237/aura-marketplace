---
name: crawl-render-audit
description: Read-only deterministic crawlability, rendering, and structured-data audit.
license: MIT
allowed-tools: [Bash, Read]
---
# Crawl & Render Audit
## When to use
Use for public crawl artifacts before other audits.
## Inputs
URL or local fixture directory.
## Prerequisites
Robots-compliant GET-only collection.
## Procedure
1. Run `python scripts/crawl.py <target>`.
2. Run render and structured-data scripts on cached HTML.
## Gating rules
CG-002 follows `references/gating-rules.md`.
## Emits
Machine-readable Twin patch and stable CG findings.
## Out of scope
Writes, login, and external APIs.
