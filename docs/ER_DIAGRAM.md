# Entity Relationship Diagram

```mermaid
erDiagram
    CUSTOMER_SEGMENTS {
        tinyint SegmentId PK
        varchar SegmentName UK
    }
    CUSTOMERS {
        int CustomerId PK
        nvarchar Email UK
        date AcquisitionDate
        varchar AcquisitionSource
        tinyint SegmentId FK
        bit IsActive
    }
    ADDRESSES {
        int AddressId PK
        int CustomerId FK
        varchar AddressType
        nvarchar City
        nvarchar StateProvince
        varchar Region
        char CountryCode
    }
    CATEGORIES {
        smallint CategoryId PK
        nvarchar CategoryName UK
        smallint ParentCategoryId FK
    }
    PRODUCTS {
        int ProductId PK
        varchar SKU UK
        nvarchar BrandName
        smallint CategoryId FK
        decimal UnitCost
        decimal ListPrice
    }
    SALES_CHANNELS {
        tinyint ChannelId PK
        varchar ChannelName UK
    }
    ORDER_STATUSES {
        tinyint StatusId PK
        varchar StatusName UK
    }
    ORDERS {
        int OrderId PK
        int CustomerId FK
        int ShippingAddressId FK
        tinyint ChannelId FK
        tinyint StatusId FK
        int PromotionId FK
        datetime OrderDate
    }
    PROMOTIONS {
        int PromotionId PK
        varchar PromotionCode UK
        varchar PromotionType
        decimal DiscountValue
        datetime StartDate
        datetime EndDate
    }
    ORDER_ITEMS {
        bigint OrderItemId PK
        int OrderId FK
        int ProductId FK
        smallint Quantity
        decimal UnitPrice
        decimal UnitCost
        decimal DiscountAmount
    }
    PAYMENTS {
        bigint PaymentId PK
        int OrderId FK
        varchar PaymentMethod
        varchar PaymentStatus
        decimal Amount
    }
    SHIPMENTS {
        bigint ShipmentId PK
        int OrderId FK,UK
        varchar Carrier
        date PromisedDeliveryDate
        datetime DeliveredDate
    }
    RETURNS {
        bigint ReturnId PK
        int OrderId FK
        date ReturnDate
        varchar ReturnReason
        varchar ReturnStatus
    }
    RETURN_ITEMS {
        bigint ReturnItemId PK
        bigint ReturnId FK
        bigint OrderItemId FK
        smallint ReturnQuantity
        decimal RefundAmount
    }
    PRODUCT_REVIEWS {
        bigint ReviewId PK
        int CustomerId FK
        int ProductId FK
        bigint OrderItemId FK
        tinyint Rating
        datetime ReviewDate
    }
    CAMPAIGN_INTERACTIONS {
        bigint InteractionId PK
        int PromotionId FK
        int CustomerId FK
        int OrderId FK
        varchar InteractionType
        datetime InteractionDate
    }

    CUSTOMER_SEGMENTS ||--o{ CUSTOMERS : classifies
    CUSTOMERS ||--o{ ADDRESSES : has
    CUSTOMERS ||--o{ ORDERS : places
    ADDRESSES ||--o{ ORDERS : ships_to
    SALES_CHANNELS ||--o{ ORDERS : originates
    ORDER_STATUSES ||--o{ ORDERS : tracks
    PROMOTIONS ||--o{ ORDERS : discounts
    CATEGORIES ||--o{ CATEGORIES : contains
    CATEGORIES ||--o{ PRODUCTS : classifies
    ORDERS ||--|{ ORDER_ITEMS : contains
    PRODUCTS ||--o{ ORDER_ITEMS : appears_in
    ORDERS ||--o{ PAYMENTS : paid_by
    ORDERS ||--o| SHIPMENTS : fulfilled_by
    ORDERS ||--o{ RETURNS : may_have
    RETURNS ||--|{ RETURN_ITEMS : contains
    ORDER_ITEMS ||--o{ RETURN_ITEMS : references
    CUSTOMERS ||--o{ PRODUCT_REVIEWS : writes
    PRODUCTS ||--o{ PRODUCT_REVIEWS : receives
    ORDER_ITEMS ||--o| PRODUCT_REVIEWS : verifies
    PROMOTIONS ||--o{ CAMPAIGN_INTERACTIONS : generates
    CUSTOMERS ||--o{ CAMPAIGN_INTERACTIONS : performs
    ORDERS ||--o{ CAMPAIGN_INTERACTIONS : attributes
```

## Modeling decisions

- Customers and addresses are separated because a customer may maintain multiple billing or shipping addresses.
- Categories are self-referencing, allowing future subcategories without redesigning products.
- Order items snapshot unit price and cost at purchase time to preserve historical margin.
- Payments support multiple attempts or split tenders, although seed data uses one payment per order.
- Returns and return items are separated so one return request can contain multiple order lines.
- Promotions and campaign interactions are separated so exposure, engagement, conversion, and order economics can be analyzed independently.
- Product reviews reference the purchased order line, enabling verified-purchase and return-versus-rating analysis.
- The reporting schema exposes denormalized views; the transactional schema remains normalized.
