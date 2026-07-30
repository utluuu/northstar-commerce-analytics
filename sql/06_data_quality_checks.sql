/* Northstar Commerce | 06_data_quality_checks.sql
   Every query should return zero rows unless explicitly marked as a summary. */
USE NorthstarCommerce;
GO

-- Duplicate natural keys
SELECT Email, COUNT(*) AS DuplicateCount FROM ecommerce.Customers GROUP BY Email HAVING COUNT(*) > 1;
SELECT SKU, COUNT(*) AS DuplicateCount FROM ecommerce.Products GROUP BY SKU HAVING COUNT(*) > 1;

-- Orders without lines or mismatched customer/address ownership
SELECT o.OrderId FROM ecommerce.Orders o LEFT JOIN ecommerce.OrderItems oi ON oi.OrderId = o.OrderId
GROUP BY o.OrderId HAVING COUNT(oi.OrderItemId) = 0;
SELECT o.OrderId FROM ecommerce.Orders o JOIN ecommerce.Addresses a ON a.AddressId = o.ShippingAddressId
WHERE o.CustomerId <> a.CustomerId;

-- Payment reconciliation (tolerance: one cent)
WITH expected AS (
    SELECT o.OrderId, SUM(oi.Quantity * oi.UnitPrice - oi.DiscountAmount) + o.ShippingAmount + o.TaxAmount AS ExpectedAmount
    FROM ecommerce.Orders o JOIN ecommerce.OrderItems oi ON oi.OrderId = o.OrderId
    GROUP BY o.OrderId, o.ShippingAmount, o.TaxAmount
), actual AS (
    SELECT OrderId, SUM(Amount) AS PaidAmount
    FROM ecommerce.Payments
    WHERE PaymentStatus IN ('Captured','Refunded','Partially Refunded')
    GROUP BY OrderId
)
SELECT e.OrderId, e.ExpectedAmount, a.PaidAmount
FROM expected e LEFT JOIN actual a ON a.OrderId = e.OrderId
WHERE a.OrderId IS NULL OR ABS(e.ExpectedAmount - a.PaidAmount) > 0.01;

-- Impossible chronology or returned quantity
SELECT ShipmentId FROM ecommerce.Shipments
WHERE (ShippedDate IS NOT NULL AND ShippedDate < (SELECT OrderDate FROM ecommerce.Orders WHERE OrderId = Shipments.OrderId))
   OR (DeliveredDate IS NOT NULL AND DeliveredDate < ShippedDate);
SELECT ri.ReturnItemId FROM ecommerce.ReturnItems ri JOIN ecommerce.OrderItems oi ON oi.OrderItemId = ri.OrderItemId
WHERE ri.ReturnQuantity > oi.Quantity;

-- Promotion code and foreign key must describe the same campaign
SELECT o.OrderId, o.PromoCode, p.PromotionCode
FROM ecommerce.Orders o
LEFT JOIN ecommerce.Promotions p ON p.PromotionId = o.PromotionId
WHERE (o.PromotionId IS NULL AND o.PromoCode IS NOT NULL)
   OR (o.PromotionId IS NOT NULL AND ISNULL(o.PromoCode, '') <> p.PromotionCode);

-- Verified reviews must belong to the customer and product on the referenced order line
SELECT r.ReviewId
FROM ecommerce.ProductReviews r
JOIN ecommerce.OrderItems oi ON oi.OrderItemId = r.OrderItemId
JOIN ecommerce.Orders o ON o.OrderId = oi.OrderId
WHERE r.IsVerifiedPurchase = 1
  AND (r.CustomerId <> o.CustomerId OR r.ProductId <> oi.ProductId OR r.ReviewDate < o.OrderDate);

-- Campaign conversions must reference an order for the same customer and promotion
SELECT ci.InteractionId
FROM ecommerce.CampaignInteractions ci
LEFT JOIN ecommerce.Orders o ON o.OrderId = ci.OrderId
WHERE ci.InteractionType = 'Conversion'
  AND (ci.OrderId IS NULL OR o.CustomerId <> ci.CustomerId OR o.PromotionId <> ci.PromotionId);

-- Analytics view reconciliation: order grain must equal line grain
WITH line_metrics AS (
    SELECT OrderId, SUM(NetRevenue) AS NetRevenue,
           SUM(RefundAmount) AS RefundAmount,
           SUM(RevenueAfterRefund) AS RevenueAfterRefund
    FROM analytics.vw_OrderLineAnalytics
    GROUP BY OrderId
)
SELECT o.OrderId
FROM analytics.vw_OrderSummary o
JOIN line_metrics l ON l.OrderId = o.OrderId
WHERE ABS(o.NetRevenue - l.NetRevenue) > 0.01
   OR ABS(o.RefundAmount - l.RefundAmount) > 0.01
   OR ABS(o.RevenueAfterRefund - l.RevenueAfterRefund) > 0.01;

-- Valid customer order sequences must be unique and gap-free
SELECT CustomerId
FROM analytics.vw_OrderSummary
WHERE StatusName <> 'Cancelled'
GROUP BY CustomerId
HAVING COUNT(*) <> COUNT(DISTINCT CustomerOrderNumber)
    OR MIN(CustomerOrderNumber) <> 1
    OR MAX(CustomerOrderNumber) <> COUNT(*);

-- Revenue after refund cannot exceed booked revenue
SELECT OrderId
FROM analytics.vw_OrderSummary
WHERE RevenueAfterRefund > NetRevenue OR RefundAmount < 0;

-- Campaign conversions should reconcile with directly attributed orders
SELECT p.PromotionId
FROM ecommerce.Promotions p
LEFT JOIN (
    SELECT PromotionId, COUNT(*) AS Conversions
    FROM ecommerce.CampaignInteractions
    WHERE InteractionType = 'Conversion'
    GROUP BY PromotionId
) i ON i.PromotionId = p.PromotionId
LEFT JOIN (
    SELECT PromotionId, COUNT(*) AS AttributedOrders
    FROM ecommerce.Orders
    WHERE PromotionId IS NOT NULL
    GROUP BY PromotionId
) o ON o.PromotionId = p.PromotionId
WHERE ISNULL(i.Conversions, 0) <> ISNULL(o.AttributedOrders, 0);

-- Summary completeness profile (informational)
SELECT 'Orders' AS Entity, COUNT(*) AS Rows,
       SUM(CASE WHEN CustomerId IS NULL THEN 1 ELSE 0 END) AS MissingRequiredValues
FROM ecommerce.Orders
UNION ALL
SELECT 'OrderItems', COUNT(*), SUM(CASE WHEN ProductId IS NULL THEN 1 ELSE 0 END)
FROM ecommerce.OrderItems;
GO
