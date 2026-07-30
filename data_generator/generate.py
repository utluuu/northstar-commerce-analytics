"""Generate relational e-commerce CSV data with deterministic business behavior."""
from __future__ import annotations

import argparse
import bisect
import csv
import hashlib
import json
import math
import platform
import random
from collections import Counter, defaultdict
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Iterable

from data_generator.catalogs import (
    ACQUISITION_SOURCES, BRANDS, CARRIERS, CATEGORY_TREE, CHANNELS, CITIES, FIRST_NAMES,
    LAST_NAMES, MONTH_MULTIPLIERS, ORDER_STATUSES, PAYMENT_METHODS, PRODUCT_ADJECTIVES,
    PRODUCT_NOUNS, RETURN_REASONS, SEGMENTS,
)

ROOT = Path(__file__).resolve().parents[1]


class CsvSink:
    def __init__(self, directory: Path, name: str, fields: list[str]):
        self.path = directory / f"{name}.csv"
        self.handle = self.path.open("w", newline="", encoding="utf-8")
        self.writer = csv.DictWriter(self.handle, fieldnames=fields, extrasaction="ignore")
        self.writer.writeheader()
        self.count = 0

    def write(self, row: dict) -> None:
        self.writer.writerow(row)
        self.count += 1

    def close(self) -> None:
        self.handle.close()


def iso(value: date | datetime | None) -> str:
    return "" if value is None else value.isoformat(sep=" ", timespec="seconds") if isinstance(value, datetime) else value.isoformat()


def money(value: float) -> str:
    return f"{value:.2f}"


def weighted_choice(rng: random.Random, values: Iterable, weights: Iterable[float]):
    return rng.choices(list(values), weights=list(weights), k=1)[0]


class WeightedSampler:
    """Reusable weighted sampler that computes cumulative weights once."""

    def __init__(self, values: Iterable, weights: Iterable[float]):
        self.values = list(values)
        self.cumulative = []
        total = 0.0
        for weight in weights:
            total += weight
            self.cumulative.append(total)
        if not self.values or len(self.values) != len(self.cumulative) or total <= 0:
            raise ValueError("WeightedSampler requires matching values and positive weights")
        self.total = total

    def sample(self, rng: random.Random):
        return self.values[bisect.bisect_left(self.cumulative, rng.random() * self.total)]


def load_config(path: Path) -> dict:
    config = json.loads(path.read_text(encoding="utf-8"))
    for key in ("seed", "customers", "products", "orders"):
        if int(config[key]) <= 0:
            raise ValueError(f"{key} must be positive")
    if config["customers"] < 10_000 or config["products"] < 500 or config["orders"] < 100_000:
        raise ValueError("Portfolio scale must be at least 10,000 customers, 500 products, and 100,000 orders.")
    return config


def build_dates(start: date, end: date) -> tuple[list[date], list[float]]:
    dates, weights = [], []
    current = start
    while current <= end:
        year_growth = 1.0 + 0.16 * (current.year - start.year)
        weekend = 1.10 if current.weekday() >= 5 else 1.0
        holiday = 1.5 if current.month == 11 and 22 <= current.day <= 30 else 1.0
        holiday *= 1.35 if current.month == 12 and 10 <= current.day <= 23 else 1.0
        dates.append(current)
        weights.append(MONTH_MULTIPLIERS[current.month] * year_growth * weekend * holiday)
        current += timedelta(days=1)
    return dates, weights


def promotion_catalog(start: date, end: date) -> list[dict]:
    specs = [
        ("NEWYEAR10", "New Year Refresh", "Percentage", 10, 50, 1, 1, 1, 31),
        ("SPRING15", "Spring Event", "Percentage", 15, 75, 3, 15, 4, 15),
        ("SUMMER20", "Summer Sale", "Percentage", 20, 100, 6, 15, 7, 15),
        ("FALL10", "Fall Essentials", "Percentage", 10, 60, 9, 1, 9, 30),
        ("CYBER20", "Cyber Week", "Percentage", 20, 120, 11, 20, 12, 2),
        ("HOLIDAY15", "Holiday Event", "Percentage", 15, 80, 12, 3, 12, 24),
    ]
    rows, promotion_id = [], 1
    for year in range(start.year, end.year + 1):
        for code, name, kind, value, minimum, sm, sd, em, ed in specs:
            end_year = year + 1 if em < sm else year
            rows.append({"PromotionId": promotion_id, "PromotionCode": f"{code}-{year}",
                         "PromotionName": f"{name} {year}", "PromotionType": kind,
                         "DiscountValue": money(value), "MinimumOrderValue": money(minimum),
                         "StartDate": iso(datetime.combine(date(year, sm, sd), time())),
                         "EndDate": iso(datetime.combine(date(end_year, em, ed), time(23, 59, 59))),
                         "ChannelId": "" if promotion_id % 3 else 2})
            promotion_id += 1
    return rows


def generate(config: dict, output_dir: Path) -> dict:
    rng = random.Random(config["seed"])
    output_dir.mkdir(parents=True, exist_ok=True)
    for pattern in ("*.csv", "manifest.json", "validation_report.json"):
        for generated_file in output_dir.glob(pattern):
            generated_file.unlink()
    start, end = date.fromisoformat(config["start_date"]), date.fromisoformat(config["end_date"])

    fields = {
        "customer_segments": ["SegmentId", "SegmentName", "Description"],
        "customers": ["CustomerId", "FirstName", "LastName", "Email", "Phone", "AcquisitionDate", "AcquisitionSource", "SegmentId", "IsActive", "CreatedAt"],
        "addresses": ["AddressId", "CustomerId", "AddressType", "AddressLine1", "City", "StateProvince", "Region", "PostalCode", "CountryCode", "IsDefault"],
        "categories": ["CategoryId", "CategoryName", "ParentCategoryId"],
        "products": ["ProductId", "SKU", "ProductName", "BrandName", "CategoryId", "UnitCost", "ListPrice", "LaunchDate", "IsActive"],
        "sales_channels": ["ChannelId", "ChannelName"], "order_statuses": ["StatusId", "StatusName"],
        "promotions": ["PromotionId", "PromotionCode", "PromotionName", "PromotionType", "DiscountValue", "MinimumOrderValue", "StartDate", "EndDate", "ChannelId"],
        "orders": ["OrderId", "CustomerId", "ShippingAddressId", "ChannelId", "StatusId", "PromotionId", "OrderDate", "PromoCode", "ShippingAmount", "TaxAmount"],
        "order_items": ["OrderItemId", "OrderId", "ProductId", "Quantity", "UnitPrice", "UnitCost", "DiscountAmount"],
        "payments": ["PaymentId", "OrderId", "PaymentDate", "PaymentMethod", "PaymentStatus", "Amount", "TransactionRef"],
        "shipments": ["ShipmentId", "OrderId", "Carrier", "TrackingNumber", "ShippedDate", "PromisedDeliveryDate", "DeliveredDate", "ShippingStatus"],
        "returns": ["ReturnId", "OrderId", "ReturnDate", "ReturnReason", "ReturnStatus"],
        "return_items": ["ReturnItemId", "ReturnId", "OrderItemId", "ReturnQuantity", "RefundAmount"],
        "product_reviews": ["ReviewId", "CustomerId", "ProductId", "OrderItemId", "ReviewDate", "Rating", "ReviewTitle", "ReviewText", "IsVerifiedPurchase", "HelpfulVotes"],
        "campaign_interactions": ["InteractionId", "PromotionId", "CustomerId", "InteractionDate", "InteractionType", "ChannelName", "OrderId"],
        "date_dimension": ["DateKey", "FullDate", "CalendarYear", "CalendarQuarter", "MonthNumber", "MonthName", "YearMonth", "WeekOfYear", "DayOfMonth", "DayName", "IsWeekend"],
    }
    sinks = {name: CsvSink(output_dir, name, cols) for name, cols in fields.items()}

    for sid, name, description, _, _ in SEGMENTS:
        sinks["customer_segments"].write({"SegmentId": sid, "SegmentName": name, "Description": description})
    for channel_id, name in CHANNELS: sinks["sales_channels"].write({"ChannelId": channel_id, "ChannelName": name})
    for status_id, name in ORDER_STATUSES: sinks["order_statuses"].write({"StatusId": status_id, "StatusName": name})

    category_ids, cid = {}, 1
    for parent, children in CATEGORY_TREE.items():
        category_ids[parent] = cid; sinks["categories"].write({"CategoryId": cid, "CategoryName": parent, "ParentCategoryId": ""}); cid += 1
        for child in children:
            category_ids[child] = cid; sinks["categories"].write({"CategoryId": cid, "CategoryName": child, "ParentCategoryId": category_ids[parent]}); cid += 1
    leaf_categories = [child for children in CATEGORY_TREE.values() for child in children]

    product_rows = {}
    for product_id in range(1, config["products"] + 1):
        category = leaf_categories[(product_id - 1) % len(leaf_categories)]
        base_cost = round(math.exp(rng.uniform(math.log(4), math.log(180))), 2)
        margin = rng.uniform(1.65, 2.65)
        row = {"ProductId": product_id, "SKU": f"NS-{category_ids[category]:02d}-{product_id:05d}",
               "ProductName": f"{PRODUCT_ADJECTIVES[(product_id * 7) % len(PRODUCT_ADJECTIVES)]} {PRODUCT_NOUNS[(product_id * 11) % len(PRODUCT_NOUNS)]} {product_id:03d}",
               "BrandName": BRANDS[(product_id * 13) % len(BRANDS)], "CategoryId": category_ids[category],
               "UnitCost": money(base_cost), "ListPrice": money(round(base_cost * margin, 2)),
               "LaunchDate": iso(start - timedelta(days=rng.randint(30, 900))), "IsActive": 0 if product_id % 79 == 0 else 1}
        product_rows[product_id] = row; sinks["products"].write(row)

    segment_weights = [x[3] for x in SEGMENTS]
    segment_propensity = {x[0]: x[4] for x in SEGMENTS}
    customers, addresses, lifecycle = {}, {}, {}
    city_weights = [x[4] for x in CITIES]
    for customer_id in range(1, config["customers"] + 1):
        segment_id = weighted_choice(rng, [x[0] for x in SEGMENTS], segment_weights)
        acquired = start - timedelta(days=rng.randint(0, 365)) + timedelta(days=rng.randint(0, (end - start).days))
        acquired = min(acquired, end - timedelta(days=7))
        city, state, region, postal, _ = weighted_choice(rng, CITIES, city_weights)
        first, last = rng.choice(FIRST_NAMES), rng.choice(LAST_NAMES)
        customer = {"CustomerId": customer_id, "FirstName": first, "LastName": last,
                    "Email": f"customer{customer_id:05d}@example.com", "Phone": f"+1-555-{customer_id:07d}",
                    "AcquisitionDate": iso(acquired), "AcquisitionSource": weighted_choice(rng, ACQUISITION_SOURCES, [28, 20, 17, 14, 12, 9]),
                    "SegmentId": segment_id, "IsActive": 0 if rng.random() < 0.035 else 1,
                    "CreatedAt": iso(datetime.combine(acquired, time(rng.randrange(8, 22), rng.randrange(60))))}
        address = {"AddressId": customer_id, "CustomerId": customer_id, "AddressType": "Shipping",
                   "AddressLine1": f"{rng.randint(10, 9999)} {rng.choice(['Market','Oak','Maple','Main','Lake','Hill'])} Street",
                   "City": city, "StateProvince": state, "Region": region, "PostalCode": postal, "CountryCode": "US", "IsDefault": 1}
        customers[customer_id] = customer; addresses[customer_id] = address
        no_purchase_probability = {1: 0.16, 2: 0.03, 3: 0.01, 4: 0.08}[segment_id]
        one_time_probability = {1: 0.34, 2: 0.08, 3: 0.03, 4: 0.18}[segment_id]
        draw = rng.random()
        lifecycle[customer_id] = "none" if draw < no_purchase_probability else "one_time" if draw < no_purchase_probability + one_time_probability else "recurring"
        sinks["customers"].write(customer); sinks["addresses"].write(address)

    promotions = promotion_catalog(start, end)
    for row in promotions: sinks["promotions"].write(row)
    promo_by_date = defaultdict(list)
    for promo in promotions:
        d, last = date.fromisoformat(promo["StartDate"][:10]), date.fromisoformat(promo["EndDate"][:10])
        while d <= last: promo_by_date[d].append(promo); d += timedelta(days=1)

    calendar_dates, calendar_weights = build_dates(start, end)
    customer_ids = list(customers)
    one_time_customers = [customer_id for customer_id in customer_ids if lifecycle[customer_id] == "one_time"]
    recurring_customers = [customer_id for customer_id in customer_ids if lifecycle[customer_id] == "recurring"]
    order_weights = [segment_propensity[customers[c]["SegmentId"]] * rng.lognormvariate(0, 0.55) for c in recurring_customers]
    product_ids = list(product_rows)
    product_weights = [1.0 / ((i + 8) ** 0.55) for i in range(len(product_ids))]
    date_sampler = WeightedSampler(calendar_dates, calendar_weights)
    customer_sampler = WeightedSampler(recurring_customers, order_weights)
    product_sampler = WeightedSampler(product_ids, product_weights)
    promoted_orders = defaultdict(list)
    ids = Counter({"order": 10001, "item": 1, "payment": 1, "shipment": 1, "return": 1, "return_item": 1, "review": 1})
    segment_order_counts = Counter()

    if len(one_time_customers) >= config["orders"]:
        raise ValueError("Order target must exceed the number of one-time customers")
    order_customer_sequence = one_time_customers + [customer_sampler.sample(rng) for _ in range(config["orders"] - len(one_time_customers))]
    rng.shuffle(order_customer_sequence)

    for customer_id in order_customer_sequence:
        customer = customers[customer_id]
        while True:
            order_day = date_sampler.sample(rng)
            if order_day >= date.fromisoformat(customer["AcquisitionDate"]): break
        order_dt = datetime.combine(order_day, time(rng.choices(range(24), weights=[1,1,1,1,1,1,2,3,4,5,6,7,8,8,7,7,8,10,11,10,8,6,4,2])[0], rng.randrange(60), rng.randrange(60)))
        segment_id = customer["SegmentId"]; segment_order_counts[segment_id] += 1
        channel_id = weighted_choice(rng, [1, 2, 3, 4], [44, 31, 17, 8])
        status_id = weighted_choice(rng, [1, 2, 3, 4, 5], [0.3, 0.7, 1.5, 94.3, 3.2])
        basket_lines = min(7, max(1, int(rng.lognormvariate(0.75 if segment_id != 3 else 1.05, 0.48))))
        chosen_products = [product_sampler.sample(rng) for _ in range(basket_lines * 2)]
        chosen_products = list(dict.fromkeys(chosen_products))[:basket_lines]
        while len(chosen_products) < basket_lines:
            candidate = product_sampler.sample(rng)
            if candidate not in chosen_products: chosen_products.append(candidate)
        item_specs, gross = [], 0.0
        for product_id in chosen_products:
            product = product_rows[product_id]; qty = weighted_choice(rng, [1, 2, 3, 4], [76, 17, 5, 2])
            price = float(product["ListPrice"]); item_specs.append((product_id, qty, price, float(product["UnitCost"])))
            gross += qty * price
        promo = None
        use_prob = {1: 0.13, 2: 0.19, 3: 0.16, 4: 0.38}[segment_id]
        eligible = [p for p in promo_by_date[order_day]
                    if (not p["ChannelId"] or int(p["ChannelId"]) == channel_id)
                    and gross >= float(p["MinimumOrderValue"])]
        if eligible and rng.random() < use_prob: promo = rng.choice(eligible)
        discount_rate = float(promo["DiscountValue"]) / 100 if promo and promo["PromotionType"] == "Percentage" else 0
        shipping = 0.0 if gross >= 90 or (promo and promo["PromotionType"] == "Free Shipping") else weighted_choice(rng, [5.99, 7.99, 11.99], [55, 35, 10])
        tax = round((gross * (1 - discount_rate)) * weighted_choice(rng, [0.0, 0.05, 0.0625, 0.0725, 0.0825], [5, 15, 25, 25, 30]), 2)
        order_id = ids["order"]; ids["order"] += 1
        order = {"OrderId": order_id, "CustomerId": customer_id, "ShippingAddressId": customer_id,
                 "ChannelId": channel_id, "StatusId": status_id, "PromotionId": promo["PromotionId"] if promo else "",
                 "OrderDate": iso(order_dt), "PromoCode": promo["PromotionCode"] if promo else "",
                 "ShippingAmount": money(shipping), "TaxAmount": money(tax)}
        sinks["orders"].write(order)
        if promo: promoted_orders[int(promo["PromotionId"])].append((customer_id, order_id, order_dt))

        order_items, net = [], 0.0
        for product_id, qty, price, cost in item_specs:
            discount = round(qty * price * discount_rate, 2)
            item = {"OrderItemId": ids["item"], "OrderId": order_id, "ProductId": product_id,
                    "Quantity": qty, "UnitPrice": money(price), "UnitCost": money(cost), "DiscountAmount": money(discount)}
            ids["item"] += 1; net += qty * price - discount; order_items.append(item); sinks["order_items"].write(item)

        payment_dt = order_dt + timedelta(minutes=rng.randint(1, 15)); total = round(net + shipping + tax, 2)
        if rng.random() < 0.025:
            sinks["payments"].write({"PaymentId": ids["payment"], "OrderId": order_id, "PaymentDate": iso(payment_dt),
                "PaymentMethod": rng.choice(PAYMENT_METHODS), "PaymentStatus": "Failed", "Amount": money(total), "TransactionRef": f"TXN-{order_id}-A1"})
            ids["payment"] += 1; payment_dt += timedelta(minutes=rng.randint(2, 10))
        pay_status = "Refunded" if status_id == 5 else "Captured"
        sinks["payments"].write({"PaymentId": ids["payment"], "OrderId": order_id, "PaymentDate": iso(payment_dt),
            "PaymentMethod": weighted_choice(rng, PAYMENT_METHODS, [47, 22, 20, 7, 4]), "PaymentStatus": pay_status,
            "Amount": money(total), "TransactionRef": f"TXN-{order_id}-FINAL"}); ids["payment"] += 1

        delivered_dt = None
        if status_id != 5:
            carrier = weighted_choice(rng, CARRIERS, [34, 29, 27, 10]); ship_dt = order_dt + timedelta(days=rng.randint(1, 3))
            promised = order_day + timedelta(days=weighted_choice(rng, [4, 5, 6, 7], [15, 40, 30, 15]))
            if status_id == 4:
                region_delay = 1 if addresses[customer_id]["Region"] == "West" and carrier == "USPS" else 0
                delivered_dt = ship_dt + timedelta(days=max(1, int(rng.gauss(3.2 + region_delay, 1.25))))
                shipping_status = "Delivered"
            else: shipping_status = "In Transit" if status_id == 3 else "Pending"
            sinks["shipments"].write({"ShipmentId": ids["shipment"], "OrderId": order_id, "Carrier": carrier,
                "TrackingNumber": f"TRK-{order_id:09d}", "ShippedDate": iso(ship_dt if status_id >= 3 else None),
                "PromisedDeliveryDate": iso(promised), "DeliveredDate": iso(delivered_dt), "ShippingStatus": shipping_status}); ids["shipment"] += 1

        returned_item_ids = set()
        if delivered_dt and rng.random() < config["base_return_rate"] * (1.25 if channel_id == 3 else 1):
            returned = rng.choice(order_items); returned_item_ids.add(returned["OrderItemId"])
            return_dt = delivered_dt.date() + timedelta(days=rng.randint(2, 28)); reason = weighted_choice(rng, RETURN_REASONS, [13, 7, 20, 34, 8, 18])
            sinks["returns"].write({"ReturnId": ids["return"], "OrderId": order_id, "ReturnDate": iso(return_dt),
                "ReturnReason": reason, "ReturnStatus": weighted_choice(rng, ["Requested", "Approved", "Received", "Refunded", "Rejected"], [3, 7, 15, 71, 4])})
            refund = float(returned["UnitPrice"]) - float(returned["DiscountAmount"]) / int(returned["Quantity"])
            sinks["return_items"].write({"ReturnItemId": ids["return_item"], "ReturnId": ids["return"],
                "OrderItemId": returned["OrderItemId"], "ReturnQuantity": 1, "RefundAmount": money(refund)})
            ids["return"] += 1; ids["return_item"] += 1

        if delivered_dt:
            for item in order_items:
                if rng.random() >= config["review_rate"]: continue
                base_rating = 2.2 if item["OrderItemId"] in returned_item_ids else 4.35
                rating = min(5, max(1, round(rng.gauss(base_rating, 0.85))))
                title = ["Very disappointing", "Could be better", "Good value", "Great product", "Exceeded expectations"][rating - 1]
                text = ["The product did not meet my expectations.", "Usable, but there is room for improvement.",
                        "Good overall value for the price.", "Works well and arrived as expected.", "Excellent quality and a smooth purchase experience."][rating - 1]
                sinks["product_reviews"].write({"ReviewId": ids["review"], "CustomerId": customer_id, "ProductId": item["ProductId"],
                    "OrderItemId": item["OrderItemId"], "ReviewDate": iso(delivered_dt + timedelta(days=rng.randint(1, 45))),
                    "Rating": rating, "ReviewTitle": title, "ReviewText": text, "IsVerifiedPurchase": 1,
                    "HelpfulVotes": min(250, int(rng.expovariate(0.20)))})
                ids["review"] += 1

    interaction_id = 1
    campaign_channels = ["Email", "Paid Social", "Display", "Push", "SMS"]
    for promo in promotions:
        pid = int(promo["PromotionId"]); start_dt = datetime.fromisoformat(promo["StartDate"]); end_dt = datetime.fromisoformat(promo["EndDate"])
        conversions = {(c, o): dt for c, o, dt in promoted_orders.get(pid, [])}
        converted_customers = {c for c, _ in conversions}
        audience_size = max(1, int(len(customer_ids) * rng.uniform(0.16, 0.28)))
        audience = set(rng.sample(customer_ids, k=audience_size)) | converted_customers
        for customer_id in audience:
            channel = weighted_choice(rng, campaign_channels, [38, 24, 13, 17, 8])
            sent_dt = start_dt + timedelta(seconds=rng.randint(0, max(1, int((end_dt - start_dt).total_seconds()))))
            sinks["campaign_interactions"].write({"InteractionId": interaction_id, "PromotionId": pid, "CustomerId": customer_id,
                "InteractionDate": iso(sent_dt), "InteractionType": "Sent" if channel in ("Email", "Push", "SMS") else "Impression", "ChannelName": channel, "OrderId": ""}); interaction_id += 1
            click_probability = 0.28 if customers[customer_id]["SegmentId"] == 4 else 0.13
            if rng.random() < click_probability:
                click_dt = min(end_dt, sent_dt + timedelta(hours=rng.randint(1, 72)))
                sinks["campaign_interactions"].write({"InteractionId": interaction_id, "PromotionId": pid, "CustomerId": customer_id,
                    "InteractionDate": iso(click_dt), "InteractionType": "Click", "ChannelName": channel, "OrderId": ""}); interaction_id += 1
        for (customer_id, order_id), order_dt in conversions.items():
            sinks["campaign_interactions"].write({"InteractionId": interaction_id, "PromotionId": pid, "CustomerId": customer_id,
                "InteractionDate": iso(order_dt), "InteractionType": "Conversion", "ChannelName": "Email", "OrderId": order_id}); interaction_id += 1

    current = start
    while current <= end + timedelta(days=365):
        sinks["date_dimension"].write({"DateKey": int(current.strftime("%Y%m%d")), "FullDate": iso(current), "CalendarYear": current.year,
            "CalendarQuarter": (current.month - 1) // 3 + 1, "MonthNumber": current.month, "MonthName": current.strftime("%B"),
            "YearMonth": current.strftime("%Y-%m"), "WeekOfYear": current.isocalendar().week, "DayOfMonth": current.day,
            "DayName": current.strftime("%A"), "IsWeekend": 1 if current.weekday() >= 5 else 0}); current += timedelta(days=1)

    for sink in sinks.values(): sink.close()
    files = {}
    for name, sink in sinks.items():
        digest = hashlib.sha256(sink.path.read_bytes()).hexdigest()
        files[name] = {"rows": sink.count, "sha256": digest, "file": sink.path.name}
    manifest = {"generator_version": "1.0.0", "python_version": platform.python_version(),
                "seed": config["seed"], "config": config, "tables": files,
                "business_profile": {"segment_order_counts": dict(segment_order_counts)}}
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate deterministic Northstar Commerce data.")
    parser.add_argument("--config", type=Path, default=ROOT / "data_generator" / "config.json")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(); config = load_config(args.config)
    output = args.output or ROOT / config["output_directory"]
    manifest = generate(config, output)
    print(json.dumps({name: meta["rows"] for name, meta in manifest["tables"].items()}, indent=2))
    print(f"Dataset written to {output}")


if __name__ == "__main__":
    main()
