/* Northstar Commerce | 02_prepare_bulk_load.sql
   Clears transactional data before a full deterministic reload.
   The Python loader performs the same operation automatically. */
USE NorthstarCommerce;
GO

SET NOCOUNT ON;
SET XACT_ABORT ON;
GO

IF OBJECT_ID(N'analytics.CustomerRfmSnapshot', N'U') IS NOT NULL
    DELETE FROM analytics.CustomerRfmSnapshot;
DELETE FROM ecommerce.CampaignInteractions;
DELETE FROM ecommerce.ProductReviews;
DELETE FROM ecommerce.ReturnItems;
DELETE FROM ecommerce.Returns;
DELETE FROM ecommerce.Shipments;
DELETE FROM ecommerce.Payments;
DELETE FROM ecommerce.OrderItems;
DELETE FROM ecommerce.Orders;
DELETE FROM ecommerce.Promotions;
DELETE FROM ecommerce.Products;
DELETE FROM ecommerce.Categories;
DELETE FROM ecommerce.Addresses;
DELETE FROM ecommerce.Customers;
DELETE FROM ecommerce.CustomerSegments;
DELETE FROM ecommerce.OrderStatuses;
DELETE FROM ecommerce.SalesChannels;
DELETE FROM analytics.DimDate;
GO
