# Power BI Measure Dictionary

All measures live in the `_Measures` table. Raw fact columns are hidden from report authors. Currency measures use USD because the synthetic source has one reporting currency.

| Display folder | Measure | Business definition | Format |
|---|---|---|---|
| Revenue | Revenue | Non-cancelled gross item value less line discounts | `$#,0;($#,0);-` |
| Revenue | Revenue After Refund | Revenue less non-rejected refunds | `$#,0;($#,0);-` |
| Revenue | Gross Revenue | Item value before discounts | `$#,0;($#,0);-` |
| Revenue | Discount Amount | Granted line discount | `$#,0;($#,0);-` |
| Revenue | Refund Amount | Non-rejected refund exposure | `$#,0;($#,0);-` |
| Profitability | Gross Profit | Revenue less product cost | `$#,0;($#,0);-` |
| Profitability | Gross Profit After Refund | Gross profit less non-rejected refunds | `$#,0;($#,0);-` |
| Profitability | Gross Margin % | Gross profit divided by revenue | `0.0%` |
| Profitability | Gross Margin After Refund % | After-refund profit divided by after-refund revenue | `0.0%` |
| Profitability | Discount Rate | Discount amount divided by gross revenue | `0.0%` |
| Profitability | Refund Rate | Refund amount divided by revenue | `0.0%` |
| Sales | Orders | Distinct non-cancelled orders | `#,0` |
| Sales | Units Sold | Units on non-cancelled order lines | `#,0` |
| Sales | Average Order Value | Revenue divided by orders | `$#,0.00` |
| Customer | Active Customers | Customers with a non-cancelled order in filter context | `#,0` |
| Customer | New Customers | Customers whose first order falls inside the selected period | `#,0` |
| Customer | Repeat Customers | Customers placing a repeat order in filter context | `#,0` |
| Customer | Repeat Orders | Orders after a customer's first valid order | `#,0` |
| Customer | Repeat Order Rate | Repeat orders divided by orders | `0.0%` |
| Customer | Revenue per Active Customer | After-refund revenue divided by active customers | `$#,0.00` |
| Customer | Average Historical CLV | Mean observed lifetime after-refund revenue among purchasers | `$#,0.00` |
| Customer | Projected 12M Customer Value | Mean annualized after-refund revenue run rate | `$#,0.00` |
| Customer | Customers at Risk | Customers classified At Risk or High Risk | `#,0` |
| Customer | Churn Indicator % | At-risk customers divided by customers with an order | `0.0%` |
| Customer | Revenue at Risk | Historical after-refund revenue of at-risk customers | `$#,0` |
| Product | Product Revenue | Line-grain revenue for product analysis | `$#,0;($#,0);-` |
| Product | Product Gross Profit | Line-grain gross profit | `$#,0;($#,0);-` |
| Product | Product Gross Margin % | Product gross profit divided by product revenue | `0.0%` |
| Returns | Returned Units | Units on non-rejected returns | `#,0` |
| Returns | Return Rate | Returned units divided by valid units sold | `0.0%` |
| Returns | Return Event Units | Non-rejected returned units filtered by return event date and return attributes | `#,0` |
| Returns | Return Refund Amount | Non-rejected refund amount filtered by return event date and return attributes | `$#,0;($#,0);-` |
| Returns | Product Refund Amount | Refund amount aligned to sold-order-line date and product context | `$#,0;($#,0);-` |
| Operations | Delivered Orders | Valid orders with a delivered date | `#,0` |
| Operations | On-Time Deliveries | Valid orders delivered by promised date | `#,0` |
| Operations | On-Time Delivery % | On-time deliveries divided by delivered orders | `0.0%` |
| Operations | Average Delivery Days | Mean calendar days from order to delivery | `0.0` |
| Reviews | Reviews | Review row count | `#,0` |
| Reviews | Average Rating | Mean review rating | `0.00` |
| Reviews | Verified Review % | Verified-purchase reviews divided by reviews | `0.0%` |
| Reviews | Reviewed Item Return Rate | Reviews linked to returned items divided by reviews | `0.0%` |
| Marketing | Campaign Audience | Unique exposed customers summed at campaign grain | `#,0` |
| Marketing | Campaign Clicks | Campaign click interactions | `#,0` |
| Marketing | Campaign Conversions | Campaign conversion interactions | `#,0` |
| Marketing | Campaign Conversion % | Conversions divided by clicks | `0.0%` |
| Marketing | Campaign CTR % | Clicks divided by audience | `0.0%` |
| Marketing | Attributed Revenue | Directly attributed after-refund revenue | `$#,0;($#,0);-` |
| Marketing | Attributed Gross Profit | Directly attributed gross profit | `$#,0;($#,0);-` |
| Marketing | Campaign Discount Cost | Discount granted on attributed orders | `$#,0;($#,0);-` |
| Marketing | Attributed Revenue per Discount Dollar | Attributed revenue divided by campaign discount cost | `$0.00` |
| Retention | Retention % | Active cohort customers divided by original cohort size; returns only at matrix-cell grain | `0.0%` |
| Retention | RFM Customers | Distinct customers in selected RFM snapshot/segment | `#,0` |
| Retention | RFM Monetary Value | After-refund historical value represented by an RFM segment | `$#,0` |
| Time Intelligence | Revenue Previous Month | Revenue shifted one month | `$#,0` |
| Time Intelligence | Revenue MoM Change | Revenue less previous-month revenue | `$#,0;($#,0);-` |
| Time Intelligence | Revenue MoM % | MoM change divided by previous-month revenue | `0.0%;(0.0%);-` |
| Time Intelligence | Revenue Previous Year | Revenue shifted one year | `$#,0` |
| Time Intelligence | Revenue YoY Change | Revenue less prior-year revenue | `$#,0;($#,0);-` |
| Time Intelligence | Revenue YoY % | YoY change divided by prior-year revenue | `0.0%;(0.0%);-` |
| Time Intelligence | Revenue MTD | Revenue from month start to current date context | `$#,0` |
| Time Intelligence | Revenue YTD | Revenue from year start to current date context | `$#,0` |
| Time Intelligence | Revenue After Refund YTD | After-refund revenue from year start | `$#,0` |
| Time Intelligence | Rolling 3M Revenue | Revenue over the trailing three-month window | `$#,0` |
| Time Intelligence | Rolling 12M Revenue | Revenue over the trailing twelve-month window | `$#,0` |
| Ranking | Product Revenue Rank | Dense product revenue rank within current selection | `#,0` |
| Ranking | Customer Revenue Rank | Dense customer revenue rank within current selection | `#,0` |
| Ranking | Cumulative Customer Revenue | Revenue accumulated through current customer rank | `$#,0` |
| Ranking | Pareto Revenue % | Cumulative customer revenue divided by selected total | `0.0%` |
| Ranking | Pareto 80% Customer Flag | One when current rank remains inside the first 80% of revenue | `0` |
| Sales | All Orders | Distinct orders including cancelled orders | `#,0` |
| Sales | Cancelled Orders | Distinct orders with Cancelled status | `#,0` |
| Sales | Cancellation Rate | Cancelled orders divided by all orders | `0.0%` |
| Operations | Late Deliveries | Delivered orders that missed the promised date | `#,0` |
| Operations | Late Delivery % | Late deliveries divided by delivered orders | `0.0%` |
| Marketing | Attributed Orders | Orders directly attributed to campaigns | `#,0` |
| Marketing | Attributed Average Order Value | Attributed after-refund revenue divided by attributed orders | `$#,0.00` |
| Marketing | Campaign Profit per Conversion | Attributed gross profit divided by campaign conversions | `$#,0.00` |
| Marketing | Promotion Orders | Valid orders carrying a promotion key | `#,0` |
| Marketing | Promotion Order Rate | Promotion orders divided by valid orders | `0.0%` |
| Reviews | One and Two Star Reviews | Reviews rated one or two stars | `#,0` |
| Reviews | Low Rating Review % | One- and two-star reviews divided by all reviews | `0.0%` |
| Time Intelligence | Orders Previous Year | Valid orders shifted one year | `#,0` |
| Time Intelligence | Orders YoY % | Order change divided by prior-year orders | `0.0%;(0.0%);-` |
| Time Intelligence | Gross Profit Previous Year | Gross profit shifted one year | `$#,0` |
| Time Intelligence | Gross Profit YoY % | Gross-profit change divided by prior-year gross profit | `0.0%;(0.0%);-` |
| Time Intelligence | Active Customer Previous Year | Active customers shifted one year | `#,0` |
| Time Intelligence | Active Customer YoY % | Active-customer change divided by prior-year active customers | `0.0%;(0.0%);-` |
| Retention | RFM Customer Share % | RFM customers divided by all customers in the selected snapshot | `0.0%` |

## Non-additive measure notes

- Percentages, AOV, CLV, rankings, retention, and delivery averages must never be summed.
- `Campaign Audience` can double-count a person exposed to multiple campaigns; it is correct at campaign grain but is not a unique cross-campaign reach measure.
- Historical CLV and projected 12-month value are descriptive planning metrics, not causal or predictive models.
- Cohort retention deliberately returns blank outside a single cohort/month cell to prevent misleading grand totals.
