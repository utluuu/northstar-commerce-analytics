"""Bulk-load generated CSV files into SQL Server using fast_executemany."""
from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[1]

TABLES = [
    ("CustomerSegments", "customer_segments", False), ("SalesChannels", "sales_channels", True),
    ("OrderStatuses", "order_statuses", True), ("Customers", "customers", True),
    ("Addresses", "addresses", True), ("Categories", "categories", True), ("Products", "products", True),
    ("Promotions", "promotions", False), ("Orders", "orders", True), ("OrderItems", "order_items", True),
    ("Payments", "payments", True), ("Shipments", "shipments", True), ("Returns", "returns", True),
    ("ReturnItems", "return_items", True), ("ProductReviews", "product_reviews", False),
    ("CampaignInteractions", "campaign_interactions", False),
]
DELETE_ORDER = [x[0] for x in reversed(TABLES)]


def engine_from_env():
    load_dotenv(ROOT / ".env")
    server, database = os.getenv("DB_SERVER", "localhost"), os.getenv("DB_NAME", "NorthstarCommerce")
    driver = os.getenv("DB_DRIVER", "ODBC Driver 18 for SQL Server")
    if os.getenv("DB_TRUSTED_CONNECTION", "yes").lower() == "yes":
        auth = "Trusted_Connection=yes"
    else:
        auth = f"UID={os.environ['DB_USER']};PWD={os.environ['DB_PASSWORD']}"
    connection = quote_plus(f"DRIVER={{{driver}}};SERVER={server};DATABASE={database};{auth};TrustServerCertificate=yes")
    return create_engine(f"mssql+pyodbc:///?odbc_connect={connection}", fast_executemany=True)


def batches(reader, size: int):
    batch = []
    for row in reader:
        batch.append({key: value if value != "" else None for key, value in row.items()})
        if len(batch) == size:
            yield batch; batch = []
    if batch: yield batch


def load(input_dir: Path, batch_size: int) -> None:
    engine = engine_from_env()
    with engine.begin() as connection:
        connection.execute(text("IF OBJECT_ID(N'analytics.CustomerRfmSnapshot', N'U') IS NOT NULL DELETE FROM analytics.CustomerRfmSnapshot"))
        for table in DELETE_ORDER:
            connection.execute(text(f"DELETE FROM ecommerce.{table}"))
        connection.execute(text("DELETE FROM analytics.DimDate"))

    for table, filename, identity in TABLES:
        path = input_dir / f"{filename}.csv"
        with path.open(newline="", encoding="utf-8") as handle, engine.begin() as connection:
            reader = csv.DictReader(handle); columns = reader.fieldnames or []
            statement = text(f"INSERT INTO ecommerce.{table} ({', '.join(columns)}) VALUES ({', '.join(':' + c for c in columns)})")
            if identity: connection.execute(text(f"SET IDENTITY_INSERT ecommerce.{table} ON"))
            loaded = 0
            for batch in batches(reader, batch_size): connection.execute(statement, batch); loaded += len(batch)
            if identity: connection.execute(text(f"SET IDENTITY_INSERT ecommerce.{table} OFF"))
        print(f"Loaded ecommerce.{table}: {loaded:,} rows")

    path = input_dir / "date_dimension.csv"
    with path.open(newline="", encoding="utf-8") as handle, engine.begin() as connection:
        reader = csv.DictReader(handle); columns = reader.fieldnames or []
        statement = text(f"INSERT INTO analytics.DimDate ({', '.join(columns)}) VALUES ({', '.join(':' + c for c in columns)})")
        loaded = 0
        for batch in batches(reader, batch_size): connection.execute(statement, batch); loaded += len(batch)
    print(f"Loaded analytics.DimDate: {loaded:,} rows")


def main() -> None:
    parser = argparse.ArgumentParser(description="Load generated data into SQL Server.")
    parser.add_argument("--input", type=Path, default=ROOT / "data" / "generated")
    parser.add_argument("--batch-size", type=int, default=5000)
    args = parser.parse_args(); load(args.input, args.batch_size)


if __name__ == "__main__":
    main()
