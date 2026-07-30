/* Northstar Commerce | 01_schema.sql */
USE NorthstarCommerce;
GO

SET NOCOUNT ON;
SET XACT_ABORT ON;
GO

CREATE TABLE ecommerce.CustomerSegments (
    SegmentId          tinyint NOT NULL CONSTRAINT PK_CustomerSegments PRIMARY KEY,
    SegmentName        varchar(30) NOT NULL CONSTRAINT UQ_CustomerSegments_Name UNIQUE,
    Description        nvarchar(200) NOT NULL
);

CREATE TABLE ecommerce.Customers (
    CustomerId       int IDENTITY(1,1) NOT NULL CONSTRAINT PK_Customers PRIMARY KEY,
    FirstName        nvarchar(50) NOT NULL,
    LastName         nvarchar(50) NOT NULL,
    Email            nvarchar(255) NOT NULL,
    Phone            nvarchar(30) NULL,
    AcquisitionDate  date NOT NULL,
    AcquisitionSource varchar(30) NOT NULL,
    SegmentId         tinyint NOT NULL,
    IsActive         bit NOT NULL CONSTRAINT DF_Customers_IsActive DEFAULT (1),
    CreatedAt        datetime2(0) NOT NULL CONSTRAINT DF_Customers_CreatedAt DEFAULT SYSUTCDATETIME(),
    CONSTRAINT UQ_Customers_Email UNIQUE (Email),
    CONSTRAINT FK_Customers_Segments FOREIGN KEY (SegmentId) REFERENCES ecommerce.CustomerSegments(SegmentId),
    CONSTRAINT CK_Customers_Source CHECK (AcquisitionSource IN ('Organic','Paid Search','Social','Referral','Email','Marketplace'))
);

CREATE TABLE ecommerce.Addresses (
    AddressId       int IDENTITY(1,1) NOT NULL CONSTRAINT PK_Addresses PRIMARY KEY,
    CustomerId      int NOT NULL,
    AddressType     varchar(10) NOT NULL,
    AddressLine1    nvarchar(100) NOT NULL,
    City            nvarchar(60) NOT NULL,
    StateProvince   nvarchar(60) NOT NULL,
    Region          varchar(20) NOT NULL,
    PostalCode      nvarchar(15) NOT NULL,
    CountryCode     char(2) NOT NULL,
    IsDefault       bit NOT NULL CONSTRAINT DF_Addresses_IsDefault DEFAULT (0),
    CONSTRAINT FK_Addresses_Customers FOREIGN KEY (CustomerId) REFERENCES ecommerce.Customers(CustomerId),
    CONSTRAINT CK_Addresses_Type CHECK (AddressType IN ('Billing','Shipping'))
);

CREATE TABLE ecommerce.Categories (
    CategoryId       smallint IDENTITY(1,1) NOT NULL CONSTRAINT PK_Categories PRIMARY KEY,
    CategoryName     nvarchar(80) NOT NULL CONSTRAINT UQ_Categories_Name UNIQUE,
    ParentCategoryId smallint NULL,
    CONSTRAINT FK_Categories_Parent FOREIGN KEY (ParentCategoryId) REFERENCES ecommerce.Categories(CategoryId)
);

CREATE TABLE ecommerce.Products (
    ProductId      int IDENTITY(1,1) NOT NULL CONSTRAINT PK_Products PRIMARY KEY,
    SKU            varchar(30) NOT NULL CONSTRAINT UQ_Products_SKU UNIQUE,
    ProductName    nvarchar(120) NOT NULL,
    BrandName      nvarchar(80) NOT NULL,
    CategoryId     smallint NOT NULL,
    UnitCost       decimal(12,2) NOT NULL,
    ListPrice      decimal(12,2) NOT NULL,
    LaunchDate     date NOT NULL,
    IsActive       bit NOT NULL CONSTRAINT DF_Products_IsActive DEFAULT (1),
    CONSTRAINT FK_Products_Categories FOREIGN KEY (CategoryId) REFERENCES ecommerce.Categories(CategoryId),
    CONSTRAINT CK_Products_Cost CHECK (UnitCost >= 0),
    CONSTRAINT CK_Products_Price CHECK (ListPrice > 0 AND ListPrice >= UnitCost)
);

CREATE TABLE ecommerce.SalesChannels (
    ChannelId    tinyint IDENTITY(1,1) NOT NULL CONSTRAINT PK_SalesChannels PRIMARY KEY,
    ChannelName  varchar(30) NOT NULL CONSTRAINT UQ_SalesChannels_Name UNIQUE
);

CREATE TABLE ecommerce.OrderStatuses (
    StatusId    tinyint IDENTITY(1,1) NOT NULL CONSTRAINT PK_OrderStatuses PRIMARY KEY,
    StatusName  varchar(20) NOT NULL CONSTRAINT UQ_OrderStatuses_Name UNIQUE
);

CREATE TABLE ecommerce.Promotions (
    PromotionId      int NOT NULL CONSTRAINT PK_Promotions PRIMARY KEY,
    PromotionCode    varchar(20) NOT NULL CONSTRAINT UQ_Promotions_Code UNIQUE,
    PromotionName    nvarchar(100) NOT NULL,
    PromotionType    varchar(20) NOT NULL,
    DiscountValue    decimal(12,2) NOT NULL,
    MinimumOrderValue decimal(12,2) NOT NULL,
    StartDate        datetime2(0) NOT NULL,
    EndDate          datetime2(0) NOT NULL,
    ChannelId        tinyint NULL,
    CONSTRAINT FK_Promotions_Channels FOREIGN KEY (ChannelId) REFERENCES ecommerce.SalesChannels(ChannelId),
    CONSTRAINT CK_Promotions_Type CHECK (PromotionType IN ('Percentage','Fixed Amount','Free Shipping')),
    CONSTRAINT CK_Promotions_Value CHECK (DiscountValue >= 0 AND MinimumOrderValue >= 0),
    CONSTRAINT CK_Promotions_Dates CHECK (EndDate > StartDate)
);

CREATE TABLE ecommerce.Orders (
    OrderId           int IDENTITY(10001,1) NOT NULL CONSTRAINT PK_Orders PRIMARY KEY,
    CustomerId        int NOT NULL,
    ShippingAddressId int NOT NULL,
    ChannelId         tinyint NOT NULL,
    StatusId          tinyint NOT NULL,
    PromotionId       int NULL,
    OrderDate         datetime2(0) NOT NULL,
    PromoCode         varchar(20) NULL,
    ShippingAmount    decimal(12,2) NOT NULL CONSTRAINT DF_Orders_Shipping DEFAULT (0),
    TaxAmount         decimal(12,2) NOT NULL CONSTRAINT DF_Orders_Tax DEFAULT (0),
    CONSTRAINT FK_Orders_Customers FOREIGN KEY (CustomerId) REFERENCES ecommerce.Customers(CustomerId),
    CONSTRAINT FK_Orders_Addresses FOREIGN KEY (ShippingAddressId) REFERENCES ecommerce.Addresses(AddressId),
    CONSTRAINT FK_Orders_Channels FOREIGN KEY (ChannelId) REFERENCES ecommerce.SalesChannels(ChannelId),
    CONSTRAINT FK_Orders_Statuses FOREIGN KEY (StatusId) REFERENCES ecommerce.OrderStatuses(StatusId),
    CONSTRAINT FK_Orders_Promotions FOREIGN KEY (PromotionId) REFERENCES ecommerce.Promotions(PromotionId),
    CONSTRAINT CK_Orders_Shipping CHECK (ShippingAmount >= 0),
    CONSTRAINT CK_Orders_Tax CHECK (TaxAmount >= 0)
);

CREATE TABLE ecommerce.OrderItems (
    OrderItemId    bigint IDENTITY(1,1) NOT NULL CONSTRAINT PK_OrderItems PRIMARY KEY,
    OrderId        int NOT NULL,
    ProductId      int NOT NULL,
    Quantity       smallint NOT NULL,
    UnitPrice      decimal(12,2) NOT NULL,
    UnitCost       decimal(12,2) NOT NULL,
    DiscountAmount decimal(12,2) NOT NULL CONSTRAINT DF_OrderItems_Discount DEFAULT (0),
    CONSTRAINT FK_OrderItems_Orders FOREIGN KEY (OrderId) REFERENCES ecommerce.Orders(OrderId),
    CONSTRAINT FK_OrderItems_Products FOREIGN KEY (ProductId) REFERENCES ecommerce.Products(ProductId),
    CONSTRAINT UQ_OrderItems_OrderProduct UNIQUE (OrderId, ProductId),
    CONSTRAINT CK_OrderItems_Quantity CHECK (Quantity > 0),
    CONSTRAINT CK_OrderItems_Price CHECK (UnitPrice > 0 AND UnitCost >= 0),
    CONSTRAINT CK_OrderItems_Discount CHECK (DiscountAmount >= 0 AND DiscountAmount <= Quantity * UnitPrice)
);

CREATE TABLE ecommerce.Payments (
    PaymentId      bigint IDENTITY(1,1) NOT NULL CONSTRAINT PK_Payments PRIMARY KEY,
    OrderId        int NOT NULL,
    PaymentDate    datetime2(0) NOT NULL,
    PaymentMethod  varchar(20) NOT NULL,
    PaymentStatus  varchar(20) NOT NULL,
    Amount          decimal(12,2) NOT NULL,
    TransactionRef  varchar(40) NOT NULL CONSTRAINT UQ_Payments_TransactionRef UNIQUE,
    CONSTRAINT FK_Payments_Orders FOREIGN KEY (OrderId) REFERENCES ecommerce.Orders(OrderId),
    CONSTRAINT CK_Payments_Method CHECK (PaymentMethod IN ('Credit Card','Debit Card','PayPal','Bank Transfer','Gift Card')),
    CONSTRAINT CK_Payments_Status CHECK (PaymentStatus IN ('Authorized','Captured','Failed','Refunded','Partially Refunded')),
    CONSTRAINT CK_Payments_Amount CHECK (Amount >= 0)
);

CREATE TABLE ecommerce.Shipments (
    ShipmentId          bigint IDENTITY(1,1) NOT NULL CONSTRAINT PK_Shipments PRIMARY KEY,
    OrderId             int NOT NULL CONSTRAINT UQ_Shipments_Order UNIQUE,
    Carrier             varchar(30) NOT NULL,
    TrackingNumber      varchar(40) NOT NULL CONSTRAINT UQ_Shipments_Tracking UNIQUE,
    ShippedDate         datetime2(0) NULL,
    PromisedDeliveryDate date NULL,
    DeliveredDate       datetime2(0) NULL,
    ShippingStatus      varchar(20) NOT NULL,
    CONSTRAINT FK_Shipments_Orders FOREIGN KEY (OrderId) REFERENCES ecommerce.Orders(OrderId),
    CONSTRAINT CK_Shipments_Status CHECK (ShippingStatus IN ('Pending','Shipped','In Transit','Delivered','Exception')),
    CONSTRAINT CK_Shipments_Chronology CHECK (DeliveredDate IS NULL OR ShippedDate IS NULL OR DeliveredDate >= ShippedDate)
);

CREATE TABLE ecommerce.Returns (
    ReturnId       bigint IDENTITY(1,1) NOT NULL CONSTRAINT PK_Returns PRIMARY KEY,
    OrderId        int NOT NULL,
    ReturnDate     date NOT NULL,
    ReturnReason   varchar(40) NOT NULL,
    ReturnStatus   varchar(20) NOT NULL,
    CONSTRAINT FK_Returns_Orders FOREIGN KEY (OrderId) REFERENCES ecommerce.Orders(OrderId),
    CONSTRAINT CK_Returns_Reason CHECK (ReturnReason IN ('Damaged','Wrong Item','Not as Described','Changed Mind','Too Late','Defective')),
    CONSTRAINT CK_Returns_Status CHECK (ReturnStatus IN ('Requested','Approved','Received','Refunded','Rejected'))
);

CREATE TABLE ecommerce.ReturnItems (
    ReturnItemId  bigint IDENTITY(1,1) NOT NULL CONSTRAINT PK_ReturnItems PRIMARY KEY,
    ReturnId      bigint NOT NULL,
    OrderItemId   bigint NOT NULL,
    ReturnQuantity smallint NOT NULL,
    RefundAmount  decimal(12,2) NOT NULL,
    CONSTRAINT FK_ReturnItems_Returns FOREIGN KEY (ReturnId) REFERENCES ecommerce.Returns(ReturnId),
    CONSTRAINT FK_ReturnItems_OrderItems FOREIGN KEY (OrderItemId) REFERENCES ecommerce.OrderItems(OrderItemId),
    CONSTRAINT UQ_ReturnItems_ReturnOrderItem UNIQUE (ReturnId, OrderItemId),
    CONSTRAINT CK_ReturnItems_Quantity CHECK (ReturnQuantity > 0),
    CONSTRAINT CK_ReturnItems_Refund CHECK (RefundAmount >= 0)
);

CREATE TABLE ecommerce.ProductReviews (
    ReviewId         bigint NOT NULL CONSTRAINT PK_ProductReviews PRIMARY KEY,
    CustomerId       int NOT NULL,
    ProductId        int NOT NULL,
    OrderItemId      bigint NOT NULL,
    ReviewDate       datetime2(0) NOT NULL,
    Rating           tinyint NOT NULL,
    ReviewTitle      nvarchar(120) NULL,
    ReviewText       nvarchar(1000) NULL,
    IsVerifiedPurchase bit NOT NULL CONSTRAINT DF_ProductReviews_Verified DEFAULT (1),
    HelpfulVotes     int NOT NULL CONSTRAINT DF_ProductReviews_Helpful DEFAULT (0),
    CONSTRAINT FK_ProductReviews_Customers FOREIGN KEY (CustomerId) REFERENCES ecommerce.Customers(CustomerId),
    CONSTRAINT FK_ProductReviews_Products FOREIGN KEY (ProductId) REFERENCES ecommerce.Products(ProductId),
    CONSTRAINT FK_ProductReviews_OrderItems FOREIGN KEY (OrderItemId) REFERENCES ecommerce.OrderItems(OrderItemId),
    CONSTRAINT UQ_ProductReviews_OrderItem UNIQUE (OrderItemId),
    CONSTRAINT CK_ProductReviews_Rating CHECK (Rating BETWEEN 1 AND 5),
    CONSTRAINT CK_ProductReviews_Helpful CHECK (HelpfulVotes >= 0)
);

CREATE TABLE ecommerce.CampaignInteractions (
    InteractionId    bigint NOT NULL CONSTRAINT PK_CampaignInteractions PRIMARY KEY,
    PromotionId      int NOT NULL,
    CustomerId       int NOT NULL,
    InteractionDate  datetime2(0) NOT NULL,
    InteractionType  varchar(20) NOT NULL,
    ChannelName      varchar(20) NOT NULL,
    OrderId          int NULL,
    CONSTRAINT FK_CampaignInteractions_Promotions FOREIGN KEY (PromotionId) REFERENCES ecommerce.Promotions(PromotionId),
    CONSTRAINT FK_CampaignInteractions_Customers FOREIGN KEY (CustomerId) REFERENCES ecommerce.Customers(CustomerId),
    CONSTRAINT FK_CampaignInteractions_Orders FOREIGN KEY (OrderId) REFERENCES ecommerce.Orders(OrderId),
    CONSTRAINT CK_CampaignInteractions_Type CHECK (InteractionType IN ('Sent','Impression','Click','Conversion','Unsubscribe')),
    CONSTRAINT CK_CampaignInteractions_Channel CHECK (ChannelName IN ('Email','Paid Social','Display','Push','SMS'))
);

CREATE TABLE analytics.DimDate (
    DateKey         int NOT NULL CONSTRAINT PK_DimDate PRIMARY KEY,
    FullDate        date NOT NULL CONSTRAINT UQ_DimDate_FullDate UNIQUE,
    CalendarYear    smallint NOT NULL,
    CalendarQuarter tinyint NOT NULL,
    MonthNumber     tinyint NOT NULL,
    MonthName       varchar(9) NOT NULL,
    YearMonth       char(7) NOT NULL,
    WeekOfYear      tinyint NOT NULL,
    DayOfMonth      tinyint NOT NULL,
    DayName         varchar(9) NOT NULL,
    IsWeekend       bit NOT NULL
);

CREATE INDEX IX_Orders_OrderDate ON ecommerce.Orders(OrderDate) INCLUDE (CustomerId, ChannelId, StatusId);
CREATE INDEX IX_Orders_CustomerId ON ecommerce.Orders(CustomerId, OrderDate);
CREATE INDEX IX_Orders_PromotionId ON ecommerce.Orders(PromotionId, OrderDate) WHERE PromotionId IS NOT NULL;
CREATE INDEX IX_Orders_ChannelDate ON ecommerce.Orders(ChannelId, OrderDate)
    INCLUDE (CustomerId, StatusId, PromotionId, ShippingAddressId);
CREATE INDEX IX_Orders_ShippingAddressDate ON ecommerce.Orders(ShippingAddressId, OrderDate)
    INCLUDE (CustomerId, ChannelId, StatusId);
CREATE INDEX IX_OrderItems_ProductId ON ecommerce.OrderItems(ProductId) INCLUDE (Quantity, UnitPrice, UnitCost, DiscountAmount);
CREATE INDEX IX_Customers_SegmentId ON ecommerce.Customers(SegmentId) INCLUDE (AcquisitionDate, AcquisitionSource);
CREATE INDEX IX_Addresses_Region ON ecommerce.Addresses(Region, StateProvince, City);
CREATE INDEX IX_Payments_OrderId ON ecommerce.Payments(OrderId, PaymentStatus) INCLUDE (Amount, PaymentDate);
CREATE INDEX IX_Shipments_Carrier ON ecommerce.Shipments(Carrier, ShippingStatus) INCLUDE (PromisedDeliveryDate, DeliveredDate);
CREATE INDEX IX_Returns_OrderId ON ecommerce.Returns(OrderId, ReturnDate);
CREATE INDEX IX_ReturnItems_OrderItemId ON ecommerce.ReturnItems(OrderItemId) INCLUDE (ReturnQuantity, RefundAmount);
CREATE INDEX IX_Products_CategoryId ON ecommerce.Products(CategoryId);
CREATE INDEX IX_ProductReviews_ProductId ON ecommerce.ProductReviews(ProductId, ReviewDate) INCLUDE (Rating, HelpfulVotes);
CREATE INDEX IX_CampaignInteractions_Promotion ON ecommerce.CampaignInteractions(PromotionId, InteractionType, InteractionDate);
CREATE INDEX IX_CampaignInteractions_Customer ON ecommerce.CampaignInteractions(CustomerId, InteractionDate);
GO
