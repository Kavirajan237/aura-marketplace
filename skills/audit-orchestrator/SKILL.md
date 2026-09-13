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
## Live URL protocol
The entrypoint accepts a public `http` or `https` URL, or a local HTML artifact directory. For a live URL it validates DNS before every request and redirect, rejects loopback/private/link-local/metadata destinations, uses GET only, obeys robots.txt, stays on origin, caps pages and response bytes, and writes a single local crawl cache under the output directory. All four auditors then read that cache; they never fetch independently. Default extended corroboration remains disabled.
## Procedure
1. Run `python scripts/run_audit.py https://example.com --out audit-output --seed 0`.
2. Submit `report.json` and `report.md`; validate with `python scripts/validate_report.py <report.json>`.
## Gating rules
Every final finding needs a URL/selector-like locator and a count. Otherwise it becomes insufficient evidence. Runtime is capped at five minutes.
## Safety
The live crawl work directory is local and contains only AURA-created HTML artifacts and its manifest. The crawler uses GET requests only, respects robots.txt, checks public DNS on every redirect, and never sends cookies, credentials, forms, or analytics events.
## Emits
Full AI Brand Twin plus validated JSON and Markdown reports.
## Out of scope
Site writes, authentication, analytics, and external corroboration by default. Read [references/live-audit-protocol.md](references/live-audit-protocol.md) when auditing a live URL.
