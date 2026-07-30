# Data Dictionary

## Core transactional tables

| Table | Grain | Primary key | Important fields |
|---|---|---|---|
| `ecommerce.CustomerSegments` | One behavioral segment | `SegmentId` | segment name and business description |
| `ecommerce.Customers` | One customer | `CustomerId` | email, acquisition date/source, segment, active flag |
| `ecommerce.Addresses` | One customer address | `AddressId` | type, city, state, region, country, default flag |
| `ecommerce.Categories` | One product category | `CategoryId` | name, optional parent category |
| `ecommerce.Products` | One sellable SKU | `ProductId` | SKU, brand, category, unit cost, list price, launch date |
| `ecommerce.Promotions` | One time-bound promotion | `PromotionId` | code, type, value, threshold, active dates, channel |
| `ecommerce.Orders` | One order | `OrderId` | customer, channel, status, promotion, date, shipping, tax |
| `ecommerce.OrderItems` | One product line per order | `OrderItemId` | quantity, historical price/cost, discount |
| `ecommerce.Payments` | One payment attempt | `PaymentId` | method, status, amount, reference |
| `ecommerce.Shipments` | One shipment per order | `ShipmentId` | carrier, ship/promise/delivery dates, status |
| `ecommerce.Returns` | One return case | `ReturnId` | order, date, reason, status |
| `ecommerce.ReturnItems` | One line in a return | `ReturnItemId` | source order line, quantity, refund |
| `ecommerce.ProductReviews` | One verified review per order line | `ReviewId` | customer, product, rating, text, helpful votes |
| `ecommerce.CampaignInteractions` | One customer-campaign event | `InteractionId` | promotion, event type, channel, attributed order |

## Analytics objects

### `analytics.vw_OrderLineAnalytics`

Grain: one order item. Use for product/category revenue, unit economics, discount analysis, and regional/channel product mix.

| Field | Definition |
|---|---|
| `GrossRevenue` | `Quantity × UnitPrice` |
| `NetRevenue` | `GrossRevenue − DiscountAmount` |
| `COGS` | `Quantity × UnitCost` |
| `GrossProfit` | `NetRevenue − COGS` |
| `RefundAmount` | Non-rejected refund amount recorded for the order line |
| `RevenueAfterRefund` | `NetRevenue − RefundAmount` |
| `GrossProfitAfterRefund` | Conservative proxy: `GrossProfit − RefundAmount` |
| `DiscountRate` | `DiscountAmount ÷ GrossRevenue` |

### `analytics.vw_OrderSummary`

Grain: one order. Cancelled orders retain gross and discount values for diagnostics but report zero net revenue and gross profit. Valid orders are sequenced per customer for repeat-purchase analysis.

| Field | Definition |
|---|---|
| `Units` | Sum of ordered quantity |
| `NetRevenue` | Non-cancelled line net revenue |
| `RevenueAfterRefund` | Booked net revenue less non-rejected refunds |
| `RefundAmount` | Sum of recorded return-item refunds |
| `CustomerOrderNumber` | Chronological non-cancelled order sequence for the customer |
| `IsRepeatPurchase` | 1 when the valid customer order number is greater than one |
| `DeliveryDays` | Calendar days from order to delivery |
| `IsOnTime` | 1 when delivery date is on/before promise, 0 when late, null when undelivered |

### `analytics.vw_CustomerMetrics`

Grain: one customer, including customers with no orders. Lifetime metrics exclude cancelled orders. `IsRepeatCustomer` is 1 after two valid orders.

| Field | Definition |
|---|---|
| `RecencyDays` | Days from the last valid order to the dataset as-of date |
| `AvgDaysBetweenOrders` | Average gap between consecutive valid orders |
| `Projected12MonthRevenue` | Annualized historical after-refund revenue over observed tenure, with a 90-day minimum observation window |
| `LifecycleStatus` | Rules-based state: Prospect, Active, One-Time Lapsed, At Risk, or High Risk |

### `analytics.vw_MonthlyKpis`

Grain: one calendar month across the observed order range. Months with no sales remain present through the date dimension.

### `analytics.vw_MonthlyPerformance`

Grain: one month. Adds prior-month and prior-year revenue, MoM/YoY growth, 3/12-month rolling averages, and cumulative revenue.

### `analytics.vw_CohortRetention`

Grain: one acquisition cohort and elapsed month. A customer is active once per month, and cohort membership is based on first valid order month.

### `analytics.vw_ProductPerformance`

Grain: one product. Combines orders, units, revenue, after-refund revenue, gross profit, discount rate, return rate, review count, and average rating.

### `analytics.vw_ReturnAnalysis`

Grain: one returned order line. `LineReturnRate` compares the returned quantity with the purchased quantity for that order line.

### `analytics.vw_ProductReviewAnalytics`

Grain: one product review. Adds customer segment, brand, category hierarchy, and a return indicator to support voice-of-customer and quality analysis.

### `analytics.vw_CampaignPerformance`

Grain: one promotion. Combines audience, clicks, conversions, attributed revenue, attributed gross profit, click-through rate, and click-to-conversion rate.

### `analytics.DimDate`

Grain: one calendar date, 2023-01-01 through 2026-12-31 in the default build. `DateKey` uses integer `YYYYMMDD` format.

## Metric caveats

- Gross profit is a merchandise margin and does not subtract tax, freight expense, marketing, labor, or overhead.
- `NetRevenue` represents booked non-cancelled sales; use `RevenueAfterRefund` when refund leakage should be recognized.
- `GrossProfitAfterRefund` is conservative because returned inventory recovery and disposition are not modeled.
- Projected customer value is an explainable annualized run rate, not a trained predictive lifetime-value model.
- Campaign attribution is direct promotion attribution and does not measure causal incrementality.
- Synthetic data is suitable for demonstration and testing, not industry benchmarking.
