"""Generate a Tabular Model (model.bim) for Northstar Commerce Analytics.

The output can be opened in Tabular Editor and deployed to Power BI Desktop,
or compiled to PBIT with pbi-tools when available.
"""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POWERBI_DIR = ROOT / "powerbi"
OUTPUT_DIR = POWERBI_DIR / "automation" / "generated"
MEASURES_PATH = POWERBI_DIR / "measures.dax"
DICTIONARY_PATH = POWERBI_DIR / "MEASURE_DICTIONARY.md"
RELATIONSHIPS_PATH = POWERBI_DIR / "relationship_manifest.csv"
DEFAULT_CSV_ROOT = ROOT / "data" / "processed"

# Power Query type -> Tabular dataType
PQ_TO_TABULAR = {
    "Int64.Type": "int64",
    "type date": "dateTime",
    "type datetime": "dateTime",
    "type text": "string",
    "type number": "double",
    "Currency.Type": "decimal",
    "Percentage.Type": "double",
}

TABLES: dict[str, dict[str, object]] = {
    "DimDate": {
        "file": "dim_date.csv",
        "types": [
            ("DateKey", "Int64.Type"),
            ("FullDate", "type date"),
            ("CalendarYear", "Int64.Type"),
            ("CalendarQuarter", "type text"),
            ("MonthNumber", "Int64.Type"),
            ("MonthName", "type text"),
            ("YearMonth", "type text"),
            ("WeekOfYear", "Int64.Type"),
            ("DayOfMonth", "Int64.Type"),
            ("DayName", "type text"),
            ("IsWeekend", "Int64.Type"),
        ],
        "hidden": False,
        "date_table": True,
        "sort_columns": {"MonthName": "MonthNumber"},
    },
    "DimCustomer": {
        "file": "dim_customers.csv",
        "types": [
            ("CustomerId", "Int64.Type"),
            ("AcquisitionDate", "type datetime"),
            ("AcquisitionSource", "type text"),
            ("SegmentName", "type text"),
            ("IsActive", "Int64.Type"),
            ("FirstOrderDate", "type datetime"),
            ("LastOrderDate", "type datetime"),
            ("LifetimeOrders", "Int64.Type"),
            ("LifetimeRevenue", "Currency.Type"),
            ("LifetimeRevenueAfterRefund", "Currency.Type"),
            ("LifetimeGrossProfit", "Currency.Type"),
            ("AverageOrderValue", "Currency.Type"),
            ("AvgDaysBetweenOrders", "type number"),
            ("RecencyDays", "Int64.Type"),
            ("IsRepeatCustomer", "Int64.Type"),
            ("Projected12MonthRevenue", "Currency.Type"),
            ("LifecycleStatus", "type text"),
        ],
    },
    "DimProduct": {
        "file": "dim_products.csv",
        "types": [
            ("ProductId", "Int64.Type"),
            ("SKU", "type text"),
            ("ProductName", "type text"),
            ("BrandName", "type text"),
            ("CategoryId", "Int64.Type"),
            ("UnitCost", "Currency.Type"),
            ("ListPrice", "Currency.Type"),
            ("LaunchDate", "type datetime"),
            ("IsActive", "Int64.Type"),
            ("SubcategoryName", "type text"),
            ("ParentCategoryId", "Int64.Type"),
            ("CategoryName", "type text"),
        ],
    },
    "DimChannel": {
        "file": "dim_channels.csv",
        "types": [("ChannelId", "Int64.Type"), ("ChannelName", "type text")],
    },
    "DimGeography": {
        "file": "dim_geography.csv",
        "types": [
            ("GeographyKey", "Int64.Type"),
            ("City", "type text"),
            ("StateProvince", "type text"),
            ("Region", "type text"),
            ("CountryCode", "type text"),
        ],
    },
    "DimPromotion": {
        "file": "dim_promotions.csv",
        "types": [
            ("PromotionId", "Int64.Type"),
            ("PromotionCode", "type text"),
            ("PromotionName", "type text"),
            ("PromotionType", "type text"),
            ("DiscountValue", "Currency.Type"),
            ("MinimumOrderValue", "Currency.Type"),
            ("StartDate", "type datetime"),
            ("EndDate", "type datetime"),
            ("ChannelId", "Int64.Type"),
        ],
    },
    "FactOrders": {
        "file": "fact_orders.csv",
        "types": [
            ("OrderId", "Int64.Type"),
            ("OrderDateKey", "Int64.Type"),
            ("OrderDate", "type datetime"),
            ("CustomerId", "Int64.Type"),
            ("CustomerOrderNumber", "Int64.Type"),
            ("IsRepeatPurchase", "Int64.Type"),
            ("ChannelId", "Int64.Type"),
            ("GeographyKey", "Int64.Type"),
            ("StatusName", "type text"),
            ("Units", "Int64.Type"),
            ("GrossRevenue", "Currency.Type"),
            ("DiscountAmount", "Currency.Type"),
            ("NetRevenue", "Currency.Type"),
            ("RevenueAfterRefund", "Currency.Type"),
            ("GrossProfit", "Currency.Type"),
            ("GrossProfitAfterRefund", "Currency.Type"),
            ("RefundAmount", "Currency.Type"),
            ("ReturnedUnits", "Int64.Type"),
            ("PromotionId", "Int64.Type"),
            ("Carrier", "type text"),
            ("ShippedDate", "type datetime"),
            ("PromisedDeliveryDate", "type datetime"),
            ("DeliveredDate", "type datetime"),
            ("DeliveryDays", "Int64.Type"),
            ("IsOnTime", "Int64.Type"),
        ],
        "hide_measures_source": True,
    },
    "FactOrderLines": {
        "file": "fact_order_lines.csv",
        "types": [
            ("OrderItemId", "Int64.Type"),
            ("OrderId", "Int64.Type"),
            ("OrderDateKey", "Int64.Type"),
            ("CustomerId", "Int64.Type"),
            ("ProductId", "Int64.Type"),
            ("Quantity", "Int64.Type"),
            ("UnitPrice", "Currency.Type"),
            ("UnitCost", "Currency.Type"),
            ("GrossRevenue", "Currency.Type"),
            ("DiscountAmount", "Currency.Type"),
            ("NetRevenue", "Currency.Type"),
            ("RevenueAfterRefund", "Currency.Type"),
            ("COGS", "Currency.Type"),
            ("GrossProfit", "Currency.Type"),
            ("GrossProfitAfterRefund", "Currency.Type"),
            ("ReturnedQuantity", "Int64.Type"),
            ("RefundAmount", "Currency.Type"),
            ("DiscountRate", "Percentage.Type"),
            ("IsValidOrder", "Int64.Type"),
            ("ChannelId", "Int64.Type"),
            ("PromotionId", "Int64.Type"),
            ("GeographyKey", "Int64.Type"),
        ],
        "hide_measures_source": True,
    },
    "FactReturns": {
        "file": "fact_returns.csv",
        "types": [
            ("ReturnItemId", "Int64.Type"),
            ("ReturnId", "Int64.Type"),
            ("OrderItemId", "Int64.Type"),
            ("OrderId", "Int64.Type"),
            ("ReturnDateKey", "Int64.Type"),
            ("ReturnDate", "type datetime"),
            ("OrderDateKey", "Int64.Type"),
            ("CustomerId", "Int64.Type"),
            ("ProductId", "Int64.Type"),
            ("ChannelId", "Int64.Type"),
            ("PromotionId", "Int64.Type"),
            ("GeographyKey", "Int64.Type"),
            ("ReturnReason", "type text"),
            ("ReturnStatus", "type text"),
            ("ReturnQuantity", "Int64.Type"),
            ("RefundAmount", "Currency.Type"),
            ("LineReturnRate", "Percentage.Type"),
        ],
        "hide_measures_source": True,
    },
    "FactReviews": {
        "file": "fact_reviews.csv",
        "types": [
            ("ReviewId", "Int64.Type"),
            ("ReviewDateKey", "Int64.Type"),
            ("ReviewDate", "type datetime"),
            ("CustomerId", "Int64.Type"),
            ("ProductId", "Int64.Type"),
            ("OrderItemId", "Int64.Type"),
            ("Rating", "Int64.Type"),
            ("ReviewTitle", "type text"),
            ("ReviewText", "type text"),
            ("IsVerifiedPurchase", "Int64.Type"),
            ("HelpfulVotes", "Int64.Type"),
            ("WasReturned", "Int64.Type"),
        ],
        "hide_measures_source": True,
        "hidden_columns": {"ReviewTitle", "ReviewText"},
    },
    "FactCampaignPerformance": {
        "file": "campaign_performance.csv",
        "types": [
            ("PromotionId", "Int64.Type"),
            ("PromotionCode", "type text"),
            ("PromotionName", "type text"),
            ("PromotionType", "type text"),
            ("DiscountValue", "Currency.Type"),
            ("MinimumOrderValue", "Currency.Type"),
            ("StartDate", "type datetime"),
            ("EndDate", "type datetime"),
            ("ChannelId", "Int64.Type"),
            ("Audience", "Int64.Type"),
            ("Clicks", "Int64.Type"),
            ("Conversions", "Int64.Type"),
            ("AttributedOrders", "Int64.Type"),
            ("AttributedRevenue", "Currency.Type"),
            ("AttributedRevenueAfterRefund", "Currency.Type"),
            ("AttributedGrossProfit", "Currency.Type"),
            ("DiscountCost", "Currency.Type"),
            ("ClickThroughRate", "Percentage.Type"),
            ("ClickToConversionRate", "Percentage.Type"),
            ("StartDateKey", "Int64.Type"),
            ("EndDateKey", "Int64.Type"),
        ],
        "hide_measures_source": True,
    },
    "FactCohortRetention": {
        "file": "cohort_retention.csv",
        "types": [
            ("CohortMonth", "type datetime"),
            ("MonthsSinceFirstOrder", "Int64.Type"),
            ("ActiveCustomers", "Int64.Type"),
            ("CohortSize", "Int64.Type"),
            ("RetentionRate", "Percentage.Type"),
        ],
    },
    "FactRfmSnapshot": {
        "file": "rfm_segments.csv",
        "types": [
            ("CustomerId", "Int64.Type"),
            ("LastOrderDate", "type datetime"),
            ("Frequency", "Int64.Type"),
            ("MonetaryValue", "Currency.Type"),
            ("SnapshotDate", "type datetime"),
            ("RecencyDays", "Int64.Type"),
            ("RScore", "Int64.Type"),
            ("FScore", "Int64.Type"),
            ("MScore", "Int64.Type"),
            ("RfmCode", "type text"),
            ("RfmSegment", "type text"),
            ("SnapshotDateKey", "Int64.Type"),
        ],
    },
    "ValidationAcquisition": {
        "file": "acquisition_performance.csv",
        "hidden_table": True,
        "types": [
            ("AcquisitionSource", "type text"),
            ("Customers", "Int64.Type"),
            ("Orders", "Int64.Type"),
            ("RevenueAfterRefund", "Currency.Type"),
            ("GrossProfit", "Currency.Type"),
            ("AverageOrderValue", "Currency.Type"),
            ("RepeatOrders", "Int64.Type"),
            ("AcquiredCustomers", "Int64.Type"),
            ("PurchaserConversionRate", "Percentage.Type"),
            ("RevenuePerPurchaser", "Currency.Type"),
            ("RepeatOrderRate", "Percentage.Type"),
        ],
    },
    "ValidationCategory": {
        "file": "category_performance.csv",
        "hidden_table": True,
        "types": [
            ("CategoryName", "type text"),
            ("Products", "Int64.Type"),
            ("Orders", "Int64.Type"),
            ("UnitsSold", "Int64.Type"),
            ("NetRevenue", "Currency.Type"),
            ("RevenueAfterRefund", "Currency.Type"),
            ("GrossProfit", "Currency.Type"),
            ("ReturnedUnits", "Int64.Type"),
            ("RefundAmount", "Currency.Type"),
            ("DiscountAmount", "Currency.Type"),
            ("GrossMarginRate", "Percentage.Type"),
            ("UnitReturnRate", "Percentage.Type"),
            ("RefundToRevenueRate", "Percentage.Type"),
        ],
    },
    "ValidationDelivery": {
        "file": "delivery_performance.csv",
        "hidden_table": True,
        "types": [
            ("Carrier", "type text"),
            ("Region", "type text"),
            ("DeliveredOrders", "Int64.Type"),
            ("AverageDeliveryDays", "type number"),
            ("MedianDeliveryDays", "type number"),
            ("OnTimeRate", "Percentage.Type"),
            ("LateOrders", "Int64.Type"),
        ],
    },
    "ValidationDiscount": {
        "file": "discount_effectiveness.csv",
        "hidden_table": True,
        "types": [
            ("MonthStart", "type datetime"),
            ("ChannelName", "type text"),
            ("PromotionGroup", "type text"),
            ("Orders", "Int64.Type"),
            ("AverageOrderValue", "Currency.Type"),
            ("RevenueAfterRefund", "Currency.Type"),
            ("GrossProfit", "Currency.Type"),
            ("DiscountCost", "Currency.Type"),
            ("GrossProfitPerOrder", "Currency.Type"),
        ],
    },
    "ValidationMonthly": {
        "file": "monthly_performance.csv",
        "hidden_table": True,
        "types": [
            ("MonthStart", "type datetime"),
            ("Orders", "Int64.Type"),
            ("ActiveCustomers", "Int64.Type"),
            ("RepeatOrders", "Int64.Type"),
            ("NetRevenue", "Currency.Type"),
            ("RevenueAfterRefund", "Currency.Type"),
            ("GrossProfit", "Currency.Type"),
            ("AverageOrderValue", "Currency.Type"),
            ("Discounts", "Currency.Type"),
            ("ReturnedUnits", "Int64.Type"),
            ("PreviousMonthRevenue", "Currency.Type"),
            ("PreviousYearRevenue", "Currency.Type"),
            ("RevenueMoMPct", "Percentage.Type"),
            ("RevenueYoYPct", "Percentage.Type"),
            ("Rolling3MonthRevenue", "Currency.Type"),
            ("Rolling12MonthRevenue", "Currency.Type"),
            ("RunningRevenue", "Currency.Type"),
            ("GrossMarginRate", "Percentage.Type"),
            ("RepeatOrderRate", "Percentage.Type"),
        ],
    },
    "ValidationPareto": {
        "file": "pareto_curve.csv",
        "hidden_table": True,
        "types": [
            ("CustomerId", "Int64.Type"),
            ("LifetimeRevenueAfterRefund", "Currency.Type"),
            ("CustomerRank", "Int64.Type"),
            ("CumulativeCustomerShare", "Percentage.Type"),
            ("CumulativeRevenueShare", "Percentage.Type"),
        ],
    },
    "ValidationProduct": {
        "file": "product_performance.csv",
        "hidden_table": True,
        "types": [
            ("ProductId", "Int64.Type"),
            ("SKU", "type text"),
            ("ProductName", "type text"),
            ("BrandName", "type text"),
            ("SubcategoryName", "type text"),
            ("CategoryName", "type text"),
            ("Orders", "Int64.Type"),
            ("UnitsSold", "Int64.Type"),
            ("GrossRevenue", "Currency.Type"),
            ("DiscountAmount", "Currency.Type"),
            ("NetRevenue", "Currency.Type"),
            ("RevenueAfterRefund", "Currency.Type"),
            ("GrossProfit", "Currency.Type"),
            ("ReturnedUnits", "Int64.Type"),
            ("RefundAmount", "Currency.Type"),
            ("Reviews", "Int64.Type"),
            ("AverageRating", "type number"),
            ("GrossMarginRate", "Percentage.Type"),
            ("UnitReturnRate", "Percentage.Type"),
            ("DiscountRate", "Percentage.Type"),
        ],
    },
    "ValidationRegionalChannel": {
        "file": "regional_channel_performance.csv",
        "hidden_table": True,
        "types": [
            ("Region", "type text"),
            ("ChannelName", "type text"),
            ("Orders", "Int64.Type"),
            ("Customers", "Int64.Type"),
            ("RevenueAfterRefund", "Currency.Type"),
            ("GrossProfit", "Currency.Type"),
            ("RepeatOrders", "Int64.Type"),
            ("GrossMarginRate", "Percentage.Type"),
            ("RepeatOrderRate", "Percentage.Type"),
        ],
    },
    "ValidationReviewReturn": {
        "file": "review_return_relationship.csv",
        "hidden_table": True,
        "types": [
            ("Rating", "Int64.Type"),
            ("Reviews", "Int64.Type"),
            ("ReturnedReviews", "Int64.Type"),
            ("ReturnRate", "Percentage.Type"),
        ],
    },
}

FK_COLUMNS = {
    "DateKey",
    "OrderDateKey",
    "ReturnDateKey",
    "ReviewDateKey",
    "StartDateKey",
    "EndDateKey",
    "SnapshotDateKey",
    "CustomerId",
    "ProductId",
    "ChannelId",
    "GeographyKey",
    "PromotionId",
    "OrderItemId",
    "ReturnItemId",
    "ReviewId",
}


def escape_m_string(value: str) -> str:
    return value.replace("\\", "\\\\")


def build_m_type_list(types: list[tuple[str, str]]) -> str:
    parts = []
    for name, pq_type in types:
        parts.append(f'{{"{name}", {pq_type}}}')
    return "{" + ", ".join(parts) + "}"


def build_partition_m(file_name: str, types: list[tuple[str, str]]) -> str:
    type_list = build_m_type_list(types)
    return (
        "let\n"
        f'    Source = Csv.Document(\n'
        f'        File.Contents(CsvRoot & "\\\\{file_name}"),\n'
        f'        [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]\n'
        f"    ),\n"
        f"    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),\n"
        f'    TypedColumns = Table.TransformColumnTypes(PromotedHeaders, {type_list}, "en-US")\n'
        f"in\n"
        f"    TypedColumns"
    )


def parse_measure_dictionary() -> dict[str, dict[str, str]]:
    text = DICTIONARY_PATH.read_text(encoding="utf-8")
    rows = re.findall(
        r"\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*`([^`]+)`\s*\|",
        text,
    )
    result: dict[str, dict[str, str]] = {}
    for folder, measure, description, fmt in rows:
        if measure.strip() == "Measure":
            continue
        result[measure.strip()] = {
            "displayFolder": folder.strip(),
            "description": description.strip(),
            "formatString": fmt.strip(),
        }
    return result


def parse_measures() -> list[tuple[str, str]]:
    text = MEASURES_PATH.read_text(encoding="utf-8")
    lines = text.splitlines()
    measures: list[tuple[str, str]] = []
    current_name: str | None = None
    current_lines: list[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("//"):
            continue
        if "=" in line and not line.startswith(" "):
            if current_name is not None:
                measures.append((current_name, "\n".join(current_lines).strip()))
            name, expr = line.split("=", 1)
            current_name = name.strip()
            current_lines = [expr.strip()]
            continue
        if current_name is not None:
            current_lines.append(line)
    if current_name is not None:
        measures.append((current_name, "\n".join(current_lines).strip()))
    return measures


def load_relationships() -> list[dict[str, str]]:
    relationships = []
    with RELATIONSHIPS_PATH.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            relationships.append(row)
    return relationships


def column_format(column_name: str, pq_type: str) -> str | None:
    if pq_type == "Currency.Type":
        return "$#,0.00;($#,0.00);-"
    if pq_type == "Percentage.Type":
        return "0.0%"
    if pq_type == "type number":
        return "0.0"
    return None


def build_column(
    table_name: str,
    column_name: str,
    pq_type: str,
    table_meta: dict[str, object],
) -> dict[str, object]:
    data_type = PQ_TO_TABULAR[pq_type]
    hidden_columns = set(table_meta.get("hidden_columns", set()))
    hide_source = bool(table_meta.get("hide_measures_source"))
    column: dict[str, object] = {
        "name": column_name,
        "dataType": data_type,
        "sourceColumn": column_name,
        "summarizeBy": "none",
    }
    fmt = column_format(column_name, pq_type)
    if fmt:
        column["formatString"] = fmt
    if column_name in FK_COLUMNS or column_name in hidden_columns:
        column["isHidden"] = True
    elif hide_source and pq_type in {"Currency.Type", "Percentage.Type", "type number"}:
        column["isHidden"] = True
    sort_columns = table_meta.get("sort_columns", {})
    if isinstance(sort_columns, dict) and column_name in sort_columns:
        column["sortByColumn"] = sort_columns[column_name]
    if table_name == "DimDate" and column_name == "FullDate":
        column["dataCategory"] = "PaddedDateTableDates"
    if table_name == "DimGeography" and column_name == "City":
        column["dataCategory"] = "City"
    if table_name == "DimGeography" and column_name == "StateProvince":
        column["dataCategory"] = "State"
    if table_name == "DimGeography" and column_name == "Region":
        column["dataCategory"] = "Region"
    if table_name == "DimGeography" and column_name == "CountryCode":
        column["dataCategory"] = "Country"
    return column


def build_table(table_name: str, table_meta: dict[str, object]) -> dict[str, object]:
    types: list[tuple[str, str]] = table_meta["types"]  # type: ignore[assignment]
    file_name: str = table_meta["file"]  # type: ignore[assignment]
    columns = [build_column(table_name, name, pq, table_meta) for name, pq in types]
    table: dict[str, object] = {
        "name": table_name,
        "columns": columns,
        "partitions": [
            {
                "name": table_name,
                "mode": "import",
                "source": {
                    "type": "m",
                    "expression": build_partition_m(file_name, types),
                },
            }
        ],
    }
    if table_meta.get("hidden_table"):
        table["isHidden"] = True
    if table_meta.get("date_table"):
        table["dataCategory"] = "Time"
        table["annotations"] = [
            {"name": "__PBI_TemplateDateTable", "value": "true"},
            {"name": "DefaultDetailRowsExpression", "value": "DimDate[FullDate]"},
        ]
    return table


def build_measures_table(
    measures: list[tuple[str, str]],
    dictionary: dict[str, dict[str, str]],
) -> dict[str, object]:
    measure_objects = []
    for name, expression in measures:
        meta = dictionary.get(name, {})
        measure: dict[str, object] = {
            "name": name,
            "expression": expression,
        }
        if meta.get("formatString"):
            measure["formatString"] = meta["formatString"]
        if meta.get("displayFolder"):
            measure["displayFolder"] = meta["displayFolder"]
        if meta.get("description"):
            measure["description"] = meta["description"]
        measure_objects.append(measure)

    return {
        "name": "_Measures",
        "isHidden": False,
        "columns": [
            {
                "name": "Placeholder",
                "dataType": "int64",
                "sourceColumn": "Placeholder",
                "isHidden": True,
            }
        ],
        "partitions": [
            {
                "name": "_Measures",
                "mode": "import",
                "source": {"type": "calculated", "expression": 'ROW("Placeholder", 1)'},
            }
        ],
        "measures": measure_objects,
    }


def build_model(csv_root: Path) -> dict[str, object]:
    csv_root_text = escape_m_string(str(csv_root.resolve()))
    measures = parse_measures()
    dictionary = parse_measure_dictionary()
    tables = [build_table(name, meta) for name, meta in TABLES.items()]
    tables.append(build_measures_table(measures, dictionary))

    relationships = []
    for rel in load_relationships():
        relationships.append(
            {
                "name": rel["RelationshipName"],
                "fromTable": rel["ToTable"],
                "fromColumn": rel["ToColumn"],
                "toTable": rel["FromTable"],
                "toColumn": rel["FromColumn"],
                "crossFilteringBehavior": "oneDirection",
            }
        )

    query_order = ["CsvRoot", "fnLoadCsv"] + list(TABLES.keys())
    return {
        "name": "Northstar Commerce Analytics",
        "compatibilityLevel": 1567,
        "model": {
            "culture": "en-US",
            "defaultPowerBIDataSourceVersion": "powerBI_V3",
            "sourceQueryCulture": "en-US",
            "dataAccessOptions": {
                "legacyRedirects": True,
                "returnErrorValuesAsNull": True,
            },
            "annotations": [
                {"name": "PBI_QueryOrder", "value": json.dumps(query_order)},
                {"name": "__PBI_TimeIntelligenceEnabled", "value": "0"},
            ],
            "expressions": [
                {
                    "name": "CsvRoot",
                    "kind": "m",
                    "expression": f'"{csv_root_text}" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]',
                },
                {
                    "name": "fnLoadCsv",
                    "kind": "m",
                    "expression": (
                        "(fileName as text, columnTypes as list) as table =>\n"
                        "let\n"
                        '    Source = Csv.Document(\n'
                        '        File.Contents(CsvRoot & "\\\\" & fileName),\n'
                        '        [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]\n'
                        "    ),\n"
                        "    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),\n"
                        '    TypedColumns = Table.TransformColumnTypes(PromotedHeaders, columnTypes, "en-US")\n'
                        "in\n"
                        "    TypedColumns"
                    ),
                },
            ],
            "tables": tables,
            "relationships": relationships,
        },
    }


def write_tabular_editor_script(output_dir: Path) -> None:
    script = """// Run this script in Tabular Editor against a blank Power BI Desktop instance,
// or open generated/model.bim and deploy to Power BI Desktop.

Model.DatabaseCompatibilityLevel = 1567;
"""
    (output_dir / "deploy_notes.csx").write_text(script, encoding="utf-8")


def write_turkish_guide(output_dir: Path, csv_root: Path) -> None:
    guide = f"""# Northstar Power BI Otomatik Kurulum

Bu klasör, Power BI modelini sizin yerinize otomatik oluşturur.

## Oluşturulan dosyalar

- `model.bim` — 22 tablo, 24 ilişki, 87 DAX ölçüsü
- `CsvRoot.txt` — CSV klasör yolu

## Yöntem A — Tabular Editor (önerilen)

1. [Tabular Editor](https://tabulareditor.com/) indirin (ücretsiz sürüm yeterli).
2. Power BI Desktop'u açın → boş rapor oluşturun.
3. Tabular Editor'de **File → Open → From DB** → çalışan Power BI Desktop örneğine bağlanın.
4. **File → Open → From File** ile `model.bim` dosyasını açın (mevcut modelin üzerine yazar).
5. **Model → Deploy** ile Power BI Desktop'a aktarın.
6. Power BI'da **Transform data** → `CsvRoot` parametresinin değerini kontrol edin:
   `{csv_root}`
7. **Close & Apply** → veri yenilensin.
8. **View → Themes → Browse for themes** → `../theme.json`
9. İlk sayfayı oluşturmaya başlayın (Executive Overview).

## Yöntem B — pbi-tools ile PBIT

PowerShell'de proje kökünden:

```powershell
.\\scripts\\Build-NorthstarPowerBI.ps1
```

Bu komut `Northstar Commerce Analytics.pbit` dosyası üretmeye çalışır.
PBIT dosyasını Power BI Desktop ile açın, `CsvRoot` yolunu onaylayın ve yenileyin.

## Not

Görsel/dashboard tasarımı (6 sayfa) Power BI Desktop'ta elle yapılmalıdır.
Model katmanı (veri + ilişki + ölçüler) bu otomasyonla hazır gelir.

Detaylı sayfa tasarımı için: `../BUILD_POWERBI.md`
"""
    (output_dir / "KURULUM_TR.md").write_text(guide, encoding="utf-8")


def main() -> int:
    csv_root = DEFAULT_CSV_ROOT
    if len(sys.argv) > 1:
        csv_root = Path(sys.argv[1]).expanduser().resolve()

    if not csv_root.exists():
        print(f"CSV klasörü bulunamadı: {csv_root}", file=sys.stderr)
        return 1

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    model = build_model(csv_root)
    model_path = OUTPUT_DIR / "model.bim"
    model_path.write_text(json.dumps(model, indent=2), encoding="utf-8")
    (OUTPUT_DIR / "CsvRoot.txt").write_text(str(csv_root), encoding="utf-8")
    write_tabular_editor_script(OUTPUT_DIR)
    write_turkish_guide(OUTPUT_DIR, csv_root)

    measure_count = len(parse_measures())
    rel_count = len(load_relationships())
    print(f"Model oluşturuldu: {model_path}")
    print(f"Tablolar: {len(TABLES) + 1}, İlişkiler: {rel_count}, Ölçüler: {measure_count}")
    print(f"CSV yolu: {csv_root}")
    print(f"Kurulum rehberi: {OUTPUT_DIR / 'KURULUM_TR.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
