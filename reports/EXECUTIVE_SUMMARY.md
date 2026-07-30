# Executive Analysis Summary

## Portfolio scope

This report was generated from deterministic synthetic Northstar Commerce transactions through 2025-12-31. It applies the same metric semantics as the SQL analytics layer and is intended to demonstrate reproducible business analysis rather than describe a real company.

## Executive scorecard

| KPI | Value |
|---|---:|
| Valid orders | 116,126 |
| Purchasing customers | 10,739 |
| Booked net revenue | $34,736,795 |
| Revenue after refund | $33,819,546 |
| Gross profit | $18,497,102 |
| Gross margin rate | 53.2% |
| Average order value | $299.13 |
| Repeat order rate | 90.8% |
| Repeat customer rate | 67.8% |
| Refund leakage rate | 2.6% |
| On-time delivery rate | 74.1% |

## Priority findings and actions

### 1. After-refund revenue establishes the commercial baseline

**Finding:** Booked net revenue is $34,736,795; refunds reduce it to $33,819,546 (2.6% leakage).

**Business impact:** Using booked revenue alone overstates realized commercial value.

**Recommended action:** Use RevenueAfterRefund as the executive revenue KPI and monitor refund leakage beside growth.
### 2. Latest year-over-year momentum

**Finding:** The latest complete monthly comparison shows 92.9% year-over-year after-refund revenue growth.

**Business impact:** Growth direction affects inventory, acquisition, and capacity planning.

**Recommended action:** Decompose the change by orders, active customers, AOV, channel, and category before setting targets.
### 3. Demand is concentrated in a seasonal peak

**Finding:** Month 12 has the highest revenue seasonality index at 1.86x an average month.

**Business impact:** Seasonal concentration raises stockout, fulfillment, and working-capital risk.

**Recommended action:** Plan inventory and carrier capacity against the seasonal index and track forecast error by category.
### 4. Acquisition-source quality differs

**Finding:** Marketplace leads after-refund revenue per purchasing customer at $3,301.

**Business impact:** Volume-only acquisition reporting can reward low-value sources.

**Recommended action:** Compare source-level cost with purchaser conversion, repeat rate, and after-refund value before reallocating spend.
### 5. Repeat behavior drives portfolio economics

**Finding:** 67.8% of acquired customers are repeat customers and 90.8% of valid orders are repeat purchases.

**Business impact:** Second-order conversion is a leading indicator of retention and future value.

**Recommended action:** Build 30/60/90-day post-purchase journeys and measure incremental second-order conversion.
### 6. Month-one cohort retention sets the early baseline

**Finding:** Average month-one cohort retention is 31.3% across observed cohorts.

**Business impact:** Weak early retention limits CLV even when acquisition volume grows.

**Recommended action:** Monitor cohort retention by acquisition source and first-purchase category, using only mature cohorts.
### 7. Customer value is exposed to churn risk

**Finding:** At Risk and High Risk customers represent $2,514,351 in historical after-refund revenue.

**Business impact:** Losing high-value customers creates disproportionate revenue risk.

**Recommended action:** Prioritize win-back tests by risk status and historical value rank; use holdouts to measure incrementality.
### 8. Category profit leadership

**Finding:** Electronics contributes the highest gross profit at $4,299,565 with 54.4% margin.

**Business impact:** Revenue leadership and profit leadership may require different assortment decisions.

**Recommended action:** Protect availability for high-profit products and review low-margin volume for basket-building value.
### 9. Returns identify a category-quality hotspot

**Finding:** Outdoor has the highest unit return rate at 2.7% and $110,753 in refunds.

**Business impact:** Returns reduce realized revenue and may signal quality, content, or expectation problems.

**Recommended action:** Break the category down by SKU and reason; assign corrective work to supplier, packaging, or content owners.
### 10. A fulfillment lane requires attention

**Finding:** USPS in West has the lowest qualifying on-time rate at 55.4% across 9,168 deliveries.

**Business impact:** Late delivery can drive support contacts, churn, and 'Too Late' returns.

**Recommended action:** Review lane-level SLA performance and test routing rules against on-time delivery and cost.
### 11. Campaign attribution must be evaluated on profit

**Finding:** Fall Essentials 2025 has the highest directly attributed gross profit at $153,909.

**Business impact:** High attributed revenue may still be discount-dependent and is not proof of incrementality.

**Recommended action:** Add campaign cost and randomized holdouts before making budget decisions; retain direct attribution as descriptive reporting.
### 12. Value concentration and experience signals

**Finding:** 39.8% of purchasing customers generate 80% of after-refund revenue. Low-rating reviews return at 60.4% versus 0.3% for ratings 4-5; promoted gross profit per order differs by -6.0% from non-promoted orders.

**Business impact:** Concentrated value and review-return alignment help prioritize retention and product-quality work.

**Recommended action:** Protect high-value relationships, investigate low-rating SKUs, and treat promotion comparisons as hypotheses for controlled tests.

## Methodology

- Source CSVs are loaded under explicit table contracts; large facts are read in configurable chunks.
- Primary keys, foreign keys, required fields, valid ranges, chronology, and outlier counts are checked before analysis.
- Order-line economics are aggregated to order grain and reconciled within one cent.
- `NetRevenue` is booked revenue after line discount and excludes cancelled orders.
- `RevenueAfterRefund` subtracts refunds associated with non-rejected returns.
- `GrossProfitAfterRefund` is a conservative proxy that subtracts refunds without assuming inventory recovery.
- RFM uses deterministic portfolio quintiles at the configured snapshot date.
- Cohorts are assigned by first valid order month; customers count once per active month.
- CLV is a transparent annualized historical after-refund revenue run rate with a 90-day minimum observation period.
- Campaign attribution is direct promotion attribution, not causal incrementality.

## Data quality

- Status: **PASS**
- Checks passed: **69**
- Warnings: **1**
- Unexpected missing required values: **0**
- Expected nullable values: **66,803**
- High-value line outliers retained: **5,150**

Outliers are reported rather than automatically removed because high-value orders may be commercially valid. Full results are available in `data_quality_report.json`.

## Limitations

- The dataset is synthetic and should not be used for external market benchmarks.
- Campaign cost is absent, so ROAS and true incremental profit cannot be calculated.
- Discount comparisons are observational and subject to customer self-selection.
- Shipping expense, overhead, marketing cost, and returned-inventory disposition are not modeled.
- Churn and projected value are interpretable rules/run rates, not trained probability models.
- Cohorts near the end of the observation window are right-censored and should only be compared at mature elapsed months.
- Review-return association is descriptive and does not establish that ratings cause returns.

## Power BI-ready exports

| File | Rows |
|---|---:|
| `acquisition_performance.csv` | 6 |
| `campaign_performance.csv` | 18 |
| `category_performance.csv` | 6 |
| `cohort_retention.csv` | 666 |
| `delivery_performance.csv` | 16 |
| `dim_channels.csv` | 4 |
| `dim_customers.csv` | 12,000 |
| `dim_date.csv` | 1,461 |
| `dim_geography.csv` | 30 |
| `dim_products.csv` | 600 |
| `dim_promotions.csv` | 18 |
| `discount_effectiveness.csv` | 221 |
| `fact_order_lines.csv` | 253,441 |
| `fact_orders.csv` | 120,000 |
| `fact_returns.csv` | 8,925 |
| `fact_reviews.csv` | 42,837 |
| `monthly_performance.csv` | 36 |
| `pareto_curve.csv` | 10,669 |
| `product_performance.csv` | 600 |
| `regional_channel_performance.csv` | 16 |
| `review_return_relationship.csv` | 5 |
| `rfm_segments.csv` | 10,739 |

## Generated figures

- `01_monthly_revenue_profit.png`
- `02_mom_yoy_growth.png`
- `03_revenue_seasonality.png`
- `04_acquisition_source_value.png`
- `05_rfm_segment_distribution.png`
- `06_cohort_retention_heatmap.png`
- `07_product_revenue_margin_returns.png`
- `08_category_refund_exposure.png`
- `09_delivery_lane_performance.png`
- `10_campaign_attributed_profit.png`
- `11_customer_pareto_curve.png`
- `12_review_rating_return_relationship.png`
