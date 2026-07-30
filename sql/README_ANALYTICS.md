# SQL Analytics Layer

## Design principles

The analytics layer separates reusable metric definitions from one-off business analysis:

1. `03_views.sql` defines stable grains and business metrics.
2. `04_stored_procedures.sql` exposes validated, parameterized analysis APIs.
3. `05_advanced_analysis.sql` demonstrates how those objects answer business questions.
4. `06_data_quality_checks.sql` protects metric integrity.

Deploy the files in numeric order after loading source data.

## Metric semantics

| Metric | Definition | Important caveat |
|---|---|---|
| Gross revenue | Quantity × historical unit price | Before discount and cancellation treatment |
| Net revenue | Gross revenue − discount | Booked revenue; cancelled orders are zero |
| Revenue after refund | Net revenue − non-rejected refunds | Recommended realized-revenue proxy |
| Gross profit | Net revenue − historical product cost | Before refund and operating expenses |
| Gross profit after refund | Gross profit − refund | Conservative; no returned-inventory cost recovery |
| AOV | Net revenue ÷ valid orders | Booked AOV, not after-refund AOV |
| Unit return rate | Non-rejected returned units ÷ sold units | Rejected return requests are excluded |
| Repeat purchase | Valid customer order number greater than one | Cancelled orders do not advance sequence |
| Projected 12-month revenue | Annualized historical after-refund revenue | Explainable run rate, not predictive ML |

## Analysis catalog

| # | Business question | Primary SQL skills | Business interpretation |
|---:|---|---|---|
| 1 | Is revenue and profit growth sustainable? | `LAG`, rolling average, running total | Separate trend from monthly noise and refund leakage |
| 2 | What drives annual growth? | CTE, `LAG`, decomposition | Distinguish customer/order growth from AOV growth |
| 3 | How is channel mix changing? | `PIVOT` | Identify channel concentration and migration |
| 4 | How quickly do customers repeat? | `LEAD`, conditional aggregation | Measure the actionable second-order window |
| 5 | Which valuable customers are at churn risk? | cadence-based classification, `RANK` | Prioritize win-back by value and abnormal inactivity |
| 6 | Which customers have the highest explainable CLV? | `NTILE`, `DENSE_RANK` | Compare historical value with transparent annual run rate |
| 7 | How should CRM audiences be segmented? | RFM, transaction, snapshot | Create auditable operational audiences |
| 8 | Are cohorts retaining better over time? | layered CTEs, windows | Detect retention deterioration hidden by aggregates |
| 9 | Which products balance revenue, profit, and quality? | partitioned ranks | Avoid revenue-only merchandising decisions |
| 10 | Which products are bought together? | temp table, self-join, lift | Generate bundle and recommendation hypotheses |
| 11 | Where is return/refund exposure concentrated? | conditional aggregation, safe ratios | Separate rate problems from dollar exposure |
| 12 | Which carrier-region lanes underperform? | conditional aggregation, `HAVING` | Support routing and SLA action |
| 13 | Which campaigns convert profitably? | funnel aggregation, attribution | Compare engagement with directly attributed economics |
| 14 | Are discounts associated with better order economics? | matched cuts, conditional aggregation | Identify candidates for controlled testing |
| 15 | Which regions create quality growth? | window shares, `RANK` | Evaluate revenue with margin and repeat behavior |
| 16 | How concentrated is customer value? | cumulative windows, Pareto | Quantify the customer share producing 80% of revenue |

## Stored procedure examples

```sql
EXEC analytics.usp_SalesPerformance
    @StartDate = '2024-01-01',
    @EndDate = '2025-12-31',
    @ChannelName = 'Mobile App',
    @Region = 'West';

EXEC analytics.usp_Customer360 @CustomerId = 250;

EXEC analytics.usp_RefreshRfmSegments @AsOfDate = '2026-01-01';

EXEC analytics.usp_ProductAffinity
    @StartDate = '2025-01-01',
    @EndDate = '2025-12-31',
    @MinimumPairOrders = 25,
    @TopN = 50;

EXEC analytics.usp_CohortRetention
    @CohortStartDate = '2024-01-01',
    @CohortEndDate = '2024-12-31',
    @MaxMonths = 12;

EXEC analytics.usp_ProductPerformance
    @CategoryName = N'Electronics',
    @MinimumOrders = 25,
    @TopN = 20;
```

## Interpretation limits

- Promotion attribution is direct promo-code attribution. It does not prove incremental lift.
- Discount comparisons are observational because customers self-select into promotions.
- The dataset has no campaign cost, shipping cost, overhead, or returned-item disposition. Therefore ROAS, contribution margin, and fully loaded profit cannot be calculated faithfully.
- Churn status is an interpretable rules-based indicator. It is not a trained probability model.
- RFM quintiles are relative to the portfolio at a snapshot date and should not be compared as absolute scores across unrelated businesses.
