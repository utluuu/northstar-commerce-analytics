# Business Insights & Recommendations

The pipeline-generated [Executive Analysis Summary](../reports/EXECUTIVE_SUMMARY.md) is the canonical source for quantified findings, business impact, and recommended actions. It is rebuilt from the current deterministic dataset on every EDA run.

This document provides the durable interpretation framework behind those generated findings. Because the data is synthetic, observations must not be presented as claims about a real company.

## Executive questions

### 1. Is growth healthy or promotion-dependent?

Compare monthly net revenue, order volume, AOV, gross margin, and discount rate. Revenue growth accompanied by falling margin or rising discount rate may be purchased rather than organic.

**Action:** establish a margin floor for promotions and A/B test offers against a holdout group. Track incremental profit, not redemption alone.

### 2. Which assortment deserves investment?

Rank products within category using revenue, gross profit, unit volume, and return rate together. High revenue does not automatically mean high contribution, and high-return products create additional operational cost.

**Action:** prioritize products with strong revenue and margin, investigate quality/listing issues for high-return SKUs, and avoid scaling low-margin volume without a basket-building role.

### 3. How important are repeat customers?

Use repeat revenue share, customer order frequency, cohort retention, and RFM segments. Compare acquisition sources on lifetime revenue rather than first-order revenue.

**Action:** create post-purchase journeys for promising new customers, loyalty benefits for champions, and targeted win-back tests for at-risk customers.

### 4. Where is fulfillment damaging experience?

Segment delivery time and on-time rate by carrier, state, channel, and month. Combine late-delivery patterns with the `Too Late` return reason.

**Action:** renegotiate carrier service levels in weak lanes, set realistic promises by region, and route orders based on measured lane performance.

### 5. What is driving returns?

Separate product-driven reasons (`Defective`, `Damaged`, `Not as Described`) from preference-driven reasons (`Changed Mind`). Review return rate and refund exposure at product/category level.

**Action:** improve product content where expectation gaps are visible, audit packaging for damage, and review suppliers for defect clusters.

## Analysis-to-action matrix

| Signal | Diagnostic cut | Likely owner | Recommended next step |
|---|---|---|---|
| Revenue up, margin down | channel × promo × product | Commercial | Test promo profitability and guardrails |
| Low month-2 retention | cohort × acquisition source | CRM/Growth | Improve onboarding and second-order offer |
| High `Not as Described` returns | SKU × refund value | Merchandising | Rewrite listing and improve imagery/specs |
| Low on-time rate | carrier × state × month | Operations | Review lane SLA and routing |
| High-value at-risk segment | RFM segment × days inactive | CRM | Controlled win-back campaign |

## Suggested portfolio narrative

1. Start with the commercial question, not the tool.
2. Explain why the normalized model protects data quality.
3. Show one advanced query and the business decision it supports.
4. Present two or three insights with context, not a list of chart descriptions.
5. Close with limitations, recommended actions, and how success would be measured.
