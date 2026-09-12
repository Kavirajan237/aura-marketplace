# AURA audit: broken-spa

Sampled 1 pages; 12 evidence-backed findings.

## F-001 — Important facts require JavaScript rendering
**Symptom:** 2/7 important fact types absent from raw HTML and present after render at /index.html: availability, price
**Cost:** This can reduce machine understanding or a human next step.
**Owner/action:** dev — Emit important facts in initial HTML.

## F-002 — First viewport lacks offering or next step
**Symptom:** 0/2 tested viewports include both at /index.html
**Cost:** This can reduce machine understanding or a human next step.
**Owner/action:** dev — Address the measurable proxy, then rerun this check.

## F-003 — No machine-extractable one-line description
**Symptom:** 0/1 sampled pages supplied a meta description or descriptive home-page sentence; sample: /index.html
**Cost:** This can reduce machine understanding or a human next step.
**Owner/action:** dev — Add one plain-language description to initial HTML and Organization markup.

## F-004 — No machine-readable entity schema detected
**Symptom:** 0/1 sampled pages expose Organization, LocalBusiness, Product, or Service markup; sample: /index.html
**Cost:** This can reduce machine understanding or a human next step.
**Owner/action:** dev — Add valid schema.org markup for the site's primary entity type.

## F-005 — No verb-like CTA in the compact first-view proxy
**Symptom:** 0/0 CTAs occur in first 300 text characters at /index.html
**Cost:** This can reduce machine understanding or a human next step.
**Owner/action:** dev — Address the measurable proxy, then rerun this check.

## F-006 — Intent page has no onward internal path
**Symptom:** 1/2 intent-bearing pages have zero onward sampled links; sample: /rendered.html
**Cost:** This can reduce machine understanding or a human next step.
**Owner/action:** dev — Add a relevant next step or canonical intent path.

## F-007 — Structural entity ambiguity risk
**Symptom:** 1/3 structural ambiguity signals on /index.html: common-name=False, sameAs=False, qualifier=False
**Cost:** This can reduce machine understanding or a human next step.
**Owner/action:** dev — State a distinguishing qualifier and link authoritative profiles with sameAs.

## F-008 — Heading hierarchy is not a single ordered outline
**Symptom:** 0/1 ordered heading-outline proxy passes at /index.html
**Cost:** This can reduce machine understanding or a human next step.
**Owner/action:** dev — Address the measurable proxy, then rerun this check.

## F-009 — Title, H1, and first paragraph lack lexical agreement
**Symptom:** 0.00/1 lexical agreement at /index.html
**Cost:** This can reduce machine understanding or a human next step.
**Owner/action:** dev — Address the measurable proxy, then rerun this check.

## F-010 — Sitemap pages are absent from navigation
**Symptom:** 1/1 sitemap-or-sampled pages are not linked from nav; sample: /rendered.html
**Cost:** This can reduce machine understanding or a human next step.
**Owner/action:** dev — Expose primary intent pages through semantic navigation.

## F-011 — Document language or hreflang metadata is invalid
**Symptom:** 0/1 html lang and 1/1 hreflang-format checks pass at /index.html
**Cost:** This can reduce machine understanding or a human next step.
**Owner/action:** dev — Address the measurable proxy, then rerun this check.

## F-012 — price is a single-point-of-truth fact
**Symptom:** 1/2 sampled pages state price; source: /rendered.html
**Cost:** This can reduce machine understanding or a human next step.
**Owner/action:** dev — Maintain a canonical facts page and reference it from relevant pages.
