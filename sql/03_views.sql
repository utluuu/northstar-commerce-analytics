/* Northstar Commerce | 03_views.sql
   Reusable analytics layer with explicit grain and metric semantics. */
USE NorthstarCommerce;
GO

/* Grain: one order item. NetRevenue is booked revenue after discount and before refunds. */
CREATE OR ALTER VIEW analytics.vw_OrderLineAnalytics AS
WITH return_totals AS (
    SELECT ri.OrderItemId,
           SUM(CASE WHEN r.ReturnStatus <> 'Rejected' THEN ri.ReturnQuantity ELSE 0 END) AS ReturnedQuantity,
           SUM(CASE WHEN r.ReturnStatus <> 'Rejected' THEN ri.RefundAmount ELSE 0 END) AS RefundAmount
    FROM ecommerce.ReturnItems ri
    JOIN ecommerce.Returns r ON r.ReturnId = ri.ReturnId
    GROUP BY ri.OrderItemId
)
SELECT
    oi.OrderItemId, o.OrderId, o.OrderDate AS OrderDateTime, CAST(o.OrderDate AS date) AS OrderDate,
    CONVERT(int, CONVERT(char(8), CAST(o.OrderDate AS date), 112)) AS OrderDateKey,
    o.CustomerId, CONCAT(c.FirstName, ' ', c.LastName) AS CustomerName,
    c.AcquisitionSource, cs.SegmentName, sc.ChannelName, os.StatusName,
    a.City, a.StateProvince, a.Region, a.CountryCode,
    p.ProductId, p.SKU, p.ProductName, p.BrandName,
    child.CategoryName AS SubcategoryName, parent.CategoryName,
    oi.Quantity, oi.UnitPrice, oi.UnitCost, oi.DiscountAmount,
    CAST(oi.Quantity * oi.UnitPrice AS decimal(14,2)) AS GrossRevenue,
    CAST(CASE WHEN os.StatusName = 'Cancelled' THEN 0
         ELSE oi.Quantity * oi.UnitPrice - oi.DiscountAmount END AS decimal(14,2)) AS NetRevenue,
    CAST(CASE WHEN os.StatusName = 'Cancelled' THEN 0 ELSE oi.Quantity * oi.UnitCost END AS decimal(14,2)) AS COGS,
    CAST(CASE WHEN os.StatusName = 'Cancelled' THEN 0
         ELSE oi.Quantity * (oi.UnitPrice - oi.UnitCost) - oi.DiscountAmount END AS decimal(14,2)) AS GrossProfit,
    ISNULL(rt.ReturnedQuantity, 0) AS ReturnedQuantity,
    CAST(ISNULL(rt.RefundAmount, 0) AS decimal(14,2)) AS RefundAmount,
    CAST(CASE WHEN os.StatusName = 'Cancelled' THEN 0
         ELSE oi.Quantity * oi.UnitPrice - oi.DiscountAmount - ISNULL(rt.RefundAmount, 0) END AS decimal(14,2)) AS RevenueAfterRefund,
    CAST(CASE WHEN os.StatusName = 'Cancelled' THEN 0
         ELSE oi.Quantity * (oi.UnitPrice - oi.UnitCost) - oi.DiscountAmount - ISNULL(rt.RefundAmount, 0) END AS decimal(14,2)) AS GrossProfitAfterRefund,
    CAST(oi.DiscountAmount / NULLIF(oi.Quantity * oi.UnitPrice, 0) AS decimal(9,4)) AS DiscountRate,
    o.PromotionId, o.PromoCode, promo.PromotionName
FROM ecommerce.OrderItems oi
JOIN ecommerce.Orders o ON o.OrderId = oi.OrderId
JOIN ecommerce.Customers c ON c.CustomerId = o.CustomerId
JOIN ecommerce.CustomerSegments cs ON cs.SegmentId = c.SegmentId
JOIN ecommerce.SalesChannels sc ON sc.ChannelId = o.ChannelId
JOIN ecommerce.OrderStatuses os ON os.StatusId = o.StatusId
JOIN ecommerce.Addresses a ON a.AddressId = o.ShippingAddressId
JOIN ecommerce.Products p ON p.ProductId = oi.ProductId
JOIN ecommerce.Categories child ON child.CategoryId = p.CategoryId
LEFT JOIN ecommerce.Categories parent ON parent.CategoryId = child.ParentCategoryId
LEFT JOIN ecommerce.Promotions promo ON promo.PromotionId = o.PromotionId
LEFT JOIN return_totals rt ON rt.OrderItemId = oi.OrderItemId;
GO

/* Grain: one order. CustomerOrderNumber counts non-cancelled orders chronologically. */
CREATE OR ALTER VIEW analytics.vw_OrderSummary AS
WITH line_totals AS (
    SELECT OrderId, SUM(Quantity) AS Units,
           SUM(Quantity * UnitPrice) AS GrossRevenue,
           SUM(DiscountAmount) AS DiscountAmount,
           SUM(Quantity * UnitPrice - DiscountAmount) AS BookedRevenue,
           SUM(Quantity * UnitCost) AS COGS
    FROM ecommerce.OrderItems
    GROUP BY OrderId
), return_totals AS (
    SELECT r.OrderId,
           SUM(CASE WHEN r.ReturnStatus <> 'Rejected' THEN ri.ReturnQuantity ELSE 0 END) AS ReturnedUnits,
           SUM(CASE WHEN r.ReturnStatus <> 'Rejected' THEN ri.RefundAmount ELSE 0 END) AS RefundAmount
    FROM ecommerce.Returns r
    JOIN ecommerce.ReturnItems ri ON ri.ReturnId = r.ReturnId
    GROUP BY r.OrderId
), enriched AS (
    SELECT o.*,
           SUM(CASE WHEN os.StatusName <> 'Cancelled' THEN 1 ELSE 0 END)
             OVER (PARTITION BY o.CustomerId ORDER BY o.OrderDate, o.OrderId ROWS UNBOUNDED PRECEDING) AS CustomerOrderNumber
    FROM ecommerce.Orders o
    JOIN ecommerce.OrderStatuses os ON os.StatusId = o.StatusId
)
SELECT o.OrderId, o.OrderDate AS OrderDateTime, CAST(o.OrderDate AS date) AS OrderDate,
       CONVERT(int, CONVERT(char(8), CAST(o.OrderDate AS date), 112)) AS OrderDateKey,
       o.CustomerId, o.CustomerOrderNumber,
       CASE WHEN os.StatusName <> 'Cancelled' AND o.CustomerOrderNumber > 1 THEN 1 ELSE 0 END AS IsRepeatPurchase,
       cs.SegmentName, sc.ChannelName, os.StatusName,
       a.City, a.StateProvince, a.Region, a.CountryCode,
       lt.Units, CAST(lt.GrossRevenue AS decimal(14,2)) AS GrossRevenue,
       CAST(lt.DiscountAmount AS decimal(14,2)) AS DiscountAmount,
       CAST(CASE WHEN os.StatusName = 'Cancelled' THEN 0 ELSE lt.BookedRevenue END AS decimal(14,2)) AS NetRevenue,
       CAST(CASE WHEN os.StatusName = 'Cancelled' THEN 0 ELSE lt.BookedRevenue - ISNULL(rt.RefundAmount, 0) END AS decimal(14,2)) AS RevenueAfterRefund,
       CAST(CASE WHEN os.StatusName = 'Cancelled' THEN 0 ELSE lt.BookedRevenue - lt.COGS END AS decimal(14,2)) AS GrossProfit,
       CAST(CASE WHEN os.StatusName = 'Cancelled' THEN 0
            ELSE lt.BookedRevenue - lt.COGS - ISNULL(rt.RefundAmount, 0) END AS decimal(14,2)) AS GrossProfitAfterRefund,
       o.ShippingAmount, o.TaxAmount, o.PromotionId, o.PromoCode, promo.PromotionName,
       ISNULL(rt.ReturnedUnits, 0) AS ReturnedUnits,
       CAST(ISNULL(rt.RefundAmount, 0) AS decimal(14,2)) AS RefundAmount,
       sh.Carrier, CAST(sh.ShippedDate AS date) AS ShippedDate, sh.PromisedDeliveryDate,
       CAST(sh.DeliveredDate AS date) AS DeliveredDate,
       DATEDIFF(day, CAST(o.OrderDate AS date), CAST(sh.DeliveredDate AS date)) AS DeliveryDays,
       CASE WHEN sh.DeliveredDate IS NULL THEN NULL
            WHEN CAST(sh.DeliveredDate AS date) <= sh.PromisedDeliveryDate THEN 1 ELSE 0 END AS IsOnTime
FROM enriched o
JOIN line_totals lt ON lt.OrderId = o.OrderId
JOIN ecommerce.SalesChannels sc ON sc.ChannelId = o.ChannelId
JOIN ecommerce.OrderStatuses os ON os.StatusId = o.StatusId
JOIN ecommerce.Customers c ON c.CustomerId = o.CustomerId
JOIN ecommerce.CustomerSegments cs ON cs.SegmentId = c.SegmentId
JOIN ecommerce.Addresses a ON a.AddressId = o.ShippingAddressId
LEFT JOIN ecommerce.Promotions promo ON promo.PromotionId = o.PromotionId
LEFT JOIN return_totals rt ON rt.OrderId = o.OrderId
LEFT JOIN ecommerce.Shipments sh ON sh.OrderId = o.OrderId;
GO

/* Grain: one customer. Projected value is an explainable annualized historical run rate, not predictive ML. */
CREATE OR ALTER VIEW analytics.vw_CustomerMetrics AS
WITH anchor AS (
    SELECT DATEADD(day, 1, CAST(MAX(OrderDate) AS date)) AS AsOfDate FROM ecommerce.Orders
), valid_orders AS (
    SELECT CustomerId, OrderId, OrderDate, NetRevenue, RevenueAfterRefund, GrossProfit,
           LAG(OrderDate) OVER (PARTITION BY CustomerId ORDER BY OrderDateTime, OrderId) AS PreviousOrderDate
    FROM analytics.vw_OrderSummary
    WHERE StatusName <> 'Cancelled'
), metrics AS (
    SELECT CustomerId, MIN(OrderDate) AS FirstOrderDate, MAX(OrderDate) AS LastOrderDate,
           COUNT(*) AS LifetimeOrders, SUM(NetRevenue) AS LifetimeRevenue,
           SUM(RevenueAfterRefund) AS LifetimeRevenueAfterRefund,
           SUM(GrossProfit) AS LifetimeGrossProfit, AVG(NetRevenue) AS AverageOrderValue,
           AVG(CAST(DATEDIFF(day, PreviousOrderDate, OrderDate) AS decimal(12,2))) AS AvgDaysBetweenOrders
    FROM valid_orders
    GROUP BY CustomerId
), returned AS (
    SELECT CustomerId, SUM(ReturnedUnits) AS ReturnedUnits
    FROM analytics.vw_OrderSummary
    WHERE StatusName <> 'Cancelled'
    GROUP BY CustomerId
)
SELECT c.CustomerId, CONCAT(c.FirstName, ' ', c.LastName) AS CustomerName, c.Email,
       c.AcquisitionDate, c.AcquisitionSource, cs.SegmentName, c.IsActive, a.AsOfDate,
       m.FirstOrderDate, m.LastOrderDate, ISNULL(m.LifetimeOrders, 0) AS LifetimeOrders,
       CAST(ISNULL(m.LifetimeRevenue, 0) AS decimal(16,2)) AS LifetimeRevenue,
       CAST(ISNULL(m.LifetimeRevenueAfterRefund, 0) AS decimal(16,2)) AS LifetimeRevenueAfterRefund,
       CAST(ISNULL(m.LifetimeGrossProfit, 0) AS decimal(16,2)) AS LifetimeGrossProfit,
       CAST(ISNULL(m.AverageOrderValue, 0) AS decimal(14,2)) AS AverageOrderValue,
       CAST(m.AvgDaysBetweenOrders AS decimal(10,2)) AS AvgDaysBetweenOrders,
       CASE WHEN m.LastOrderDate IS NULL THEN NULL ELSE DATEDIFF(day, m.LastOrderDate, a.AsOfDate) END AS RecencyDays,
       ISNULL(r.ReturnedUnits, 0) AS ReturnedUnits,
       CASE WHEN m.LifetimeOrders >= 2 THEN 1 ELSE 0 END AS IsRepeatCustomer,
       CAST(CASE WHEN m.LifetimeOrders IS NULL THEN 0
            ELSE m.LifetimeRevenueAfterRefund /
                 NULLIF(CASE WHEN DATEDIFF(day, c.AcquisitionDate, a.AsOfDate) < 90 THEN 90.0 / 365.25
                             ELSE DATEDIFF(day, c.AcquisitionDate, a.AsOfDate) / 365.25 END, 0) END AS decimal(16,2)) AS Projected12MonthRevenue,
       CASE WHEN m.LifetimeOrders IS NULL THEN 'Prospect'
            WHEN m.LifetimeOrders = 1 AND DATEDIFF(day, m.LastOrderDate, a.AsOfDate) > 90 THEN 'One-Time Lapsed'
            WHEN m.LifetimeOrders >= 2
             AND DATEDIFF(day, m.LastOrderDate, a.AsOfDate) >
                 CASE WHEN 2 * ISNULL(m.AvgDaysBetweenOrders, 45) > 90 THEN 2 * ISNULL(m.AvgDaysBetweenOrders, 45) ELSE 90 END THEN 'High Risk'
            WHEN m.LifetimeOrders >= 2
             AND DATEDIFF(day, m.LastOrderDate, a.AsOfDate) >
                 CASE WHEN 1.5 * ISNULL(m.AvgDaysBetweenOrders, 45) > 60 THEN 1.5 * ISNULL(m.AvgDaysBetweenOrders, 45) ELSE 60 END THEN 'At Risk'
            ELSE 'Active' END AS LifecycleStatus
FROM ecommerce.Customers c
JOIN ecommerce.CustomerSegments cs ON cs.SegmentId = c.SegmentId
CROSS JOIN anchor a
LEFT JOIN metrics m ON m.CustomerId = c.CustomerId
LEFT JOIN returned r ON r.CustomerId = c.CustomerId;
GO

/* Grain: one calendar month, including zero-activity months within the observed order range. */
CREATE OR ALTER VIEW analytics.vw_MonthlyKpis AS
WITH bounds AS (
    SELECT DATEFROMPARTS(YEAR(MIN(OrderDate)), MONTH(MIN(OrderDate)), 1) AS MinMonth,
           DATEFROMPARTS(YEAR(MAX(OrderDate)), MONTH(MAX(OrderDate)), 1) AS MaxMonth
    FROM ecommerce.Orders
)
SELECT d.DateKey, d.FullDate AS MonthStart, d.CalendarYear, d.CalendarQuarter,
       d.MonthNumber, d.MonthName, d.YearMonth,
       COUNT(o.OrderId) AS Orders, COUNT(DISTINCT o.CustomerId) AS ActiveCustomers,
       SUM(CASE WHEN o.IsRepeatPurchase = 1 THEN 1 ELSE 0 END) AS RepeatOrders,
       CAST(ISNULL(SUM(o.NetRevenue), 0) AS decimal(18,2)) AS NetRevenue,
       CAST(ISNULL(SUM(o.RevenueAfterRefund), 0) AS decimal(18,2)) AS RevenueAfterRefund,
       CAST(ISNULL(SUM(o.GrossProfit), 0) AS decimal(18,2)) AS GrossProfit,
       CAST(ISNULL(AVG(o.NetRevenue), 0) AS decimal(14,2)) AS AverageOrderValue,
       CAST(ISNULL(SUM(o.DiscountAmount), 0) AS decimal(16,2)) AS Discounts,
       SUM(ISNULL(o.ReturnedUnits, 0)) AS ReturnedUnits
FROM analytics.DimDate d
CROSS JOIN bounds b
LEFT JOIN analytics.vw_OrderSummary o
  ON o.OrderDateTime >= d.FullDate
 AND o.OrderDateTime < DATEADD(month, 1, d.FullDate)
 AND o.StatusName <> 'Cancelled'
WHERE d.DayOfMonth = 1 AND d.FullDate BETWEEN b.MinMonth AND b.MaxMonth
GROUP BY d.DateKey, d.FullDate, d.CalendarYear, d.CalendarQuarter,
         d.MonthNumber, d.MonthName, d.YearMonth;
GO

/* Grain: one calendar month with comparative and cumulative metrics. */
CREATE OR ALTER VIEW analytics.vw_MonthlyPerformance AS
WITH compared AS (
    SELECT m.*,
           LAG(NetRevenue, 1) OVER (ORDER BY MonthStart) AS PreviousMonthRevenue,
           LAG(NetRevenue, 12) OVER (ORDER BY MonthStart) AS PreviousYearRevenue,
           LAG(GrossProfit, 1) OVER (ORDER BY MonthStart) AS PreviousMonthGrossProfit,
           AVG(NetRevenue) OVER (ORDER BY MonthStart ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS Rolling3MonthRevenue,
           AVG(NetRevenue) OVER (ORDER BY MonthStart ROWS BETWEEN 11 PRECEDING AND CURRENT ROW) AS Rolling12MonthRevenue,
           SUM(NetRevenue) OVER (ORDER BY MonthStart ROWS UNBOUNDED PRECEDING) AS RunningRevenue
    FROM analytics.vw_MonthlyKpis m
)
SELECT *,
       CAST((NetRevenue / NULLIF(PreviousMonthRevenue, 0) - 1) * 100 AS decimal(9,2)) AS RevenueMoMPct,
       CAST((NetRevenue / NULLIF(PreviousYearRevenue, 0) - 1) * 100 AS decimal(9,2)) AS RevenueYoYPct,
       CAST((GrossProfit / NULLIF(PreviousMonthGrossProfit, 0) - 1) * 100 AS decimal(9,2)) AS GrossProfitMoMPct,
       CAST(Rolling3MonthRevenue AS decimal(18,2)) AS Rolling3MonthRevenueValue,
       CAST(Rolling12MonthRevenue AS decimal(18,2)) AS Rolling12MonthRevenueValue,
       CAST(RunningRevenue AS decimal(19,2)) AS RunningRevenueValue
FROM compared;
GO

/* Grain: one cohort-month and elapsed month. */
CREATE OR ALTER VIEW analytics.vw_CohortRetention AS
WITH customer_months AS (
    SELECT CustomerId, DATEFROMPARTS(YEAR(OrderDate), MONTH(OrderDate), 1) AS ActivityMonth
    FROM analytics.vw_OrderSummary
    WHERE StatusName <> 'Cancelled'
    GROUP BY CustomerId, DATEFROMPARTS(YEAR(OrderDate), MONTH(OrderDate), 1)
), assigned AS (
    SELECT CustomerId, ActivityMonth,
           MIN(ActivityMonth) OVER (PARTITION BY CustomerId) AS CohortMonth
    FROM customer_months
), retained AS (
    SELECT CohortMonth, DATEDIFF(month, CohortMonth, ActivityMonth) AS MonthsSinceFirstOrder,
           COUNT(*) AS ActiveCustomers
    FROM assigned
    GROUP BY CohortMonth, DATEDIFF(month, CohortMonth, ActivityMonth)
), sized AS (
    SELECT *, MAX(CASE WHEN MonthsSinceFirstOrder = 0 THEN ActiveCustomers END)
                      OVER (PARTITION BY CohortMonth) AS CohortSize
    FROM retained
)
SELECT CohortMonth, MonthsSinceFirstOrder, ActiveCustomers, CohortSize,
       CAST(ActiveCustomers * 1.0 / NULLIF(CohortSize, 0) AS decimal(9,4)) AS RetentionRate
FROM sized;
GO

/* Grain: one product. */
CREATE OR ALTER VIEW analytics.vw_ProductPerformance AS
WITH sales AS (
    SELECT ProductId, MIN(SKU) AS SKU, MIN(ProductName) AS ProductName, MIN(BrandName) AS BrandName,
           MIN(SubcategoryName) AS SubcategoryName, MIN(CategoryName) AS CategoryName,
           COUNT(DISTINCT OrderId) AS Orders, SUM(Quantity) AS UnitsSold,
           SUM(GrossRevenue) AS GrossRevenue, SUM(DiscountAmount) AS DiscountAmount,
           SUM(NetRevenue) AS NetRevenue, SUM(RevenueAfterRefund) AS RevenueAfterRefund,
           SUM(GrossProfit) AS GrossProfit, SUM(ReturnedQuantity) AS ReturnedUnits,
           SUM(RefundAmount) AS RefundAmount
    FROM analytics.vw_OrderLineAnalytics
    WHERE StatusName <> 'Cancelled'
    GROUP BY ProductId
), reviews AS (
    SELECT ProductId, COUNT(*) AS Reviews, AVG(CAST(Rating AS decimal(9,4))) AS AverageRating
    FROM ecommerce.ProductReviews
    GROUP BY ProductId
)
SELECT s.*, ISNULL(r.Reviews, 0) AS Reviews, CAST(r.AverageRating AS decimal(4,2)) AS AverageRating,
       CAST(s.GrossProfit / NULLIF(s.NetRevenue, 0) AS decimal(9,4)) AS GrossMarginRate,
       CAST(s.ReturnedUnits * 1.0 / NULLIF(s.UnitsSold, 0) AS decimal(9,4)) AS UnitReturnRate,
       CAST(s.DiscountAmount / NULLIF(s.GrossRevenue, 0) AS decimal(9,4)) AS DiscountRate
FROM sales s
LEFT JOIN reviews r ON r.ProductId = s.ProductId;
GO

/* Grain: one returned order line. */
CREATE OR ALTER VIEW analytics.vw_ReturnAnalysis AS
SELECT r.ReturnId, r.OrderId, r.ReturnDate, r.ReturnReason, r.ReturnStatus,
       oi.OrderItemId, p.ProductId, p.ProductName, p.BrandName,
       child.CategoryName AS SubcategoryName, parent.CategoryName,
       ri.ReturnQuantity, ri.RefundAmount, oi.Quantity AS PurchasedQuantity,
       CAST(ri.ReturnQuantity * 1.0 / NULLIF(oi.Quantity, 0) AS decimal(9,4)) AS LineReturnRate
FROM ecommerce.Returns r
JOIN ecommerce.ReturnItems ri ON ri.ReturnId = r.ReturnId
JOIN ecommerce.OrderItems oi ON oi.OrderItemId = ri.OrderItemId
JOIN ecommerce.Products p ON p.ProductId = oi.ProductId
JOIN ecommerce.Categories child ON child.CategoryId = p.CategoryId
LEFT JOIN ecommerce.Categories parent ON parent.CategoryId = child.ParentCategoryId;
GO

/* Grain: one verified product review. */
CREATE OR ALTER VIEW analytics.vw_ProductReviewAnalytics AS
SELECT r.ReviewId, r.ReviewDate, r.CustomerId, cs.SegmentName,
       r.ProductId, p.SKU, p.ProductName, p.BrandName,
       child.CategoryName AS SubcategoryName, parent.CategoryName,
       r.Rating, r.ReviewTitle, r.IsVerifiedPurchase, r.HelpfulVotes,
       CASE WHEN ri.ReturnItemId IS NULL THEN 0 ELSE 1 END AS WasReturned
FROM ecommerce.ProductReviews r
JOIN ecommerce.Customers c ON c.CustomerId = r.CustomerId
JOIN ecommerce.CustomerSegments cs ON cs.SegmentId = c.SegmentId
JOIN ecommerce.Products p ON p.ProductId = r.ProductId
JOIN ecommerce.Categories child ON child.CategoryId = p.CategoryId
LEFT JOIN ecommerce.Categories parent ON parent.CategoryId = child.ParentCategoryId
LEFT JOIN ecommerce.ReturnItems ri ON ri.OrderItemId = r.OrderItemId;
GO

/* Grain: one promotion. Attribution is direct promo-code attribution, not causal incrementality. */
CREATE OR ALTER VIEW analytics.vw_CampaignPerformance AS
WITH interactions AS (
    SELECT PromotionId,
           COUNT(DISTINCT CASE WHEN InteractionType IN ('Sent','Impression') THEN CustomerId END) AS Audience,
           SUM(CASE WHEN InteractionType = 'Click' THEN 1 ELSE 0 END) AS Clicks,
           SUM(CASE WHEN InteractionType = 'Conversion' THEN 1 ELSE 0 END) AS Conversions
    FROM ecommerce.CampaignInteractions
    GROUP BY PromotionId
), attributed AS (
    SELECT PromotionId, COUNT(*) AS AttributedOrders, SUM(NetRevenue) AS AttributedRevenue,
           SUM(RevenueAfterRefund) AS AttributedRevenueAfterRefund,
           SUM(GrossProfit) AS AttributedGrossProfit, SUM(DiscountAmount) AS DiscountCost
    FROM analytics.vw_OrderSummary
    WHERE PromotionId IS NOT NULL AND StatusName <> 'Cancelled'
    GROUP BY PromotionId
)
SELECT p.PromotionId, p.PromotionCode, p.PromotionName, p.PromotionType,
       p.StartDate, p.EndDate, ISNULL(i.Audience, 0) AS Audience,
       ISNULL(i.Clicks, 0) AS Clicks, ISNULL(i.Conversions, 0) AS Conversions,
       CAST(i.Clicks * 1.0 / NULLIF(i.Audience, 0) AS decimal(9,4)) AS ClickThroughRate,
       CAST(i.Conversions * 1.0 / NULLIF(i.Clicks, 0) AS decimal(9,4)) AS ClickToConversionRate,
       ISNULL(a.AttributedOrders, 0) AS AttributedOrders,
       CAST(ISNULL(a.AttributedRevenue, 0) AS decimal(18,2)) AS AttributedRevenue,
       CAST(ISNULL(a.AttributedRevenueAfterRefund, 0) AS decimal(18,2)) AS AttributedRevenueAfterRefund,
       CAST(ISNULL(a.AttributedGrossProfit, 0) AS decimal(18,2)) AS AttributedGrossProfit,
       CAST(ISNULL(a.DiscountCost, 0) AS decimal(18,2)) AS DiscountCost
FROM ecommerce.Promotions p
LEFT JOIN interactions i ON i.PromotionId = p.PromotionId
LEFT JOIN attributed a ON a.PromotionId = p.PromotionId;
GO
