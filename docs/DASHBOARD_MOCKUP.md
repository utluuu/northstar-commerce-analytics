# Power BI Dashboard Blueprint

> The delivery build is now consolidated into six portfolio pages. `BUILD_POWERBI.md` is the authoritative implementation specification; it combines the former Operations and Returns pages into **Operations, Returns & Satisfaction** while preserving both analytical scopes.

## Design system

- Canvas: 16:9, 1280 x 720, light neutral page background, 24 px outer margin, 16 px visual gaps.
- Navigation: persistent left rail with seven page icons and text labels; active page uses the primary blue accent.
- Header: page title, selected date context, last refresh timestamp, and a filter-pane button.
- Reading order: KPI outcomes first, trend and driver analysis second, diagnostic detail last.
- Color: blue for primary values, teal for profit/positive outcomes, amber for attention, red only for adverse exceptions. Color is always paired with a label or symbol.
- Accessibility: minimum 4.5:1 text contrast, descriptive alt text, logical tab order, no color-only meaning, and consistent units.
- Interaction: charts cross-highlight only when analytically meaningful. Disable interactions that cause a denominator or benchmark to become misleading.

Global slicers use dropdowns for `Date`, `Channel`, `Region`, `Category`, and `Customer Segment`. Date is a between slicer on analysis pages and a relative-date slicer on the executive page. Sync only slicers whose dimensions apply to every visual on the target pages.

## 1. Executive Overview

Business question: Are growth, customer activity, and profitability moving in the right direction, and where is leadership attention required?

```text
+------+---------------------------------------------------------------+
| NAV  | Executive Overview                      Date | Filters | Reset |
|      +-----------+-----------+-----------+-----------+-----------+---+
| Exec | Revenue   | Rev. after| Gross     | Margin %  | Orders    |AOV|
| Sales| refund    | YoY delta | profit    | vs PY     | vs PY     |   |
| Cust +-------------------------------+-------------------------------+
| Prod | Monthly revenue and rolling 12M| Revenue by category/channel |
| Mktg | Actual line + rolling line     | Ranked horizontal bars      |
| Ops  +-------------------------------+-------------------------------+
| Ret  | Profit bridge: revenue to GP   | Exceptions: returns, late,  |
|      | waterfall                      | churn risk with status icons |
+------+-------------------------------+-------------------------------+
```

- KPI cards: `Revenue After Refund`, `Revenue YoY %`, `Gross Profit After Refund`, `Gross Margin After Refund %`, `Orders`, `Average Order Value`.
- Visual rationale: a line chart exposes direction and seasonality; ranked bars compare drivers without pie-chart precision loss; the waterfall explains economic leakage; the exception strip directs action.
- Tooltip: current, prior period, variance, margin, orders, and active customers.
- Drill-through: category to Product Detail; churn exception to Customer Detail; delivery exception to Operations.
- Conditional formatting: red for negative YoY or margin below selected baseline; amber for high refund rate; green only for favorable variance.

## 2. Sales Performance

Business question: Which periods, channels, and regions explain revenue and profit growth?

```text
+------+---------------------------------------------------------------+
| NAV  | Sales Performance                 Date | Channel | Region     |
|      +-----------+-----------+-----------+-----------+---------------+
|      | Revenue   | YoY %     | MoM %     | Rolling 3M| Rolling 12M  |
|      +-----------------------------------+---------------------------+
|      | Revenue vs prior year by month    | Channel revenue and margin|
|      | two-line time series              | clustered bars + dot      |
|      +-----------------------------------+---------------------------+
|      | Region x channel matrix           | Daily/weekly contribution |
|      | revenue, growth, margin heatmap   | decomposition tree         |
+------+-----------------------------------+---------------------------+
```

- KPI cards: `Revenue`, `Revenue YoY %`, `Revenue MoM %`, `Rolling 3M Revenue`, `Rolling 12M Revenue`.
- Comparisons: current versus prior year uses aligned lines; channel bars show revenue with margin as a marker, avoiding dual-axis distortion where possible.
- Drill-through: region/channel to filtered Order Detail.
- Tooltip: revenue, after-refund revenue, profit, margin, AOV, units, and discount rate.
- Conditional formatting: matrix background for YoY and margin; use diverging scale centered at zero for growth.

## 3. Customer Analytics

Business question: Which customer groups drive value, retention, repeat behavior, and churn exposure?

```text
+------+---------------------------------------------------------------+
| NAV  | Customer Analytics            Date | Segment | Acquisition   |
|      +-----------+-----------+-----------+-----------+---------------+
|      | Active    | New       | Repeat    | Avg CLV   | Revenue risk  |
|      +-------------------------------+-------------------------------+
|      | Cohort retention heatmap       | RFM segment distribution    |
|      | cohort rows x elapsed months   | bars: customers + value     |
|      +-------------------------------+-------------------------------+
|      | Repeat purchase curve          | Pareto cumulative curve     |
|      | order number vs repurchase %   | customer share vs revenue % |
+------+-------------------------------+-------------------------------+
```

- KPI cards: `Active Customers`, `New Customers`, `Repeat Customers`, `Average Historical CLV`, `Revenue at Risk`.
- Visual rationale: cohort heatmap shows retention decay; RFM bars keep segment comparisons readable; a Pareto line quantifies concentration.
- Slicers: acquisition source, customer segment, lifecycle status, RFM segment, snapshot date.
- Drill-through: customer to Customer 360 with order history, lifetime value, recency, cadence, returns, and reviews.
- Tooltip: segment size, revenue, CLV, recency, order frequency, repeat rate, and risk status.
- Conditional formatting: cohort cells use a sequential single-hue scale; risk table uses labeled red/amber status icons.

## 4. Product & Category Analytics

Business question: Which products create profitable growth, and which have margin, discount, or return quality problems?

```text
+------+---------------------------------------------------------------+
| NAV  | Product & Category             Date | Category | Brand       |
|      +-----------+-----------+-----------+-----------+---------------+
|      | Product   | Product GP| Margin %  | Units     | Return rate   |
|      +-----------------------------------+---------------------------+
|      | Category revenue/profit bars      | Product portfolio scatter|
|      | hierarchy drill-down              | revenue x margin; size GP |
|      +-----------------------------------+---------------------------+
|      | Top/bottom product matrix         | Product revenue Pareto    |
|      | rank, discount, margin, returns   | cumulative contribution   |
+------+-----------------------------------+---------------------------+
```

- KPI cards: `Product Revenue`, `Product Gross Profit`, `Product Gross Margin %`, `Units Sold`, `Return Rate`.
- Visual rationale: scatter reveals scale/quality trade-offs; matrix supports exact investigation; Pareto separates assortment breadth from concentration.
- Drill-through: product to Product Detail with monthly trend, channel/region split, reviews, returns, and order-line table.
- Tooltip: rank, revenue, after-refund profit, margin, units, discount rate, return rate, reviews, and average rating.
- Conditional formatting: data bars for revenue, red icons for high returns, amber for discount above category benchmark, negative-profit font emphasis.

## 5. Marketing & Campaign Performance

Business question: Which acquisition sources and campaigns create profitable customer behavior rather than discounted volume?

```text
+------+---------------------------------------------------------------+
| NAV  | Marketing & Campaigns       Date | Promotion type | Channel  |
|      +-----------+-----------+-----------+-----------+---------------+
|      | Audience  | CTR %     | Conv. %   | Attr. rev | Profit       |
|      +-----------------------------------+---------------------------+
|      | Campaign funnel                  | Attributed revenue vs     |
|      | audience > clicks > conversions  | discount cost scatter     |
|      +-----------------------------------+---------------------------+
|      | Campaign performance matrix      | Acquisition source value  |
|      | conversion, revenue, profit      | customers, CLV, repeat %  |
+------+-----------------------------------+---------------------------+
```

- KPI cards: `Campaign Audience`, `Campaign CTR %`, `Campaign Conversion %`, `Attributed Revenue`, `Attributed Gross Profit`.
- Visual rationale: funnel is used only for sequential stages; scatter exposes efficiency; matrices preserve campaign-level auditability.
- Drill-through: promotion to Campaign Detail; acquisition source to Customer Analytics.
- Tooltip: promotion dates, audience, clicks, conversions, attributed orders, after-refund revenue, gross profit, and discount efficiency.
- Conditional formatting: profit and efficiency use diverging rules; never label attributed revenue as incremental ROAS because media cost and causal lift are unavailable.

## 6. Operations & Delivery

Business question: Where do carrier and regional fulfillment failures threaten customer experience?

```text
+------+---------------------------------------------------------------+
| NAV  | Operations & Delivery             Date | Carrier | Region    |
|      +-----------+-----------+-----------+-----------+---------------+
|      | Delivered | On-time % | Avg days  | Late      | Revenue risk  |
|      +-----------------------------------+---------------------------+
|      | On-time trend and SLA reference   | Carrier x region matrix  |
|      | line with target band             | on-time %, days, volume   |
|      +-----------------------------------+---------------------------+
|      | Delivery-day distribution         | Late order exception list|
|      | histogram                         | order, customer, variance |
+------+-----------------------------------+---------------------------+
```

- KPI cards: `Delivered Orders`, `On-Time Delivery %`, `Average Delivery Days`, late-order count, after-refund revenue on late orders.
- Visual rationale: SLA line detects drift; matrix isolates lane problems; histogram shows variability hidden by averages; exception table enables action.
- Drill-through: carrier/region to Delivery Detail; order to Order Detail.
- Tooltip: delivered volume, on-time count/rate, average days, promised date, delivered date, and revenue.
- Conditional formatting: SLA breach is red, near-threshold is amber, and low-volume lanes are visually de-emphasized.

## 7. Returns & Customer Satisfaction

Business question: Which products and customer experience signals explain refund exposure and dissatisfaction?

```text
+------+---------------------------------------------------------------+
| NAV  | Returns & Satisfaction      Date | Category | Return reason  |
|      +-----------+-----------+-----------+-----------+---------------+
|      | Returned  | Return %  | Refund $  | Refund %  | Avg rating    |
|      +-----------------------------------+---------------------------+
|      | Return reason contribution        | Rating vs return rate    |
|      | sorted horizontal bars            | columns + confidence n   |
|      +-----------------------------------+---------------------------+
|      | Product return/refund matrix      | Rating distribution      |
|      | volume, rate, refund, rating      | verified vs all reviews  |
+------+-----------------------------------+---------------------------+
```

- KPI cards: `Returned Units`, `Return Rate`, `Refund Amount`, `Refund Rate`, `Average Rating`.
- Visual rationale: reason bars show actionable drivers; rating-return comparison tests an experience hypothesis; product matrix connects financial and satisfaction signals.
- Drill-through: return reason/product to Return Detail; review to Product Detail.
- Tooltip: returned units, refund amount, return rate, rating, verified review share, sample size, and after-refund margin.
- Conditional formatting: high return/refund rates use red icons only when minimum-volume thresholds are met; low sample sizes show a warning label.

## Drill-through pages

| Page | Drill-through fields | Contents |
|---|---|---|
| Customer 360 | `CustomerId` | profile, lifecycle, RFM, order trend, order history, returns |
| Product Detail | `ProductId` | revenue/profit trend, channel/region mix, rank, returns, reviews |
| Order Detail | `OrderId` | order economics, item table, promotion, shipment, return status |
| Campaign Detail | `PromotionId` | funnel, attributed economics, time window, customer segments |
| Delivery Detail | `Carrier`, `GeographyKey` | SLA trend, distribution, late-order list |

Keep drill-through pages hidden from primary navigation and include a Back button. Preserve filters only when the originating context remains meaningful.

## Tooltip pages

Create compact report-page tooltips for Product, Customer Segment, Campaign, and Delivery Lane. Each contains no more than four metrics and one micro-trend. Tooltip pages supplement labels; they do not hide essential definitions or warnings.

## Navigation and bookmarks

- Use Page Navigator for the seven primary pages and bookmark buttons only for state changes such as opening the filter panel.
- Provide `Reset filters` as a bookmark captured with data state and current page only.
- Use consistent Back, Help, and Definitions buttons. Definitions opens a tooltip or information panel sourced from `MEASURE_DICTIONARY.md`.
- Avoid bookmark-based visual duplication when a field parameter can switch a metric cleanly.

## Quality gates before publication

1. Reconcile six financial measures to SQL and Python outputs.
2. Test every slicer, interaction, drill-through, tooltip, bookmark, and keyboard tab sequence.
3. Review at 100% and common laptop resolution; no scrollbars on core pages.
4. Run Performance Analyzer and investigate visuals above two seconds.
5. Add alt text, page descriptions, measure descriptions, and a visible data-refresh timestamp.
6. Validate color contrast and test red/green encodings with labels or icons.
7. Publish only after removing unused columns and ensuring no credentials or local paths are embedded.
