# Entity/fact claim vocabulary

The extractor uses this small fixed vocabulary to avoid speculative fact mining. It normalizes values with lowercase comparison, then preserves the extracted value in output.

| Key | Accepted language | Value rule | Check |
| --- | --- | --- | --- |
| `founded` | `founded`, `established`, `since` followed by a year | Four-digit year from 1800–2099 | EF-003 |
| `email` | RFC-like visible email address | Lowercase address | EF-003 |
| `identity.name` | Home-page title before `|`, dash, or H1 fallback | Trimmed visible text | EF-001 |
| `identity.one_liner` | Meta description or first descriptive home-page text | Plain text, max 280 chars | EF-001 |

Intent detection uses fixed two-signal groups, not generative interpretation: `pricing`, `what-is-it`, `who-is-it-for`, `how-to-buy`, and `support`. A page is an anchor only when it matches every group for that intent. A lone partial page is not called a defect.

`sameAs` is accepted only from parseable JSON-LD. A missing profile link is one structural signal, not proof that a brand is ambiguous. `llms.txt` or `/.well-known/` discovery is reported as a non-defect proactive opportunity only.

EF-007 checks only for parseable `Organization`, `LocalBusiness`, `Product`, or `Service` entity markup. Property validity remains CG-structured-data scope.
