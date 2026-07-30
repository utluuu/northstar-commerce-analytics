/* Northstar Commerce | 04_stored_procedures.sql
   Parameterized analytics APIs with validation, SARGable date ranges, and error handling. */
USE NorthstarCommerce;
GO

IF OBJECT_ID(N'analytics.CustomerRfmSnapshot', N'U') IS NULL
BEGIN
    CREATE TABLE analytics.CustomerRfmSnapshot (
        SnapshotDate date NOT NULL,
        CustomerId int NOT NULL,
        RecencyDays int NOT NULL,
        Frequency int NOT NULL,
        MonetaryValue decimal(18,2) NOT NULL,
        RScore tinyint NOT NULL,
        FScore tinyint NOT NULL,
        MScore tinyint NOT NULL,
        RfmCode char(3) NOT NULL,
        Segment varchar(30) NOT NULL,
        CONSTRAINT PK_CustomerRfmSnapshot PRIMARY KEY (SnapshotDate, CustomerId),
        CONSTRAINT FK_Rfm_Customers FOREIGN KEY (CustomerId) REFERENCES ecommerce.Customers(CustomerId)
    );
    CREATE INDEX IX_CustomerRfmSnapshot_Segment
        ON analytics.CustomerRfmSnapshot(SnapshotDate, Segment)
        INCLUDE (MonetaryValue, RecencyDays, Frequency);
END;
GO

/* Monthly commercial performance with MoM, YoY, rolling, and running metrics. */
CREATE OR ALTER PROCEDURE analytics.usp_SalesPerformance
    @StartDate date,
    @EndDate date,
    @ChannelName varchar(30) = NULL,
    @Region varchar(20) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    BEGIN TRY
        IF @StartDate IS NULL OR @EndDate IS NULL OR @StartDate > @EndDate OR @EndDate = '9999-12-31'
            THROW 50001, 'Provide a valid inclusive date range.', 1;
        IF @ChannelName IS NOT NULL
           AND NOT EXISTS (SELECT 1 FROM ecommerce.SalesChannels WHERE ChannelName = @ChannelName)
            THROW 50002, 'ChannelName is not valid.', 1;
        IF @Region IS NOT NULL
           AND NOT EXISTS (SELECT 1 FROM ecommerce.Addresses WHERE Region = @Region)
            THROW 50003, 'Region is not valid.', 1;

        DECLARE @EndExclusive date = DATEADD(day, 1, @EndDate);

        ;WITH monthly AS (
            SELECT DATEFROMPARTS(YEAR(OrderDate), MONTH(OrderDate), 1) AS MonthStart,
                   COUNT(*) AS Orders, COUNT(DISTINCT CustomerId) AS ActiveCustomers,
                   SUM(IsRepeatPurchase) AS RepeatOrders,
                   SUM(NetRevenue) AS NetRevenue, SUM(RevenueAfterRefund) AS RevenueAfterRefund,
                   SUM(GrossProfit) AS GrossProfit, AVG(NetRevenue) AS AverageOrderValue
            FROM analytics.vw_OrderSummary
            WHERE OrderDateTime >= @StartDate AND OrderDateTime < @EndExclusive
              AND StatusName <> 'Cancelled'
              AND (@ChannelName IS NULL OR ChannelName = @ChannelName)
              AND (@Region IS NULL OR Region = @Region)
            GROUP BY DATEFROMPARTS(YEAR(OrderDate), MONTH(OrderDate), 1)
        ), compared AS (
            SELECT *,
                   LAG(NetRevenue, 1) OVER (ORDER BY MonthStart) AS PreviousMonthRevenue,
                   LAG(NetRevenue, 12) OVER (ORDER BY MonthStart) AS PreviousYearRevenue,
                   AVG(NetRevenue) OVER (ORDER BY MonthStart ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS Rolling3MonthRevenue,
                   SUM(NetRevenue) OVER (ORDER BY MonthStart ROWS UNBOUNDED PRECEDING) AS RunningRevenue
            FROM monthly
        )
        SELECT MonthStart, Orders, ActiveCustomers, RepeatOrders,
               CAST(NetRevenue AS decimal(18,2)) AS NetRevenue,
               CAST(RevenueAfterRefund AS decimal(18,2)) AS RevenueAfterRefund,
               CAST(GrossProfit AS decimal(18,2)) AS GrossProfit,
               CAST(AverageOrderValue AS decimal(14,2)) AS AverageOrderValue,
               CAST((NetRevenue / NULLIF(PreviousMonthRevenue, 0) - 1) * 100 AS decimal(9,2)) AS RevenueMoMPct,
               CAST((NetRevenue / NULLIF(PreviousYearRevenue, 0) - 1) * 100 AS decimal(9,2)) AS RevenueYoYPct,
               CAST(Rolling3MonthRevenue AS decimal(18,2)) AS Rolling3MonthRevenue,
               CAST(RunningRevenue AS decimal(19,2)) AS RunningRevenue
        FROM compared
        ORDER BY MonthStart
        OPTION (RECOMPILE);
    END TRY
    BEGIN CATCH
        THROW;
    END CATCH;
END;
GO

/* Customer profile, order history, and preferred products. */
CREATE OR ALTER PROCEDURE analytics.usp_Customer360 @CustomerId int
AS
BEGIN
    SET NOCOUNT ON;

    BEGIN TRY
        IF NOT EXISTS (SELECT 1 FROM ecommerce.Customers WHERE CustomerId = @CustomerId)
            THROW 50004, 'CustomerId does not exist.', 1;

        SELECT CustomerId, CustomerName, AcquisitionDate, AcquisitionSource, SegmentName,
               FirstOrderDate, LastOrderDate, LifetimeOrders, LifetimeRevenue,
               LifetimeRevenueAfterRefund, LifetimeGrossProfit, AverageOrderValue,
               AvgDaysBetweenOrders, RecencyDays, Projected12MonthRevenue, LifecycleStatus
        FROM analytics.vw_CustomerMetrics
        WHERE CustomerId = @CustomerId;

        SELECT OrderId, OrderDateTime, CustomerOrderNumber, IsRepeatPurchase, ChannelName,
               StatusName, NetRevenue, RevenueAfterRefund, GrossProfit, RefundAmount,
               DeliveryDays, IsOnTime
        FROM analytics.vw_OrderSummary
        WHERE CustomerId = @CustomerId
        ORDER BY OrderDateTime DESC, OrderId DESC;

        SELECT TOP (5) ProductId, ProductName, CategoryName,
               SUM(Quantity) AS Units, SUM(NetRevenue) AS NetRevenue,
               ROW_NUMBER() OVER (ORDER BY SUM(NetRevenue) DESC, ProductId) AS PreferenceRank
        FROM analytics.vw_OrderLineAnalytics
        WHERE CustomerId = @CustomerId AND StatusName <> 'Cancelled'
        GROUP BY ProductId, ProductName, CategoryName
        ORDER BY PreferenceRank;
    END TRY
    BEGIN CATCH
        THROW;
    END CATCH;
END;
GO

/* Persist an auditable RFM snapshot. The transaction makes delete-and-replace atomic. */
CREATE OR ALTER PROCEDURE analytics.usp_RefreshRfmSegments @AsOfDate date = NULL
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    BEGIN TRY
        SET @AsOfDate = COALESCE(@AsOfDate,
            (SELECT DATEADD(day, 1, CAST(MAX(OrderDate) AS date)) FROM ecommerce.Orders));
        IF @AsOfDate IS NULL
            THROW 50005, 'RFM cannot run without order data or an explicit AsOfDate.', 1;
        IF @AsOfDate = '9999-12-31'
            THROW 50012, 'AsOfDate must be earlier than 9999-12-31.', 1;

        BEGIN TRANSACTION;
        DELETE FROM analytics.CustomerRfmSnapshot WHERE SnapshotDate = @AsOfDate;

        ;WITH base AS (
            SELECT CustomerId, DATEDIFF(day, MAX(OrderDate), @AsOfDate) AS RecencyDays,
                   COUNT(*) AS Frequency, SUM(RevenueAfterRefund) AS MonetaryValue
            FROM analytics.vw_OrderSummary
            WHERE StatusName <> 'Cancelled'
              AND OrderDateTime < DATEADD(day, 1, @AsOfDate)
            GROUP BY CustomerId
        ), scored AS (
            SELECT *,
                   6 - NTILE(5) OVER (ORDER BY RecencyDays, CustomerId) AS RScore,
                   NTILE(5) OVER (ORDER BY Frequency, CustomerId) AS FScore,
                   NTILE(5) OVER (ORDER BY MonetaryValue, CustomerId) AS MScore
            FROM base
        )
        INSERT analytics.CustomerRfmSnapshot
            (SnapshotDate, CustomerId, RecencyDays, Frequency, MonetaryValue,
             RScore, FScore, MScore, RfmCode, Segment)
        SELECT @AsOfDate, CustomerId, RecencyDays, Frequency, MonetaryValue,
               RScore, FScore, MScore, CONCAT(RScore, FScore, MScore),
               CASE WHEN RScore >= 4 AND FScore >= 4 AND MScore >= 4 THEN 'Champions'
                    WHEN RScore >= 3 AND FScore >= 4 THEN 'Loyal Customers'
                    WHEN RScore = 5 AND FScore <= 2 THEN 'New Customers'
                    WHEN RScore >= 4 AND FScore BETWEEN 2 AND 3 THEN 'Potential Loyalists'
                    WHEN RScore <= 2 AND FScore >= 3 THEN 'At Risk'
                    WHEN RScore <= 2 AND FScore <= 2 THEN 'Hibernating'
                    ELSE 'Needs Attention' END
        FROM scored;

        COMMIT TRANSACTION;

        SELECT Segment, COUNT(*) AS Customers,
               CAST(AVG(CAST(RecencyDays AS decimal(12,2))) AS decimal(10,2)) AS AvgRecencyDays,
               CAST(AVG(CAST(Frequency AS decimal(12,2))) AS decimal(10,2)) AS AvgFrequency,
               CAST(SUM(MonetaryValue) AS decimal(18,2)) AS SegmentValue
        FROM analytics.CustomerRfmSnapshot
        WHERE SnapshotDate = @AsOfDate
        GROUP BY Segment
        ORDER BY SegmentValue DESC;
    END TRY
    BEGIN CATCH
        IF XACT_STATE() <> 0 ROLLBACK TRANSACTION;
        THROW;
    END CATCH;
END;
GO

/* Market-basket affinity using support, directional confidence, and lift. */
CREATE OR ALTER PROCEDURE analytics.usp_ProductAffinity
    @StartDate date,
    @EndDate date,
    @MinimumPairOrders int = 25,
    @TopN int = 50
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    BEGIN TRY
        IF @StartDate IS NULL OR @EndDate IS NULL OR @StartDate > @EndDate OR @EndDate = '9999-12-31'
            THROW 50006, 'Provide a valid inclusive date range.', 1;
        IF @MinimumPairOrders < 2 OR @TopN NOT BETWEEN 1 AND 500
            THROW 50007, 'MinimumPairOrders must be at least 2 and TopN must be between 1 and 500.', 1;

        DECLARE @EndExclusive date = DATEADD(day, 1, @EndDate);

        CREATE TABLE #OrderProducts (
            OrderId int NOT NULL,
            ProductId int NOT NULL,
            CONSTRAINT PK_OrderProducts PRIMARY KEY CLUSTERED (OrderId, ProductId)
        );

        INSERT #OrderProducts (OrderId, ProductId)
        SELECT o.OrderId, oi.ProductId
        FROM ecommerce.Orders o
        JOIN ecommerce.OrderStatuses os ON os.StatusId = o.StatusId
        JOIN ecommerce.OrderItems oi ON oi.OrderId = o.OrderId
        WHERE o.OrderDate >= @StartDate AND o.OrderDate < @EndExclusive
          AND os.StatusName <> 'Cancelled';

        DECLARE @BasketCount decimal(18,4) = (SELECT COUNT(DISTINCT OrderId) FROM #OrderProducts);
        IF @BasketCount = 0 THROW 50008, 'No qualifying baskets were found.', 1;

        ;WITH product_support AS (
            SELECT ProductId, COUNT(*) AS ProductOrders
            FROM #OrderProducts
            GROUP BY ProductId
        ), pairs AS (
            SELECT a.ProductId AS ProductAId, b.ProductId AS ProductBId, COUNT(*) AS PairOrders
            FROM #OrderProducts a
            JOIN #OrderProducts b ON b.OrderId = a.OrderId AND b.ProductId > a.ProductId
            GROUP BY a.ProductId, b.ProductId
            HAVING COUNT(*) >= @MinimumPairOrders
        ), scored AS (
            SELECT p.*,
                   sa.ProductOrders AS ProductAOrders, sb.ProductOrders AS ProductBOrders,
                   p.PairOrders / @BasketCount AS Support,
                   p.PairOrders * 1.0 / sa.ProductOrders AS ConfidenceAToB,
                   p.PairOrders * 1.0 / sb.ProductOrders AS ConfidenceBToA,
                   (p.PairOrders / @BasketCount) /
                     NULLIF((sa.ProductOrders / @BasketCount) * (sb.ProductOrders / @BasketCount), 0) AS Lift
            FROM pairs p
            JOIN product_support sa ON sa.ProductId = p.ProductAId
            JOIN product_support sb ON sb.ProductId = p.ProductBId
        )
        SELECT TOP (@TopN)
               s.ProductAId, pa.ProductName AS ProductA,
               s.ProductBId, pb.ProductName AS ProductB,
               s.PairOrders, CAST(s.Support AS decimal(9,4)) AS Support,
               CAST(s.ConfidenceAToB AS decimal(9,4)) AS ConfidenceAToB,
               CAST(s.ConfidenceBToA AS decimal(9,4)) AS ConfidenceBToA,
               CAST(s.Lift AS decimal(12,4)) AS Lift,
               DENSE_RANK() OVER (ORDER BY s.Lift DESC) AS LiftRank
        FROM scored s
        JOIN ecommerce.Products pa ON pa.ProductId = s.ProductAId
        JOIN ecommerce.Products pb ON pb.ProductId = s.ProductBId
        ORDER BY Lift DESC, PairOrders DESC, ProductAId, ProductBId;
    END TRY
    BEGIN CATCH
        THROW;
    END CATCH;
END;
GO

/* Cohort retention with bounded output for a selected acquisition period. */
CREATE OR ALTER PROCEDURE analytics.usp_CohortRetention
    @CohortStartDate date,
    @CohortEndDate date,
    @MaxMonths int = 12
AS
BEGIN
    SET NOCOUNT ON;

    BEGIN TRY
        IF @CohortStartDate IS NULL OR @CohortEndDate IS NULL OR @CohortStartDate > @CohortEndDate
            THROW 50009, 'Provide a valid cohort date range.', 1;
        IF @MaxMonths NOT BETWEEN 0 AND 36
            THROW 50010, 'MaxMonths must be between 0 and 36.', 1;

        SELECT CohortMonth, MonthsSinceFirstOrder, ActiveCustomers, CohortSize,
               RetentionRate,
               LAG(RetentionRate) OVER (PARTITION BY CohortMonth ORDER BY MonthsSinceFirstOrder) AS PreviousMonthRetention,
               CAST(RetentionRate - LAG(RetentionRate) OVER
                    (PARTITION BY CohortMonth ORDER BY MonthsSinceFirstOrder) AS decimal(9,4)) AS RetentionPointChange
        FROM analytics.vw_CohortRetention
        WHERE CohortMonth >= DATEFROMPARTS(YEAR(@CohortStartDate), MONTH(@CohortStartDate), 1)
          AND CohortMonth <= DATEFROMPARTS(YEAR(@CohortEndDate), MONTH(@CohortEndDate), 1)
          AND MonthsSinceFirstOrder <= @MaxMonths
        ORDER BY CohortMonth, MonthsSinceFirstOrder;
    END TRY
    BEGIN CATCH
        THROW;
    END CATCH;
END;
GO

/* Ranked product performance with optional category filter. */
CREATE OR ALTER PROCEDURE analytics.usp_ProductPerformance
    @CategoryName nvarchar(80) = NULL,
    @MinimumOrders int = 25,
    @TopN int = 25
AS
BEGIN
    SET NOCOUNT ON;

    BEGIN TRY
        IF @MinimumOrders < 1 OR @TopN NOT BETWEEN 1 AND 500
            THROW 50011, 'MinimumOrders must be positive and TopN must be between 1 and 500.', 1;

        ;WITH filtered AS (
            SELECT * FROM analytics.vw_ProductPerformance
            WHERE Orders >= @MinimumOrders
              AND (@CategoryName IS NULL OR CategoryName = @CategoryName)
        ), ranked AS (
            SELECT *,
                   DENSE_RANK() OVER (PARTITION BY CategoryName ORDER BY NetRevenue DESC) AS RevenueRankInCategory,
                   DENSE_RANK() OVER (PARTITION BY CategoryName ORDER BY GrossProfit DESC) AS ProfitRankInCategory,
                   ROW_NUMBER() OVER (ORDER BY NetRevenue DESC, ProductId) AS OverallRevenueRowNumber
            FROM filtered
        )
        SELECT TOP (@TopN) *
        FROM ranked
        ORDER BY NetRevenue DESC, ProductId
        OPTION (RECOMPILE);
    END TRY
    BEGIN CATCH
        THROW;
    END CATCH;
END;
GO
