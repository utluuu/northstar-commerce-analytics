/* Northstar Commerce | 05_advanced_analysis.sql
   Business-question-oriented portfolio analysis pack.
   Read sql/README_ANALYTICS.md before interpreting results. */
USE NorthstarCommerce;
GO

DECLARE @AnalysisStart date = '2023-01-01';
DECLARE @AnalysisEnd date = '2025-12-31';

/* ANALYSIS 01 — Executive revenue and profit trend
   Business question: Are revenue and merchandise profit growing sustainably?
   Why it matters: Growth without margin or after-refund growth can destroy value.
   SQL skills: LAG, 3/12-month rolling averages, running total, reusable view.
   Interpretation: Compare booked revenue, after-refund revenue, margin, MoM, and YoY together. */
SELECT MonthStart, Orders, ActiveCustomers, NetRevenue, RevenueAfterRefund, GrossProfit,
       AverageOrderValue, RevenueMoMPct, RevenueYoYPct,
       Rolling3MonthRevenueValue, Rolling12MonthRevenueValue, RunningRevenueValue
FROM analytics.vw_MonthlyPerformance
WHERE MonthStart >= @AnalysisStart AND MonthStart < DATEADD(day, 1, @AnalysisEnd)
ORDER BY MonthStart;

/* ANALYSIS 02 — Annual growth decomposition
   Business question: Is yearly revenue growth driven by more customers, more orders, or higher AOV?
   Why it matters: The growth lever determines whether retention, acquisition, or pricing needs attention.
   SQL skills: CTE, LAG, conditional aggregation, growth-rate calculation. */
WITH annual AS (
    SELECT YEAR(OrderDate) AS CalendarYear, COUNT(*) AS Orders,
           COUNT(DISTINCT CustomerId) AS ActiveCustomers,
           SUM(NetRevenue) AS NetRevenue, SUM(GrossProfit) AS GrossProfit,
           AVG(NetRevenue) AS AverageOrderValue
    FROM analytics.vw_OrderSummary
    WHERE StatusName <> 'Cancelled'
      AND OrderDateTime >= @AnalysisStart AND OrderDateTime < DATEADD(day, 1, @AnalysisEnd)
    GROUP BY YEAR(OrderDate)
), compared AS (
    SELECT *, LAG(NetRevenue) OVER (ORDER BY CalendarYear) AS PriorRevenue,
              LAG(Orders) OVER (ORDER BY CalendarYear) AS PriorOrders,
              LAG(ActiveCustomers) OVER (ORDER BY CalendarYear) AS PriorCustomers,
              LAG(AverageOrderValue) OVER (ORDER BY CalendarYear) AS PriorAOV
    FROM annual
)
SELECT CalendarYear, Orders, ActiveCustomers, NetRevenue, GrossProfit, AverageOrderValue,
       CAST((NetRevenue / NULLIF(PriorRevenue, 0) - 1) * 100 AS decimal(9,2)) AS RevenueYoYPct,
       CAST((Orders * 1.0 / NULLIF(PriorOrders, 0) - 1) * 100 AS decimal(9,2)) AS OrdersYoYPct,
       CAST((ActiveCustomers * 1.0 / NULLIF(PriorCustomers, 0) - 1) * 100 AS decimal(9,2)) AS CustomersYoYPct,
       CAST((AverageOrderValue / NULLIF(PriorAOV, 0) - 1) * 100 AS decimal(9,2)) AS AOVYoYPct
FROM compared
ORDER BY CalendarYear;

/* ANALYSIS 03 — Sales channel cross-analysis
   Business question: How has channel revenue mix shifted by year?
   Why it matters: Concentration or migration can change fees, ownership of customer data, and margin.
   SQL skills: PIVOT, date dimension, aggregation. */
SELECT ChannelName, ISNULL([2023], 0) AS Revenue2023,
       ISNULL([2024], 0) AS Revenue2024, ISNULL([2025], 0) AS Revenue2025
FROM (
    SELECT ChannelName, YEAR(OrderDate) AS OrderYear, RevenueAfterRefund
    FROM analytics.vw_OrderSummary
    WHERE StatusName <> 'Cancelled'
      AND OrderDateTime >= @AnalysisStart AND OrderDateTime < DATEADD(day, 1, @AnalysisEnd)
) source_data
PIVOT (SUM(RevenueAfterRefund) FOR OrderYear IN ([2023], [2024], [2025])) pivoted
ORDER BY ChannelName;

/* ANALYSIS 04 — Repeat-purchase timing
   Business question: How quickly do first-time customers place a second order?
   Why it matters: Time-to-second-order is an actionable early-retention KPI.
   SQL skills: LEAD, ROW_NUMBER-compatible order sequence, conditional aggregation. */
WITH ordered AS (
    SELECT CustomerId, CustomerOrderNumber, OrderDate,
           LEAD(OrderDate) OVER (PARTITION BY CustomerId ORDER BY OrderDateTime, OrderId) AS NextOrderDate
    FROM analytics.vw_OrderSummary
    WHERE StatusName <> 'Cancelled'
), first_orders AS (
    SELECT CustomerId, OrderDate AS FirstOrderDate, NextOrderDate,
           DATEDIFF(day, OrderDate, NextOrderDate) AS DaysToSecondOrder
    FROM ordered
    WHERE CustomerOrderNumber = 1
)
SELECT COUNT(*) AS FirstTimeCustomers,
       SUM(CASE WHEN DaysToSecondOrder <= 30 THEN 1 ELSE 0 END) AS RepeatedWithin30Days,
       SUM(CASE WHEN DaysToSecondOrder <= 60 THEN 1 ELSE 0 END) AS RepeatedWithin60Days,
       SUM(CASE WHEN DaysToSecondOrder <= 90 THEN 1 ELSE 0 END) AS RepeatedWithin90Days,
       CAST(AVG(CAST(DaysToSecondOrder AS decimal(12,2))) AS decimal(10,2)) AS AvgDaysToSecondOrder,
       CAST(SUM(CASE WHEN DaysToSecondOrder <= 90 THEN 1.0 ELSE 0 END) / NULLIF(COUNT(*), 0) AS decimal(9,4)) AS RepeatWithin90DayRate
FROM first_orders;

/* ANALYSIS 05 — Churn-risk prioritization
   Business question: Which valuable customers show abnormal purchase inactivity?
   Why it matters: Recency relative to personal cadence is more useful than one global cutoff.
   SQL skills: derived lifecycle classification, RANK, conditional filtering. */
SELECT CustomerId, SegmentName, LifetimeOrders, LifetimeRevenueAfterRefund,
       AverageOrderValue, AvgDaysBetweenOrders, RecencyDays, LifecycleStatus,
       RANK() OVER (PARTITION BY LifecycleStatus ORDER BY LifetimeRevenueAfterRefund DESC) AS ValueRankWithinRisk
FROM analytics.vw_CustomerMetrics
WHERE LifecycleStatus IN ('At Risk', 'High Risk', 'One-Time Lapsed')
ORDER BY CASE LifecycleStatus WHEN 'High Risk' THEN 1 WHEN 'At Risk' THEN 2 ELSE 3 END,
         ValueRankWithinRisk;

/* ANALYSIS 06 — Explainable customer lifetime-value tiers
   Business question: Which customers have the strongest observed and forward run-rate value?
   Why it matters: A transparent annualized value is easier to defend than an unexplained black box.
   SQL skills: NTILE, DENSE_RANK, multiple value definitions.
   Interpretation: Projected12MonthRevenue is an annualized historical run rate, not causal prediction. */
WITH valued AS (
    SELECT CustomerId, SegmentName, LifetimeOrders, LifetimeRevenueAfterRefund,
           LifetimeGrossProfit, Projected12MonthRevenue,
           NTILE(10) OVER (ORDER BY Projected12MonthRevenue) AS ProjectedValueDecile
    FROM analytics.vw_CustomerMetrics
    WHERE LifetimeOrders > 0
)
SELECT *, DENSE_RANK() OVER (ORDER BY LifetimeRevenueAfterRefund DESC) AS HistoricalValueRank
FROM valued
ORDER BY ProjectedValueDecile DESC, Projected12MonthRevenue DESC;

/* ANALYSIS 07 — RFM portfolio
   Business question: How should CRM audiences be prioritized by recency, frequency, and value?
   Why it matters: RFM translates purchase history into operational customer groups.
   SQL skills: transactional stored procedure, NTILE, persisted snapshot, TRY/CATCH.
   Usage: Run the refresh, then inspect the auditable snapshot below. */
-- EXEC analytics.usp_RefreshRfmSegments @AsOfDate = '2026-01-01';
SELECT SnapshotDate, Segment, COUNT(*) AS Customers,
       CAST(AVG(CAST(RecencyDays AS decimal(12,2))) AS decimal(10,2)) AS AvgRecencyDays,
       CAST(AVG(CAST(Frequency AS decimal(12,2))) AS decimal(10,2)) AS AvgFrequency,
       CAST(SUM(MonetaryValue) AS decimal(18,2)) AS SegmentValue
FROM analytics.CustomerRfmSnapshot
WHERE SnapshotDate = (SELECT MAX(SnapshotDate) FROM analytics.CustomerRfmSnapshot)
GROUP BY SnapshotDate, Segment
ORDER BY SegmentValue DESC;

/* ANALYSIS 08 — Cohort retention curve
   Business question: Are newer acquisition cohorts retaining better than earlier cohorts?
   Why it matters: Aggregate repeat rate can hide cohort deterioration.
   SQL skills: layered CTEs and window functions encapsulated in a reusable view. */
SELECT CohortMonth, MonthsSinceFirstOrder, ActiveCustomers, CohortSize, RetentionRate,
       LAG(RetentionRate) OVER (PARTITION BY CohortMonth ORDER BY MonthsSinceFirstOrder) AS PreviousMonthRetention
FROM analytics.vw_CohortRetention
WHERE MonthsSinceFirstOrder <= 12
ORDER BY CohortMonth, MonthsSinceFirstOrder;

/* ANALYSIS 09 — Product and category portfolio
   Business question: Which products lead revenue, profit, and quality within each category?
   Why it matters: Revenue-only rankings can promote low-margin or high-return products.
   SQL skills: DENSE_RANK, ROW_NUMBER, partitioned ranking, multi-metric view. */
WITH ranked AS (
    SELECT *,
           DENSE_RANK() OVER (PARTITION BY CategoryName ORDER BY NetRevenue DESC) AS RevenueRank,
           DENSE_RANK() OVER (PARTITION BY CategoryName ORDER BY GrossProfit DESC) AS ProfitRank,
           ROW_NUMBER() OVER (PARTITION BY CategoryName ORDER BY UnitReturnRate, ProductId) AS ReturnQualityRowNumber
    FROM analytics.vw_ProductPerformance
    WHERE Orders >= 25
)
SELECT CategoryName, ProductId, ProductName, Orders, UnitsSold, NetRevenue, GrossProfit,
       GrossMarginRate, UnitReturnRate, AverageRating, RevenueRank, ProfitRank, ReturnQualityRowNumber
FROM ranked
WHERE RevenueRank <= 5 OR ProfitRank <= 5
ORDER BY CategoryName, RevenueRank, ProfitRank;

/* ANALYSIS 10 — Product affinity / market basket
   Business question: Which products appear together more often than independent chance predicts?
   Why it matters: Lift supports bundle, recommendation, and merchandising hypotheses.
   SQL skills: temporary table, self-join, support, confidence, lift, parameterized procedure. */
-- EXEC analytics.usp_ProductAffinity
--     @StartDate = '2025-01-01', @EndDate = '2025-12-31',
--     @MinimumPairOrders = 25, @TopN = 50;

/* ANALYSIS 11 — Return and refund exposure
   Business question: Which categories create the largest return rate and refund burden?
   Why it matters: Unit return rate and refund dollars reveal different operational priorities.
   SQL skills: conditional aggregation, ratio safety with NULLIF, ranking. */
WITH category_returns AS (
    SELECT CategoryName, SUM(UnitsSold) AS UnitsSold, SUM(ReturnedUnits) AS ReturnedUnits,
           SUM(RefundAmount) AS RefundAmount, SUM(NetRevenue) AS NetRevenue,
           SUM(GrossProfit) AS GrossProfit
    FROM analytics.vw_ProductPerformance
    GROUP BY CategoryName
)
SELECT *,
       CAST(ReturnedUnits * 1.0 / NULLIF(UnitsSold, 0) AS decimal(9,4)) AS UnitReturnRate,
       CAST(RefundAmount / NULLIF(NetRevenue, 0) AS decimal(9,4)) AS RefundToRevenueRate,
       RANK() OVER (ORDER BY RefundAmount DESC) AS RefundExposureRank
FROM category_returns
ORDER BY RefundExposureRank;

/* ANALYSIS 12 — Delivery performance
   Business question: Which carrier-region lanes miss promises or deliver slowly?
   Why it matters: Lane-level evidence supports routing and SLA decisions.
   SQL skills: conditional aggregation, HAVING, percentile-friendly detail grain. */
SELECT Carrier, Region, COUNT(*) AS DeliveredOrders,
       CAST(AVG(CAST(DeliveryDays AS decimal(10,2))) AS decimal(10,2)) AS AvgDeliveryDays,
       CAST(AVG(CAST(IsOnTime AS decimal(9,4))) AS decimal(9,4)) AS OnTimeRate,
       SUM(CASE WHEN IsOnTime = 0 THEN 1 ELSE 0 END) AS LateOrders,
       RANK() OVER (ORDER BY AVG(CAST(IsOnTime AS decimal(9,4))), AVG(CAST(DeliveryDays AS decimal(10,2))) DESC) AS ServiceRiskRank
FROM analytics.vw_OrderSummary
WHERE DeliveredDate IS NOT NULL
GROUP BY Carrier, Region
HAVING COUNT(*) >= 100
ORDER BY ServiceRiskRank;

/* ANALYSIS 13 — Campaign funnel and attributed economics
   Business question: Which campaigns convert engagement into revenue and gross profit?
   Why it matters: High conversion without profit can reflect excessive discounting.
   SQL skills: conditional aggregation, direct attribution, safe funnel ratios.
   Interpretation: Attribution is descriptive and does not estimate incremental lift. */
SELECT PromotionCode, PromotionName, Audience, Clicks, Conversions,
       ClickThroughRate, ClickToConversionRate, AttributedOrders,
       AttributedRevenueAfterRefund, AttributedGrossProfit, DiscountCost,
       CAST(AttributedGrossProfit / NULLIF(DiscountCost, 0) AS decimal(12,2)) AS GrossProfitPerDiscountDollar,
       DENSE_RANK() OVER (ORDER BY AttributedGrossProfit DESC) AS CampaignProfitRank
FROM analytics.vw_CampaignPerformance
ORDER BY CampaignProfitRank;

/* ANALYSIS 14 — Discount effectiveness diagnostic
   Business question: Do promoted orders show enough AOV/order-volume difference to justify discount cost?
   Why it matters: It identifies where a controlled incrementality test should be prioritized.
   SQL skills: conditional aggregation, matched month/channel cuts, descriptive comparison.
   Interpretation: This is not causal because customers self-select into promotions. */
WITH matched AS (
    SELECT DATEFROMPARTS(YEAR(OrderDate), MONTH(OrderDate), 1) AS MonthStart, ChannelName,
           CASE WHEN PromotionId IS NULL THEN 'No Promotion' ELSE 'Promotion' END AS PromotionGroup,
           COUNT(*) AS Orders, AVG(NetRevenue) AS AOV, SUM(NetRevenue) AS Revenue,
           SUM(GrossProfit) AS GrossProfit, SUM(DiscountAmount) AS DiscountCost
    FROM analytics.vw_OrderSummary
    WHERE StatusName <> 'Cancelled'
    GROUP BY DATEFROMPARTS(YEAR(OrderDate), MONTH(OrderDate), 1), ChannelName,
             CASE WHEN PromotionId IS NULL THEN 'No Promotion' ELSE 'Promotion' END
)
SELECT MonthStart, ChannelName,
       SUM(CASE WHEN PromotionGroup = 'Promotion' THEN Orders ELSE 0 END) AS PromotionOrders,
       SUM(CASE WHEN PromotionGroup = 'No Promotion' THEN Orders ELSE 0 END) AS NonPromotionOrders,
       MAX(CASE WHEN PromotionGroup = 'Promotion' THEN AOV END) AS PromotionAOV,
       MAX(CASE WHEN PromotionGroup = 'No Promotion' THEN AOV END) AS NonPromotionAOV,
       SUM(CASE WHEN PromotionGroup = 'Promotion' THEN GrossProfit ELSE 0 END) AS PromotionGrossProfit,
       SUM(CASE WHEN PromotionGroup = 'Promotion' THEN DiscountCost ELSE 0 END) AS PromotionDiscountCost
FROM matched
GROUP BY MonthStart, ChannelName
ORDER BY MonthStart, ChannelName;

/* ANALYSIS 15 — Regional sales contribution
   Business question: Which regions and states drive revenue, margin, and repeat business?
   Why it matters: Regional scale without margin or retention may not be attractive growth.
   SQL skills: CTE, window share, RANK, conditional aggregation. */
WITH regional AS (
    SELECT Region, StateProvince, COUNT(*) AS Orders, COUNT(DISTINCT CustomerId) AS Customers,
           SUM(NetRevenue) AS NetRevenue, SUM(GrossProfit) AS GrossProfit,
           SUM(IsRepeatPurchase) AS RepeatOrders
    FROM analytics.vw_OrderSummary
    WHERE StatusName <> 'Cancelled'
    GROUP BY Region, StateProvince
)
SELECT *, CAST(NetRevenue / NULLIF(SUM(NetRevenue) OVER (), 0) AS decimal(9,4)) AS RevenueShare,
       CAST(GrossProfit / NULLIF(NetRevenue, 0) AS decimal(9,4)) AS GrossMarginRate,
       CAST(RepeatOrders * 1.0 / NULLIF(Orders, 0) AS decimal(9,4)) AS RepeatOrderRate,
       RANK() OVER (ORDER BY NetRevenue DESC) AS RevenueRank
FROM regional
ORDER BY RevenueRank;

/* ANALYSIS 16 — Customer Pareto / 80-20
   Business question: What share of customers produces 80% of after-refund revenue?
   Why it matters: Concentration affects retention priority and commercial risk.
   SQL skills: running total, ROW_NUMBER, window share, threshold extraction. */
WITH value_base AS (
    SELECT CustomerId, LifetimeRevenueAfterRefund,
           SUM(LifetimeRevenueAfterRefund) OVER () AS TotalRevenue,
           COUNT(*) OVER () AS CustomerCount
    FROM analytics.vw_CustomerMetrics
    WHERE LifetimeRevenueAfterRefund > 0
), cumulative AS (
    SELECT *, ROW_NUMBER() OVER (ORDER BY LifetimeRevenueAfterRefund DESC, CustomerId) AS CustomerRank,
           SUM(LifetimeRevenueAfterRefund) OVER
               (ORDER BY LifetimeRevenueAfterRefund DESC, CustomerId ROWS UNBOUNDED PRECEDING) AS CumulativeRevenue
    FROM value_base
), scored AS (
    SELECT *, CumulativeRevenue / NULLIF(TotalRevenue, 0) AS CumulativeRevenueShare,
           CustomerRank * 1.0 / CustomerCount AS CumulativeCustomerShare
    FROM cumulative
)
SELECT TOP (1) CustomerRank AS CustomersRequired,
       CAST(CumulativeCustomerShare AS decimal(9,4)) AS CustomerShareRequired,
       CAST(CumulativeRevenueShare AS decimal(9,4)) AS RevenueShareReached
FROM scored
WHERE CumulativeRevenueShare >= 0.80
ORDER BY CustomerRank;
GO
