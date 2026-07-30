"""Data-quality checks for source tables and derived metric reconciliation."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

import numpy as np
import pandas as pd

from .contracts import CONTRACTS, DataQualityError


@dataclass
class QualityReport:
    """Serializable results of structural, relational, and statistical checks."""

    status: str = "PASS"
    checks_passed: int = 0
    row_counts: dict[str, int] = field(default_factory=dict)
    unexpected_missing_values: dict[str, int] = field(default_factory=dict)
    expected_null_values: dict[str, int] = field(default_factory=dict)
    outlier_counts: dict[str, int] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def _check(report: QualityReport, condition: bool, message: str) -> None:
    if condition:
        report.checks_passed += 1
    else:
        report.errors.append(message)


def _foreign_key_check(
    report: QualityReport,
    child: pd.DataFrame,
    child_column: str,
    parent: pd.DataFrame,
    parent_column: str,
    label: str,
) -> None:
    values = child[child_column].dropna()
    _check(report, values.isin(parent[parent_column]).all(), f"Orphan foreign keys detected: {label}")


def validate_sources(data: dict[str, pd.DataFrame]) -> QualityReport:
    """Validate required values, primary keys, relationships, ranges, and outliers."""
    report = QualityReport(row_counts={name: len(frame) for name, frame in data.items()})
    for table, contract in CONTRACTS.items():
        frame = data[table]
        required_columns = sorted(set(contract.columns) - set(contract.nullable_columns))
        report.unexpected_missing_values[table] = int(frame[required_columns].isna().sum().sum())
        report.expected_null_values[table] = int(frame[list(contract.nullable_columns)].isna().sum().sum()) if contract.nullable_columns else 0
        _check(report, report.unexpected_missing_values[table] == 0, f"Unexpected null values in {table}")
        _check(report, frame[contract.primary_key].notna().all(), f"Null primary key in {table}")
        _check(report, frame[contract.primary_key].is_unique, f"Duplicate primary key in {table}")

    _foreign_key_check(report, data["orders"], "CustomerId", data["customers"], "CustomerId", "orders.CustomerId")
    _foreign_key_check(report, data["orders"], "ShippingAddressId", data["addresses"], "AddressId", "orders.ShippingAddressId")
    _foreign_key_check(report, data["order_items"], "OrderId", data["orders"], "OrderId", "order_items.OrderId")
    _foreign_key_check(report, data["order_items"], "ProductId", data["products"], "ProductId", "order_items.ProductId")
    _foreign_key_check(report, data["return_items"], "ReturnId", data["returns"], "ReturnId", "return_items.ReturnId")
    _foreign_key_check(report, data["return_items"], "OrderItemId", data["order_items"], "OrderItemId", "return_items.OrderItemId")
    _foreign_key_check(report, data["product_reviews"], "OrderItemId", data["order_items"], "OrderItemId", "reviews.OrderItemId")

    items = data["order_items"]
    _check(report, items["Quantity"].gt(0).all(), "Non-positive order quantity detected")
    _check(report, items[["UnitPrice", "UnitCost", "DiscountAmount"]].ge(0).all().all(), "Negative line economics detected")
    _check(report, items["DiscountAmount"].le(items["Quantity"] * items["UnitPrice"] + 0.001).all(), "Discount exceeds gross line value")
    _check(report, data["product_reviews"]["Rating"].between(1, 5).all(), "Review rating outside 1-5")

    line_value = items["Quantity"] * items["UnitPrice"] - items["DiscountAmount"]
    q1, q3 = line_value.quantile([0.25, 0.75])
    upper = q3 + 3 * (q3 - q1)
    report.outlier_counts["high_value_order_lines"] = int((line_value > upper).sum())
    if report.outlier_counts["high_value_order_lines"]:
        report.warnings.append("High-value order lines were retained as plausible commercial observations.")

    delivery = data["shipments"].dropna(subset=["ShippedDate", "DeliveredDate"]).copy()
    delivery_days = (delivery["DeliveredDate"].dt.normalize() - delivery["ShippedDate"].dt.normalize()).dt.days
    report.outlier_counts["delivery_over_14_days"] = int((delivery_days > 14).sum())
    _check(report, delivery_days.ge(0).all(), "Delivery precedes shipment")

    if report.errors:
        report.status = "FAIL"
        raise DataQualityError("; ".join(report.errors))
    return report


def validate_metric_reconciliation(
    report: QualityReport,
    order_lines: pd.DataFrame,
    orders: pd.DataFrame,
) -> None:
    """Ensure Python order-grain metrics reconcile to line-grain SQL definitions."""
    line_totals = order_lines.groupby("OrderId", as_index=False).agg(
        NetRevenue=("NetRevenue", "sum"),
        RefundAmount=("RefundAmount", "sum"),
        RevenueAfterRefund=("RevenueAfterRefund", "sum"),
        GrossProfit=("GrossProfit", "sum"),
        GrossProfitAfterRefund=("GrossProfitAfterRefund", "sum"),
    )
    merged = orders.merge(line_totals, on="OrderId", suffixes=("_order", "_line"), validate="one_to_one")
    metrics = ("NetRevenue", "RefundAmount", "RevenueAfterRefund", "GrossProfit", "GrossProfitAfterRefund")
    for metric in metrics:
        difference = (merged[f"{metric}_order"] - merged[f"{metric}_line"]).abs()
        _check(report, difference.le(0.01).all(), f"Order/line reconciliation failed for {metric}")
    _check(report, orders["RevenueAfterRefund"].le(orders["NetRevenue"] + 0.001).all(), "After-refund revenue exceeds booked revenue")
    if report.errors:
        report.status = "FAIL"
        raise DataQualityError("; ".join(report.errors))
