# Measurable engagement proxies
| Check | Proxy | Why it correlates | Known false-positive mode |
|---|---|---|---|
| EG-001 | Offering + verb CTA within 300/700 visible text chars | A concise first view can orient and offer a next action | CSS layout may differ from text order |
| EG-002/003 | Ordered headings; token overlap across title/H1/first paragraph | Coherent document structure supports scanning | Deliberately creative copy may use different words |
| EG-004/005 | CTA inventory/position; parsed inline/style color contrast | Visible actionable controls and contrast support action | Dynamic CSS is not computed |
| EG-006/007 | Sitemap-or-sample routes in nav; intent text with zero onward links | Reachable routes and onward paths reduce avoidable friction | Intent words can be incidental |
| EG-008/009 | Hidden key-fact words; 250-word paragraphs | Fresh-load facts and scannable chunks support comprehension | Disclosure UI or long-form editorial pages |
| EG-010/011 | Label/autofill and explicit 44px dimensions | Accessible forms and targets reduce input friction | CSS classes/media queries may supply omitted styles |
| EG-012 | `lang`/`hreflang` attributes | Language metadata helps locale handling | Single-language sites need no alternates |
| EG-013 | Bytes, blocking scripts, stylesheets | Static payload/dependency count is a first-paint proxy | Compression/cache/runtime behavior is unknown |

All are proxies, not measurements of bounce, intent, or conversion. Missing computable CSS is insufficient evidence rather than a defect.
