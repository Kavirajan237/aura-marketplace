# Crawl/render gating rules

## CG-002: JavaScript render gap

Emit a **high** render-gap finding only when all conditions below are proven from the sampled evidence:

1. The missing content is semantically important: price, availability, specification, contact details, hours, shipping, or returns.
2. The content is absent from raw HTML and present after the deterministic rendered representation.
3. The page is client-rendered: no SSR/prerender marker is detected (`__NEXT_DATA__`, `window.__NUXT__`, `serverRendered`, or explicit prerender hint).
4. No equivalent normalized text exists elsewhere in the crawl sample.

If conditions 1–3 hold but condition 4 cannot be established, emit `medium` with an insufficiency note. If only condition 1 plus a partial rendering signal holds, emit `informational` only when the locator and counts are concrete. Otherwise emit nothing. A fetch failure, blocked route, or missing rendering capability is insufficient evidence, never a render-gap defect.

All crawler checks must refuse robots-disallowed URLs, obey the configured page cap and request timeout, use only GET/HEAD, and record every skip as `insufficient_evidence` or `checked_and_clean` as appropriate.
