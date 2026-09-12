# Evidence-derived priority rubric

For each finding, the orchestrator computes `priority_points = round(impact × confidence × reach_share × fixability)`. It emits no readiness score or percentage beyond a directly measured count or ratio.

| Factor | Range | Deterministic source |
| --- | --- | --- |
| impact | 1–5 | Stable check-ID mapping documented in that check's catalog; gated checks cannot exceed their mapped cap. |
| confidence | 0–1 | `confirmed_evidence_count / applicable_evidence_count`, clamped to `[0, 1]`; zero applicable evidence becomes insufficient evidence. |
| reach_share | 0–1 | affected sampled pages divided by sampled pages; estimate is used only where a template fingerprint establishes reach. |
| fixability | 1–5 | Stable check-ID mapping based on a documented, local counterfactual fix class. |

Sort by descending points, then check ID, then canonical locator. Keep twelve findings; group the remainder in `other_findings`. An exploratory check is capped at `medium`; a gated check may only use the severity its gate permits.
