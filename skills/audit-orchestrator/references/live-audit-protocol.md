# Live audit protocol

Run one deterministic, read-only crawl per audit. The crawler accepts only public HTTP(S) targets, resolves DNS before every request and redirect, and fails closed if any resolved address is not globally routable. It sends no credentials or cookies, performs GET requests only, follows at most five validated redirects, honours robots.txt, remains on the starting origin, and limits each response to 2 MB.

Progress is emitted to stderr as `[AURA]` stage messages, so stdout remains suitable for structured output. Live HTML is saved in `<out>/.aura-crawl/pages`; this is the sole input to every downstream auditor. The cache is evidence, not a publishing target.

Use `--max-pages`, `--timeout`, `--delay`, and `--budget-seconds` to set bounded execution. If the crawl yields no readable pages, the report must contain `insufficient_evidence`, not fabricated defects. Do not enable external corroboration unless an operator explicitly requests it.
