# Conflict taxonomy
| Check | Canonicalization / gate | False-positive limit |
|---|---|---|
| TF-001 | `founded/established/since` years, employee counts, and visible prices normalized before grouping | Different product prices are not compared when keyed only by product-agnostic price; findings need two values |
| TF-002 | Latest visible year compared to copyright year | Historic pages may intentionally retain old dates |
| TF-003 | One sampled source for one normalized claim | Sampling cannot prove site-wide uniqueness |
| TF-004 | Numeric customer/user/team/percent claim lacks nearby source language | First-party claims may be self-evident but still lack cited context |
| TF-005 | Disabled unless `--extended` | Default result is always insufficient evidence, never a web claim |
| TF-006 | Currency value with no dated/effective context | Stable prices may not need a date |
| TF-007 | Local HTML link target absent from the same artifact set | The crawl/sample may be incomplete; it is not called a live 404 |
| TF-008 | Visible Contact link has empty, fragment, or unavailable sampled target | An external contact provider may be intentionally unavailable from the artifact set |
