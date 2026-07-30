# Power Query Catalog

Create a Text parameter named `CsvRoot`, then create the `fnLoadCsv` function from the adjacent M files. Create one blank query per row below and use the supplied expression in Advanced Editor. The expressions preserve source columns and apply deterministic types; no business metrics are recalculated in Power Query.

## Core dimensions and facts

### DimDate

```powerquery
fnLoadCsv("dim_date.csv", {{"DateKey", Int64.Type}, {"FullDate", type date}, {"CalendarYear", Int64.Type}, {"CalendarQuarter", type text}, {"MonthNumber", Int64.Type}, {"MonthName", type text}, {"YearMonth", type text}, {"WeekOfYear", Int64.Type}, {"DayOfMonth", Int64.Type}, {"DayName", type text}, {"IsWeekend", Int64.Type}})
```

### DimCustomer

```powerquery
fnLoadCsv("dim_customers.csv", {{"CustomerId", Int64.Type}, {"AcquisitionDate", type datetime}, {"AcquisitionSource", type text}, {"SegmentName", type text}, {"IsActive", Int64.Type}, {"FirstOrderDate", type datetime}, {"LastOrderDate", type datetime}, {"LifetimeOrders", Int64.Type}, {"LifetimeRevenue", Currency.Type}, {"LifetimeRevenueAfterRefund", Currency.Type}, {"LifetimeGrossProfit", Currency.Type}, {"AverageOrderValue", Currency.Type}, {"AvgDaysBetweenOrders", type number}, {"RecencyDays", Int64.Type}, {"IsRepeatCustomer", Int64.Type}, {"Projected12MonthRevenue", Currency.Type}, {"LifecycleStatus", type text}})
```

### DimProduct

```powerquery
fnLoadCsv("dim_products.csv", {{"ProductId", Int64.Type}, {"SKU", type text}, {"ProductName", type text}, {"BrandName", type text}, {"CategoryId", Int64.Type}, {"UnitCost", Currency.Type}, {"ListPrice", Currency.Type}, {"LaunchDate", type datetime}, {"IsActive", Int64.Type}, {"SubcategoryName", type text}, {"ParentCategoryId", Int64.Type}, {"CategoryName", type text}})
```

### DimChannel

```powerquery
fnLoadCsv("dim_channels.csv", {{"ChannelId", Int64.Type}, {"ChannelName", type text}})
```

### DimGeography

```powerquery
fnLoadCsv("dim_geography.csv", {{"GeographyKey", Int64.Type}, {"City", type text}, {"StateProvince", type text}, {"Region", type text}, {"CountryCode", type text}})
```

### DimPromotion

```powerquery
fnLoadCsv("dim_promotions.csv", {{"PromotionId", Int64.Type}, {"PromotionCode", type text}, {"PromotionName", type text}, {"PromotionType", type text}, {"DiscountValue", Currency.Type}, {"MinimumOrderValue", Currency.Type}, {"StartDate", type datetime}, {"EndDate", type datetime}, {"ChannelId", Int64.Type}})
```

### FactOrders

```powerquery
fnLoadCsv("fact_orders.csv", {{"OrderId", Int64.Type}, {"OrderDateKey", Int64.Type}, {"OrderDate", type datetime}, {"CustomerId", Int64.Type}, {"CustomerOrderNumber", Int64.Type}, {"IsRepeatPurchase", Int64.Type}, {"ChannelId", Int64.Type}, {"GeographyKey", Int64.Type}, {"StatusName", type text}, {"Units", Int64.Type}, {"GrossRevenue", Currency.Type}, {"DiscountAmount", Currency.Type}, {"NetRevenue", Currency.Type}, {"RevenueAfterRefund", Currency.Type}, {"GrossProfit", Currency.Type}, {"GrossProfitAfterRefund", Currency.Type}, {"RefundAmount", Currency.Type}, {"ReturnedUnits", Int64.Type}, {"PromotionId", Int64.Type}, {"Carrier", type text}, {"ShippedDate", type datetime}, {"PromisedDeliveryDate", type datetime}, {"DeliveredDate", type datetime}, {"DeliveryDays", Int64.Type}, {"IsOnTime", Int64.Type}})
```

### FactOrderLines

```powerquery
fnLoadCsv("fact_order_lines.csv", {{"OrderItemId", Int64.Type}, {"OrderId", Int64.Type}, {"OrderDateKey", Int64.Type}, {"CustomerId", Int64.Type}, {"ProductId", Int64.Type}, {"Quantity", Int64.Type}, {"UnitPrice", Currency.Type}, {"UnitCost", Currency.Type}, {"GrossRevenue", Currency.Type}, {"DiscountAmount", Currency.Type}, {"NetRevenue", Currency.Type}, {"RevenueAfterRefund", Currency.Type}, {"COGS", Currency.Type}, {"GrossProfit", Currency.Type}, {"GrossProfitAfterRefund", Currency.Type}, {"ReturnedQuantity", Int64.Type}, {"RefundAmount", Currency.Type}, {"DiscountRate", Percentage.Type}, {"IsValidOrder", Int64.Type}, {"ChannelId", Int64.Type}, {"PromotionId", Int64.Type}, {"GeographyKey", Int64.Type}})
```

### FactReturns

```powerquery
fnLoadCsv("fact_returns.csv", {{"ReturnItemId", Int64.Type}, {"ReturnId", Int64.Type}, {"OrderItemId", Int64.Type}, {"OrderId", Int64.Type}, {"ReturnDateKey", Int64.Type}, {"ReturnDate", type datetime}, {"OrderDateKey", Int64.Type}, {"CustomerId", Int64.Type}, {"ProductId", Int64.Type}, {"ChannelId", Int64.Type}, {"PromotionId", Int64.Type}, {"GeographyKey", Int64.Type}, {"ReturnReason", type text}, {"ReturnStatus", type text}, {"ReturnQuantity", Int64.Type}, {"RefundAmount", Currency.Type}, {"LineReturnRate", Percentage.Type}})
```

### FactReviews

```powerquery
fnLoadCsv("fact_reviews.csv", {{"ReviewId", Int64.Type}, {"ReviewDateKey", Int64.Type}, {"ReviewDate", type datetime}, {"CustomerId", Int64.Type}, {"ProductId", Int64.Type}, {"OrderItemId", Int64.Type}, {"Rating", Int64.Type}, {"ReviewTitle", type text}, {"ReviewText", type text}, {"IsVerifiedPurchase", Int64.Type}, {"HelpfulVotes", Int64.Type}, {"WasReturned", Int64.Type}})
```

### FactCampaignPerformance

```powerquery
fnLoadCsv("campaign_performance.csv", {{"PromotionId", Int64.Type}, {"PromotionCode", type text}, {"PromotionName", type text}, {"PromotionType", type text}, {"DiscountValue", Currency.Type}, {"MinimumOrderValue", Currency.Type}, {"StartDate", type datetime}, {"EndDate", type datetime}, {"ChannelId", Int64.Type}, {"Audience", Int64.Type}, {"Clicks", Int64.Type}, {"Conversions", Int64.Type}, {"AttributedOrders", Int64.Type}, {"AttributedRevenue", Currency.Type}, {"AttributedRevenueAfterRefund", Currency.Type}, {"AttributedGrossProfit", Currency.Type}, {"DiscountCost", Currency.Type}, {"ClickThroughRate", Percentage.Type}, {"ClickToConversionRate", Percentage.Type}, {"StartDateKey", Int64.Type}, {"EndDateKey", Int64.Type}})
```

### FactCohortRetention

```powerquery
fnLoadCsv("cohort_retention.csv", {{"CohortMonth", type datetime}, {"MonthsSinceFirstOrder", Int64.Type}, {"ActiveCustomers", Int64.Type}, {"CohortSize", Int64.Type}, {"RetentionRate", Percentage.Type}})
```

### FactRfmSnapshot

```powerquery
fnLoadCsv("rfm_segments.csv", {{"CustomerId", Int64.Type}, {"LastOrderDate", type datetime}, {"Frequency", Int64.Type}, {"MonetaryValue", Currency.Type}, {"SnapshotDate", type datetime}, {"RecencyDays", Int64.Type}, {"RScore", Int64.Type}, {"FScore", Int64.Type}, {"MScore", Int64.Type}, {"RfmCode", type text}, {"RfmSegment", type text}, {"SnapshotDateKey", Int64.Type}})
```

## Disconnected validation aggregates

Use the same helper and query names from `table_manifest.csv`. Keep these tables hidden and do not create relationships.

```powerquery
// ValidationAcquisition
fnLoadCsv("acquisition_performance.csv", {{"AcquisitionSource", type text}, {"Customers", Int64.Type}, {"Orders", Int64.Type}, {"RevenueAfterRefund", Currency.Type}, {"GrossProfit", Currency.Type}, {"AverageOrderValue", Currency.Type}, {"RepeatOrders", Int64.Type}, {"AcquiredCustomers", Int64.Type}, {"PurchaserConversionRate", Percentage.Type}, {"RevenuePerPurchaser", Currency.Type}, {"RepeatOrderRate", Percentage.Type}})

// ValidationCategory
fnLoadCsv("category_performance.csv", {{"CategoryName", type text}, {"Products", Int64.Type}, {"Orders", Int64.Type}, {"UnitsSold", Int64.Type}, {"NetRevenue", Currency.Type}, {"RevenueAfterRefund", Currency.Type}, {"GrossProfit", Currency.Type}, {"ReturnedUnits", Int64.Type}, {"RefundAmount", Currency.Type}, {"DiscountAmount", Currency.Type}, {"GrossMarginRate", Percentage.Type}, {"UnitReturnRate", Percentage.Type}, {"RefundToRevenueRate", Percentage.Type}})

// ValidationDelivery
fnLoadCsv("delivery_performance.csv", {{"Carrier", type text}, {"Region", type text}, {"DeliveredOrders", Int64.Type}, {"AverageDeliveryDays", type number}, {"MedianDeliveryDays", type number}, {"OnTimeRate", Percentage.Type}, {"LateOrders", Int64.Type}})

// ValidationDiscount
fnLoadCsv("discount_effectiveness.csv", {{"MonthStart", type datetime}, {"ChannelName", type text}, {"PromotionGroup", type text}, {"Orders", Int64.Type}, {"AverageOrderValue", Currency.Type}, {"RevenueAfterRefund", Currency.Type}, {"GrossProfit", Currency.Type}, {"DiscountCost", Currency.Type}, {"GrossProfitPerOrder", Currency.Type}})

// ValidationMonthly
fnLoadCsv("monthly_performance.csv", {{"MonthStart", type datetime}, {"Orders", Int64.Type}, {"ActiveCustomers", Int64.Type}, {"RepeatOrders", Int64.Type}, {"NetRevenue", Currency.Type}, {"RevenueAfterRefund", Currency.Type}, {"GrossProfit", Currency.Type}, {"AverageOrderValue", Currency.Type}, {"Discounts", Currency.Type}, {"ReturnedUnits", Int64.Type}, {"PreviousMonthRevenue", Currency.Type}, {"PreviousYearRevenue", Currency.Type}, {"RevenueMoMPct", Percentage.Type}, {"RevenueYoYPct", Percentage.Type}, {"Rolling3MonthRevenue", Currency.Type}, {"Rolling12MonthRevenue", Currency.Type}, {"RunningRevenue", Currency.Type}, {"GrossMarginRate", Percentage.Type}, {"RepeatOrderRate", Percentage.Type}})

// ValidationPareto
fnLoadCsv("pareto_curve.csv", {{"CustomerId", Int64.Type}, {"LifetimeRevenueAfterRefund", Currency.Type}, {"CustomerRank", Int64.Type}, {"CumulativeCustomerShare", Percentage.Type}, {"CumulativeRevenueShare", Percentage.Type}})

// ValidationProduct
fnLoadCsv("product_performance.csv", {{"ProductId", Int64.Type}, {"SKU", type text}, {"ProductName", type text}, {"BrandName", type text}, {"SubcategoryName", type text}, {"CategoryName", type text}, {"Orders", Int64.Type}, {"UnitsSold", Int64.Type}, {"GrossRevenue", Currency.Type}, {"DiscountAmount", Currency.Type}, {"NetRevenue", Currency.Type}, {"RevenueAfterRefund", Currency.Type}, {"GrossProfit", Currency.Type}, {"ReturnedUnits", Int64.Type}, {"RefundAmount", Currency.Type}, {"Reviews", Int64.Type}, {"AverageRating", type number}, {"GrossMarginRate", Percentage.Type}, {"UnitReturnRate", Percentage.Type}, {"DiscountRate", Percentage.Type}})

// ValidationRegionalChannel
fnLoadCsv("regional_channel_performance.csv", {{"Region", type text}, {"ChannelName", type text}, {"Orders", Int64.Type}, {"Customers", Int64.Type}, {"RevenueAfterRefund", Currency.Type}, {"GrossProfit", Currency.Type}, {"RepeatOrders", Int64.Type}, {"GrossMarginRate", Percentage.Type}, {"RepeatOrderRate", Percentage.Type}})

// ValidationReviewReturn
fnLoadCsv("review_return_relationship.csv", {{"Rating", Int64.Type}, {"Reviews", Int64.Type}, {"ReturnedReviews", Int64.Type}, {"ReturnRate", Percentage.Type}})
```

## Required final settings

- Enable load for all 22 data queries because the delivery requirement explicitly includes every CSV.
- Hide all `Validation*` tables from report view and keep them disconnected.
- Disable load for `fnLoadCsv`; keep `CsvRoot` as a parameter.
- Use privacy level `Organizational` or `None` consistently for the single local folder source.
- Do not add index columns, joins, calculated business metrics, or inferred relationships in Power Query.
