# AURA — AI Understanding & Resonance Architect

AURA is a deterministic, recommend-only marketplace that audits a public website in two linked chains: AI visibility (`Reach → Read → Understand → Verify → Trust → Quote → Cite`) and human engagement (`Orient → Understand → Engage → Act → Retain`). Its default path uses only public, read-only HTTP requests and respects `robots.txt` in code.

## Skills

- `audit-orchestrator` is the sole entrypoint; it runs the shared crawl, merges patches into the AI Brand Twin, clusters duplicate findings, prioritizes evidence-backed actions, and validates the report.
- `crawl-render-audit` checks whether machines can reach and read pages, including robots, metadata, rendering gaps, and valid structured data.
- `entity-fact-audit` checks whether machines can identify the brand, extract stable facts, and find complete intent anchor pages.
- `trust-freshness-audit` checks whether claims are consistent, current, sourced, and resilient across the site.
- `engagement-audit` checks documented, computable proxies for orientation and journey friction; it never claims to measure intent or bounce rate.

## Composition contract

Each non-entrypoint skill emits only `{ "twin_patch": {...}, "findings": [...] }`. The orchestrator is the only writer of the full AI Brand Twin and final report. Every finding must name a stable check ID, chain link, concrete locator, and evidence count. Default runs never use external AI/search APIs; `--extended` is opt-in and must declare unavailable corroboration honestly.

## Safety and determinism

The marketplace performs GET/HEAD requests only, enforces robots, page caps, concurrency, timeouts, and a five-minute budget. Given the same input and seed it deterministically sorts all crawl targets, patches, and findings; `audited_at` is the sole time-varying field.

## Run and verify

Run a fixture audit with `python skills/audit-orchestrator/scripts/run_audit.py fixtures/broken-spa --out evidence/sample-run`. For a live, public site, run `python skills/audit-orchestrator/scripts/run_audit.py https://example.com --out evidence/live-run --max-pages 30 --timeout 10`. The live protocol validates every target and redirect against non-public networks, honours robots.txt, and saves the one shared crawl under `evidence/live-run/.aura-crawl/` before every auditor reads it. Validate a report with `python skills/audit-orchestrator/scripts/validate_report.py evidence/sample-run/report.json`. Run the offline suite and deterministic package checks with `python scripts/selfcheck.py`.

## Counterfactuals and research

`scripts/simulate_fix.py` changes only a local HTML copy and accepts a fix only when the relevant check flips. The current research rationale is intentionally conservative and is documented in `evidence/field-research.md`: default reports do not claim external corroboration without `--extended` evidence.
