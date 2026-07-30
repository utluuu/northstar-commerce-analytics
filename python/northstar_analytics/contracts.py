"""Column contracts and validation errors for generated source tables."""
from __future__ import annotations

from dataclasses import dataclass


class DataQualityError(RuntimeError):
    """Raised when source data violates an analytical data contract."""


@dataclass(frozen=True)
class TableContract:
    """Required columns, primary key, and parsing hints for one source table."""

    columns: tuple[str, ...]
    primary_key: str
    date_columns: tuple[str, ...] = ()
    nullable_columns: tuple[str, ...] = ()


CONTRACTS: dict[str, TableContract] = {
    "customer_segments": TableContract(("SegmentId", "SegmentName"), "SegmentId"),
    "customers": TableContract(
        ("CustomerId", "AcquisitionDate", "AcquisitionSource", "SegmentId", "IsActive"),
        "CustomerId", ("AcquisitionDate", "CreatedAt"),
    ),
    "addresses": TableContract(("AddressId", "CustomerId", "City", "StateProvince", "Region"), "AddressId"),
    "categories": TableContract(("CategoryId", "CategoryName", "ParentCategoryId"), "CategoryId", nullable_columns=("ParentCategoryId",)),
    "products": TableContract(
        ("ProductId", "SKU", "ProductName", "BrandName", "CategoryId", "UnitCost", "ListPrice"),
        "ProductId", ("LaunchDate",),
    ),
    "sales_channels": TableContract(("ChannelId", "ChannelName"), "ChannelId"),
    "order_statuses": TableContract(("StatusId", "StatusName"), "StatusId"),
    "promotions": TableContract(
        ("PromotionId", "PromotionCode", "PromotionName", "PromotionType", "DiscountValue"),
        "PromotionId", ("StartDate", "EndDate"), ("ChannelId",),
    ),
    "orders": TableContract(
        ("OrderId", "CustomerId", "ShippingAddressId", "ChannelId", "StatusId", "OrderDate", "ShippingAmount", "TaxAmount"),
        "OrderId", ("OrderDate",),
    ),
    "order_items": TableContract(
        ("OrderItemId", "OrderId", "ProductId", "Quantity", "UnitPrice", "UnitCost", "DiscountAmount"),
        "OrderItemId",
    ),
    "payments": TableContract(("PaymentId", "OrderId", "PaymentDate", "PaymentStatus", "Amount"), "PaymentId", ("PaymentDate",)),
    "shipments": TableContract(
        ("ShipmentId", "OrderId", "Carrier", "ShippedDate", "PromisedDeliveryDate", "DeliveredDate", "ShippingStatus"),
        "ShipmentId", ("ShippedDate", "PromisedDeliveryDate", "DeliveredDate"),
        ("ShippedDate", "PromisedDeliveryDate", "DeliveredDate"),
    ),
    "returns": TableContract(("ReturnId", "OrderId", "ReturnDate", "ReturnReason", "ReturnStatus"), "ReturnId", ("ReturnDate",)),
    "return_items": TableContract(("ReturnItemId", "ReturnId", "OrderItemId", "ReturnQuantity", "RefundAmount"), "ReturnItemId"),
    "product_reviews": TableContract(
        ("ReviewId", "CustomerId", "ProductId", "OrderItemId", "ReviewDate", "Rating"),
        "ReviewId", ("ReviewDate",),
    ),
    "campaign_interactions": TableContract(
        ("InteractionId", "PromotionId", "CustomerId", "InteractionDate", "InteractionType", "ChannelName", "OrderId"),
        "InteractionId", ("InteractionDate",), ("OrderId",),
    ),
    "date_dimension": TableContract(("DateKey", "FullDate", "CalendarYear", "MonthNumber", "YearMonth"), "DateKey", ("FullDate",)),
}
