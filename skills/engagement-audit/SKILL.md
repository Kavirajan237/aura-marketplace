---
name: engagement-audit
description: Audit computable static-page orientation and journey-friction proxies; do not infer behavior or analytics outcomes.
license: MIT
allowed-tools: [Bash, Read]
---
# Engagement Audit
## When to use
Use after a read-only crawl has saved sampled HTML. It measures deterministic document proxies, never bounce rate, intent, conversion, or real-device rendering.
## Inputs
One HTML page for orientation checks; a sampled HTML directory for journey checks.
## Prerequisites
Robots and public read-only collection are enforced by the caller. These scripts make no network requests.
## Procedure
1. Run `python scripts/orientation_scan.py <page.html> --url /path > orientation.json`.
2. Run `python scripts/journey_friction.py <html-dir> > journey.json`.
3. Send only each `twin_patch` and its sorted raw `findings` to the orchestrator.
## Gating rules
EG-001 requires both offering and next-step absence in a named viewport proxy. CSS contrast and tap-target results emit only when style dimensions/colors are computable; otherwise they are insufficient evidence. Navigation defects require sampled/sitemap counts and a locator.
## Emits
Partial `human_experience` and `check_execution` Twin fields plus stable EG findings with URL/selector-equivalent locators and counts.
## Out of scope
Analytics, live interaction, visual assertions beyond static proxies, authentication, form submission, and all writes.
