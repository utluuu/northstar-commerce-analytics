"""Validate generated files, relationships, scale, and business realism."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def rows(directory: Path, table: str):
    with (directory / f"{table}.csv").open(newline="", encoding="utf-8") as handle:
        yield from csv.DictReader(handle)


def unique_keys(directory: Path, table: str, key: str) -> set[int]:
    values = [int(row[key]) for row in rows(directory, table)]
    if len(values) != len(set(values)):
        raise AssertionError(f"{table}.{key} contains duplicate values")
    return set(values)


def validate(directory: Path) -> dict:
    manifest_path = directory / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing manifest: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for table, metadata in manifest["tables"].items():
        path = directory / metadata["file"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != metadata["sha256"]:
            raise AssertionError(f"Checksum mismatch: {path.name}")

    counts = {name: meta["rows"] for name, meta in manifest["tables"].items()}
    assert counts["customers"] >= 10_000, "Customer scale target not met"
    assert counts["products"] >= 500, "Product scale target not met"
    assert counts["orders"] >= 100_000, "Order scale target not met"
    assert counts["order_items"] > counts["orders"] * 1.8, "Orders are not sufficiently multi-line"
    assert counts["payments"] >= counts["orders"], "Every order must have a payment outcome"
    assert counts["shipments"] > counts["orders"] * 0.90, "Shipment coverage is unexpectedly low"
    assert counts["returns"] > 0 and counts["product_reviews"] > 0 and counts["campaign_interactions"] > 0

    customers = unique_keys(directory, "customers", "CustomerId")
    addresses = unique_keys(directory, "addresses", "AddressId")
    products = unique_keys(directory, "products", "ProductId")
    promotions = unique_keys(directory, "promotions", "PromotionId")
    orders = unique_keys(directory, "orders", "OrderId")
    order_items = unique_keys(directory, "order_items", "OrderItemId")

    order_customer, customer_orders, month_orders = {}, Counter(), Counter()
    for row in rows(directory, "orders"):
        oid, customer_id = int(row["OrderId"]), int(row["CustomerId"])
        assert customer_id in customers and int(row["ShippingAddressId"]) in addresses
        if row["PromotionId"]: assert int(row["PromotionId"]) in promotions
        order_customer[oid] = customer_id; customer_orders[customer_id] += 1
        month_orders[datetime.fromisoformat(row["OrderDate"]).month] += 1

    line_counts = Counter()
    for row in rows(directory, "order_items"):
        assert int(row["OrderId"]) in orders and int(row["ProductId"]) in products
        assert float(row["DiscountAmount"]) <= int(row["Quantity"]) * float(row["UnitPrice"])
        line_counts[int(row["OrderId"])] += 1
    assert set(line_counts) == orders, "Every order must have at least one item"

    for row in rows(directory, "returns"): assert int(row["OrderId"]) in orders
    for row in rows(directory, "return_items"): assert int(row["OrderItemId"]) in order_items
    for row in rows(directory, "product_reviews"):
        assert int(row["CustomerId"]) in customers and int(row["ProductId"]) in products and int(row["OrderItemId"]) in order_items
        assert 1 <= int(row["Rating"]) <= 5
    for row in rows(directory, "campaign_interactions"):
        assert int(row["CustomerId"]) in customers and int(row["PromotionId"]) in promotions
        if row["OrderId"]: assert int(row["OrderId"]) in orders

    repeat_customers = sum(value >= 2 for value in customer_orders.values())
    repeat_rate = repeat_customers / len(customers)
    assert 0.60 <= repeat_rate <= 0.85, f"Repeat-customer rate is outside the expected range: {repeat_rate:.1%}"
    holiday_ratio = (month_orders[11] + month_orders[12]) / max(1, month_orders[1] + month_orders[2])
    assert 1.45 <= holiday_ratio <= 3.50, f"Seasonality is outside the expected range: {holiday_ratio:.2f}"

    results = {
        "status": "PASS", "customers": counts["customers"], "products": counts["products"],
        "orders": counts["orders"], "order_items": counts["order_items"],
        "average_lines_per_order": round(counts["order_items"] / counts["orders"], 2),
        "repeat_customer_rate": round(repeat_rate, 4), "holiday_to_early_year_ratio": round(holiday_ratio, 2),
    }
    (directory / "validation_report.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate generated Northstar Commerce data.")
    parser.add_argument("--input", type=Path, default=ROOT / "data" / "generated")
    args = parser.parse_args()
    print(json.dumps(validate(args.input), indent=2))


if __name__ == "__main__":
    main()
