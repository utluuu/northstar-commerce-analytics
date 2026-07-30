# Build the Northstar Commerce Power BI Report

## Deliverable scope

This guide builds a six-page, portfolio-ready Power BI report from the 22 CSV exports in `data/processed`. It uses the governed DAX in `powerbi/measures.dax`, the Northstar theme, a strict star schema, and disconnected validation aggregates. No SQL, Python, or generated CSV modification is required.

## 1. Create the report and import the theme

1. Open the current 64-bit Power BI Desktop.
2. Create a blank report and save it as `Northstar Commerce Analytics.pbix` outside the repository until credentials and paths are reviewed.
3. Select **View > Themes > Browse for themes** and choose `powerbi/theme.json`.
4. Select **File > Options and settings > Options > Data Load** and disable Auto date/time.
5. Set the page canvas to 16:9. Use 1280 x 720 as the design reference.

Theme roles:

| Purpose | Hex |
|---|---|
| Primary revenue | `#2563EB` |
| Profit / favorable | `#0F766E` |
| Attention / discount | `#D97706` |
| Secondary segmentation | `#7C3AED` |
| Adverse / exception | `#DC2626` |
| Neutral comparison | `#64748B` |
| Page background | `#F8FAFC` |
| Visual background | `#FFFFFF` |
| Primary text | `#0F172A` |

Use red only for adverse results. Pair every color with a label, icon, or direct value.

## 2. Configure Power Query

1. Open **Home > Transform data > Manage Parameters > New Parameter**.
2. Create `CsvRoot` as Text and enter the absolute path to `data\processed`.
3. Create a blank query named `fnLoadCsv` and paste `powerbi/power_query/fnLoadCsv.m` into Advanced Editor.
4. Disable load for `fnLoadCsv`.
5. Create all 22 table queries using `powerbi/power_query/QUERY_CATALOG.md`.
6. Name every query exactly as specified in `powerbi/table_manifest.csv`.
7. Confirm the Applied Steps for each table contain only `Source`, `PromotedHeaders`, and `TypedColumns`.
8. Enable load for all 22 data tables.
9. Hide the nine `Validation*` tables after loading; do not relate them to the model.
10. Select **Close & Apply**.

The validation tables satisfy the all-CSV requirement and provide reconciliation evidence. They must not drive production visuals because their pre-aggregated grains do not respond safely to conformed slicers.

## 3. Validate table grains

| Table | Expected rows | Required unique key or grain |
|---|---:|---|
| `DimDate` | 1,461 | `DateKey` |
| `DimCustomer` | 12,000 | `CustomerId` |
| `DimProduct` | 600 | `ProductId` |
| `DimChannel` | 4 | `ChannelId` |
| `DimGeography` | 30 | `GeographyKey` |
| `DimPromotion` | 18 | `PromotionId` |
| `FactOrders` | 120,000 | `OrderId` |
| `FactOrderLines` | 253,441 | `OrderItemId` |
| `FactReturns` | 8,925 | `ReturnItemId` |
| `FactReviews` | 42,837 | `ReviewId` |
| `FactCampaignPerformance` | 18 | `PromotionId` |
| `FactCohortRetention` | 666 | `CohortMonth + MonthsSinceFirstOrder` |
| `FactRfmSnapshot` | 10,739 | `CustomerId + SnapshotDateKey` |

Use a temporary table visual or Power Query profiling to confirm these values. Do not create a relationship until its one-side key is unique.

## 4. Create relationships

Create every relationship below as active, one-to-many, and single-direction from the dimension to the fact.

| One side | Many side | Cardinality | Direction |
|---|---|---|---|
| `DimDate[DateKey]` | `FactOrders[OrderDateKey]` | 1:* | Single |
| `DimDate[DateKey]` | `FactOrderLines[OrderDateKey]` | 1:* | Single |
| `DimDate[DateKey]` | `FactReturns[ReturnDateKey]` | 1:* | Single |
| `DimDate[DateKey]` | `FactReviews[ReviewDateKey]` | 1:* | Single |
| `DimDate[DateKey]` | `FactCampaignPerformance[StartDateKey]` | 1:* | Single |
| `DimDate[DateKey]` | `FactRfmSnapshot[SnapshotDateKey]` | 1:* | Single |
| `DimCustomer[CustomerId]` | `FactOrders[CustomerId]` | 1:* | Single |
| `DimCustomer[CustomerId]` | `FactOrderLines[CustomerId]` | 1:* | Single |
| `DimCustomer[CustomerId]` | `FactReturns[CustomerId]` | 1:* | Single |
| `DimCustomer[CustomerId]` | `FactReviews[CustomerId]` | 1:* | Single |
| `DimCustomer[CustomerId]` | `FactRfmSnapshot[CustomerId]` | 1:* | Single |
| `DimProduct[ProductId]` | `FactOrderLines[ProductId]` | 1:* | Single |
| `DimProduct[ProductId]` | `FactReturns[ProductId]` | 1:* | Single |
| `DimProduct[ProductId]` | `FactReviews[ProductId]` | 1:* | Single |
| `DimChannel[ChannelId]` | `FactOrders[ChannelId]` | 1:* | Single |
| `DimChannel[ChannelId]` | `FactOrderLines[ChannelId]` | 1:* | Single |
| `DimChannel[ChannelId]` | `FactReturns[ChannelId]` | 1:* | Single |
| `DimGeography[GeographyKey]` | `FactOrders[GeographyKey]` | 1:* | Single |
| `DimGeography[GeographyKey]` | `FactOrderLines[GeographyKey]` | 1:* | Single |
| `DimGeography[GeographyKey]` | `FactReturns[GeographyKey]` | 1:* | Single |
| `DimPromotion[PromotionId]` | `FactOrders[PromotionId]` | 1:* | Single |
| `DimPromotion[PromotionId]` | `FactOrderLines[PromotionId]` | 1:* | Single |
| `DimPromotion[PromotionId]` | `FactReturns[PromotionId]` | 1:* | Single |
| `DimPromotion[PromotionId]` | `FactCampaignPerformance[PromotionId]` | 1:* | Single |

The data audit found zero duplicate dimension keys and zero non-null orphans for all 24 relationships. Blank promotion foreign keys are expected for non-promoted transactions.

Do not create:

- Fact-to-fact relationships.
- Relationships to `FactCohortRetention`.
- Relationships to any `Validation*` table.
- Bidirectional or many-to-many relationships.
- A relationship from `DimPromotion[ChannelId]` to `DimChannel`; this creates an unwanted dimension-to-dimension path.

Mark `DimDate[FullDate]` as the date table. Sort `DimDate[MonthName]` by `MonthNumber`. If `YearMonth` does not sort chronologically in Desktop, create a Power Query-only sort field from `DateKey` rather than a DAX business column.

## 5. Configure model metadata

Create hierarchies:

- Product: `CategoryName > SubcategoryName > ProductName`.
- Geography: `Region > StateProvince > City`.
- Date: `CalendarYear > CalendarQuarter > MonthName > FullDate`.

Hide:

- All foreign keys and technical date keys.
- `OrderItemId`, `ReturnItemId`, and `ReviewId` except on drill-through pages.
- Raw numeric fact columns after measures are created.
- `ReviewText` and `ReviewTitle` from ordinary report authors; retain them for detail pages.
- All `Validation*` tables.

Keep `OrderId`, `CustomerId`, `ProductId`, `PromotionId`, and SKU available for detail/drill-through pages.

## 6. Add the complete DAX layer

1. Select **Home > Enter data**.
2. Create a table named `_Measures` with one placeholder value.
3. Hide the placeholder column.
4. Open `powerbi/measures.dax`.
5. Add measures in file order because later measures reference earlier measures.
6. Apply descriptions, formats, and display folders from `powerbi/MEASURE_DICTIONARY.md`.
7. Validate the required measure list with `tests/test_powerbi_contract.py`.

The file contains 87 governed measures covering revenue, profit, sales, customers, CLV, churn, products, returns, delivery, reviews, campaigns, retention, time intelligence, ranking, Pareto, cancellation, promotion, and operational support.

## 7. Apply number formats

| Metric type | Format string | Examples |
|---|---|---|
| Whole counts | `#,0` | Orders, customers, units, reviews |
| Currency totals | `$#,0;($#,0);-` | Revenue, profit, refunds |
| Currency averages | `$#,0.00` | AOV, CLV, profit per conversion |
| Percentages | `0.0%;(0.0%);-` | Margin, growth, return rate |
| Ratings | `0.00` | Average rating |
| Days | `0.0` | Delivery days, purchase gaps |
| Ranks | `#,0` | Product/customer rank |
| Dates | `dd MMM yyyy` | Event dates |
| Month labels | `MMM yyyy` | Trend axes |

Use display units `None` on KPI cards below $1 million and `Millions` with one decimal above $1 million. Never mix K/M automatic units across comparable visuals.

## 8. Global report shell

- Page size: 16:9.
- Outer margin: 24 px; visual gap: 16 px.
- Header: 56 px high with page title left and selected date context right.
- Left navigation: 144 px wide with six Page Navigator buttons.
- Visual corners: 6 px; shadow off; 1 px `#E2E8F0` border only when separation is needed.
- Visual titles: Segoe UI Semibold 12 pt, left aligned.
- KPI labels: 10–11 pt; callout values: 24–28 pt.
- Background: `#F8FAFC`; visual surface: white.
- Global slicers: Date, Channel, Region, Category. Sync them only to pages where their fact coverage is valid.
- Add a Reset Filters bookmark per page and a Definitions button opening a measure glossary panel.

## 9. Page 1 — Executive Overview

Title: **Executive Overview — Growth, Profitability, and Customer Health**

Slicers:

- `DimDate[FullDate]`: Relative date or Between.
- `DimChannel[ChannelName]`: Dropdown.
- `DimGeography[Region]`: Dropdown.
- `DimProduct[CategoryName]`: Dropdown; disable its interaction with order-only cards if product filtering is not intended there.

KPI cards:

| Card | Measure | Secondary label / formatting |
|---|---|---|
| Revenue | `Revenue After Refund` | `Revenue YoY %`; blue |
| Profit | `Gross Profit After Refund` | `Gross Profit YoY %`; teal |
| Margin | `Gross Margin After Refund %` | red only below benchmark |
| Orders | `Orders` | `Orders YoY %` |
| Customers | `Active Customers` | `Active Customer YoY %` |
| AOV | `Average Order Value` | currency, two decimals |

Visuals:

1. Line chart — title **Revenue Trend and Rolling Baseline**. X: `DimDate[YearMonth]`; Y: `Revenue After Refund`, `Rolling 12M Revenue`. Primary solid blue; rolling line dashed slate.
2. Clustered bar — title **Revenue and Profit by Channel**. Y: `DimChannel[ChannelName]`; X: `Revenue After Refund`, `Gross Profit After Refund`. Sort descending by revenue.
3. Bar chart — title **Category Contribution**. Y: `DimProduct[CategoryName]`; X: `Product Revenue`; tooltip: `Product Gross Profit`, `Product Gross Margin %`, `Return Rate`.
4. Exception strip — `Refund Rate`, `Return Rate`, `Late Delivery %`, `Churn Indicator %`. Use icon + label, not color alone.

## 10. Page 2 — Sales Performance

Title: **Sales Performance — Trend, Channel, and Regional Drivers**

Slicers: Date, Channel, Region, Customer Segment.

KPI cards: `Revenue`, `Revenue MoM %`, `Revenue YoY %`, `Rolling 3M Revenue`, `Rolling 12M Revenue`, `Average Order Value`.

Visuals:

1. Combo chart — title **Monthly Revenue vs Prior Year**. X: `DimDate[YearMonth]`; columns: `Revenue`; line: `Revenue Previous Year`.
2. Matrix — title **Regional Channel Performance**. Rows: `DimGeography[Region]`; columns: `DimChannel[ChannelName]`; values: `Revenue After Refund`, `Gross Margin After Refund %`, `Orders`. Apply diverging background only to margin.
3. Ribbon chart — title **Channel Revenue Rank Over Time**. Axis: `DimDate[YearMonth]`; legend: ChannelName; value: Revenue.
4. Waterfall — title **Revenue Leakage to After-Refund Profit**. Use a disconnected bridge created manually only after base pages work; values derive from Gross Revenue, Discount Amount, Refund Amount, and Gross Profit After Refund.
5. Detail table — Month, Channel, Region, Revenue, Orders, AOV, MoM %, YoY %. Use data bars for revenue and icons for growth.

## 11. Page 3 — Customer Analytics

Title: **Customer Analytics — Retention, Value, and Churn Risk**

Slicers: Date, `DimCustomer[SegmentName]`, AcquisitionSource, LifecycleStatus, `FactRfmSnapshot[RfmSegment]`.

KPI cards: `Active Customers`, `New Customers`, `Repeat Customers`, `Average Historical CLV`, `Projected 12M Customer Value`, `Revenue at Risk`.

Visuals:

1. Cohort matrix — title **Monthly Cohort Retention**. Rows: `FactCohortRetention[CohortMonth]`; columns: MonthsSinceFirstOrder; values: `Retention %`. Disable totals. Sequential blue scale from 0% to 100%.
2. Horizontal bars — title **RFM Segment Size and Value**. Y: RfmSegment; X: `RFM Customers`; tooltip: `RFM Monetary Value`, `RFM Customer Share %`.
3. Scatter — title **Customer Value vs Recency**. X: DimCustomer RecencyDays; Y: LifetimeRevenueAfterRefund; legend: LifecycleStatus; details: CustomerId. Use transparency and avoid labels on every point.
4. Pareto table/line — CustomerId, Customer Revenue Rank, Pareto Revenue %. Add an 80% constant line.
5. Risk table — CustomerId, SegmentName, LifecycleStatus, RecencyDays, LifetimeOrders, LifetimeRevenueAfterRefund, Projected12MonthRevenue. Apply red/amber labeled status icons.

Date slicers do not filter the disconnected cohort fact. Make this explicit in an information tooltip.

## 12. Page 4 — Product & Category Analytics

Title: **Product & Category Analytics — Profitable Growth and Quality**

Slicers: Date, Category, Subcategory, Brand, Channel.

KPI cards: `Product Revenue`, `Product Gross Profit`, `Product Gross Margin %`, `Units Sold`, `Return Rate`, `Average Rating`.

Visuals:

1. Decomposition tree — Analyze `Product Gross Profit`; explain by CategoryName, SubcategoryName, BrandName, ProductName.
2. Scatter — title **Product Portfolio: Scale vs Margin**. X: Product Revenue; Y: Product Gross Margin %; size: Units Sold; details: ProductName; legend: CategoryName.
3. Ranked bar — title **Top 15 Products by Revenue**. Y: ProductName; X: Product Revenue; tooltip includes rank, profit, margin, units, return rate, rating.
4. Matrix — Category > Subcategory > Product; values: Product Revenue, Product Gross Profit, Product Gross Margin %, Units Sold, Return Rate, Average Rating. Red icon for high returns only when volume is material.
5. Pareto line — X: Product Revenue Rank; Y: cumulative share using a product-specific extension if added later. Do not reuse customer Pareto measures for products.

## 13. Page 5 — Marketing & Campaign Performance

Title: **Marketing Performance — Conversion, Attribution, and Discount Efficiency**

Slicers: `DimDate[FullDate]`, `DimPromotion[PromotionType]`, `DimPromotion[PromotionName]`. Use Channel slicer only for order-based visuals; campaign rows do not have a direct DimChannel relationship by design.

KPI cards: `Campaign Audience`, `Campaign CTR %`, `Campaign Conversion %`, `Attributed Orders`, `Attributed Revenue`, `Attributed Gross Profit`.

Visuals:

1. Funnel — title **Campaign Funnel**. Values: Audience, Clicks, Conversions. Use direct labels.
2. Scatter — title **Attributed Revenue vs Discount Cost**. X: Campaign Discount Cost; Y: Attributed Revenue; size: Attributed Gross Profit; details: PromotionName.
3. Bar chart — title **Attributed Profit by Campaign**. Y: PromotionName; X: Attributed Gross Profit; sort descending.
4. Matrix — PromotionName, PromotionType, Campaign Audience, Campaign CTR %, Campaign Conversion %, Attributed Orders, Attributed Revenue, Attributed Gross Profit, Campaign Profit per Conversion.
5. Order-side promotion cards: `Promotion Orders`, `Promotion Order Rate`, `Attributed Average Order Value`. Label direct attribution as descriptive, not incremental ROAS.

## 14. Page 6 — Operations, Returns & Satisfaction

Title: **Operations & Customer Experience — Delivery, Returns, and Reviews**

Slicers: Date, Carrier, Region, Category, ReturnReason, Rating.

KPI cards: `On-Time Delivery %`, `Average Delivery Days`, `Late Deliveries`, `Return Rate`, `Refund Amount`, `Average Rating`.

Visuals:

1. Line chart — title **On-Time Delivery Trend**. X: YearMonth; Y: On-Time Delivery %. Add a clearly labeled reference line only if a business target is defined.
2. Matrix — title **Carrier and Region SLA Performance**. Rows: FactOrders Carrier; columns: DimGeography Region; values: Delivered Orders, On-Time Delivery %, Average Delivery Days, Late Deliveries.
3. Horizontal bars — title **Return Reasons by Refunded Value**. Y: FactReturns ReturnReason; X: `Return Refund Amount`; tooltip: `Return Event Units`. Do not show the sold-cohort Return Rate by return reason because its denominator is not filtered by that fact attribute.
4. Combo chart — title **Rating and Observed Return Behavior**. X: FactReviews Rating; columns: Reviews; line: Reviewed Item Return Rate.
5. Product exception table — ProductName, Product Revenue, Return Rate, Product Refund Amount, Average Rating, Low Rating Review %. Require a minimum units threshold before escalating a product.

## 15. Drill-through and tooltip pages

Create hidden drill-through pages:

- Customer 360: `CustomerId`.
- Product Detail: `ProductId`.
- Order Detail: `OrderId`.
- Campaign Detail: `PromotionId`.

Create report-page tooltips for Product, Campaign, Customer Segment, and Delivery Lane. Limit each tooltip to four measures and one small trend.

## 16. Interaction rules

- Dimension slicers filter related facts through single-direction relationships.
- Disable Category interaction with order-grain visuals that do not use FactOrderLines.
- Disable Rating interaction with delivery visuals.
- Do not synchronize RFM segment or cohort controls across unrelated pages.
- Use cross-filter rather than cross-highlight when part-to-whole interpretation would otherwise be unclear.
- Keep each page below eight visible analytical visuals, excluding navigation and slicers.

## 17. Reconciliation and acceptance

Before formatting details, reconcile:

1. Revenue.
2. Revenue After Refund.
3. Gross Profit.
4. Gross Profit After Refund.
5. Refund Amount.
6. Orders.

Compare atomic model measures to the corresponding hidden `Validation*` tables at their exact grain. Do not create relationships merely to make validation tables respond to slicers.

Then complete `docs/POWER_BI_MANUAL_CHECKLIST.md` and `docs/DEPLOYMENT_VALIDATION.md`.

## 18. Save as PBIP after Desktop validation

Power BI Project files are still a preview/developer-mode format and Power BI Desktop is the supported creator/converter. After the `.pbix` opens, refreshes, and validates successfully:

1. Enable **Store semantic model using TMDL format** in Preview features.
2. Select **File > Save As > Power BI Project (.pbip)**.
3. Close and reopen the `.pbip` to verify external files load.
4. Commit the generated Report and SemanticModel folders only after removing `.pbi` cache/local settings and reviewing source paths.

Do not hand-author unsupported report layout or diagram files. Microsoft documents that external edits can prevent Desktop from opening the project, and PBIX/PBIP conversion is supported through Power BI Desktop rather than programmatically.
