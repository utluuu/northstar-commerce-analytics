"""End-to-end orchestration for validation, analysis, plots, reports, and exports."""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

from .analysis import build_analysis_tables, executive_metrics, generate_insights
from .config import AnalyticsConfig
from .io import export_tables, load_generated_data
from .model import (
    build_campaign_performance, build_cohort_retention, build_customer_metrics,
    build_monthly_performance, build_order_lines, build_order_summary,
    build_product_performance, build_returns, build_review_analytics, build_rfm,
)
from .reporting import write_executive_summary, write_insights, write_quality_report, write_run_manifest
from .validation import validate_metric_reconciliation, validate_sources

LOGGER = logging.getLogger(__name__)


def _configure_logging(log_file: Path) -> None:
    log_file.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[logging.FileHandler(log_file, mode="w", encoding="utf-8"), logging.StreamHandler()],
        force=True,
    )


def _product_dimension(raw: dict[str, pd.DataFrame]) -> pd.DataFrame:
    categories = raw["categories"]
    child = categories[["CategoryId", "CategoryName", "ParentCategoryId"]].rename(columns={"CategoryName": "SubcategoryName"})
    parent = categories[["CategoryId", "CategoryName"]].rename(columns={"CategoryId": "ParentCategoryId"})
    return raw["products"].merge(child, on="CategoryId", validate="many_to_one").merge(parent, on="ParentCategoryId", how="left", validate="many_to_one")


def _select_exports(
    raw: dict[str, pd.DataFrame],
    orders: pd.DataFrame,
    lines: pd.DataFrame,
    customers: pd.DataFrame,
    products: pd.DataFrame,
    returns: pd.DataFrame,
    reviews: pd.DataFrame,
    campaigns: pd.DataFrame,
    monthly: pd.DataFrame,
    cohort: pd.DataFrame,
    rfm: pd.DataFrame,
    analyses: dict[str, pd.DataFrame],
) -> dict[str, pd.DataFrame]:
    geography = (
        orders[["City", "StateProvince", "Region", "CountryCode"]]
        .drop_duplicates()
        .sort_values(["CountryCode", "Region", "StateProvince", "City"])
        .reset_index(drop=True)
    )
    geography.insert(0, "GeographyKey", np.arange(1, len(geography) + 1, dtype="int32"))
    geo_columns = ["City", "StateProvince", "Region", "CountryCode"]
    orders = orders.merge(geography, on=geo_columns, validate="many_to_one")
    lines = lines.merge(geography, on=geo_columns, validate="many_to_one")
    address_geography = raw["addresses"][["AddressId", *geo_columns]].merge(
        geography, on=geo_columns, validate="many_to_one"
    )[["AddressId", "GeographyKey"]]
    returns = returns.merge(
        address_geography, left_on="ShippingAddressId", right_on="AddressId", validate="many_to_one"
    )

    order_columns = [
        "OrderId", "OrderDateKey", "OrderDate", "CustomerId", "CustomerOrderNumber", "IsRepeatPurchase",
        "ChannelId", "GeographyKey", "StatusName", "Units", "GrossRevenue",
        "DiscountAmount", "NetRevenue", "RevenueAfterRefund", "GrossProfit", "GrossProfitAfterRefund",
        "RefundAmount", "ReturnedUnits", "PromotionId", "Carrier", "ShippedDate", "PromisedDeliveryDate",
        "DeliveredDate", "DeliveryDays", "IsOnTime",
    ]
    line_columns = [
        "OrderItemId", "OrderId", "OrderDateKey", "CustomerId", "ProductId", "Quantity", "UnitPrice", "UnitCost",
        "GrossRevenue", "DiscountAmount", "NetRevenue", "RevenueAfterRefund", "COGS", "GrossProfit",
        "GrossProfitAfterRefund", "ReturnedQuantity", "RefundAmount", "DiscountRate", "IsValidOrder",
        "ChannelId", "PromotionId", "GeographyKey",
    ]
    customer_columns = [
        "CustomerId", "AcquisitionDate", "AcquisitionSource", "SegmentName", "IsActive", "FirstOrderDate", "LastOrderDate",
        "LifetimeOrders", "LifetimeRevenue", "LifetimeRevenueAfterRefund", "LifetimeGrossProfit", "AverageOrderValue",
        "AvgDaysBetweenOrders", "RecencyDays", "IsRepeatCustomer", "Projected12MonthRevenue", "LifecycleStatus",
    ]
    return_columns = [
        "ReturnItemId", "ReturnId", "OrderItemId", "OrderId", "ReturnDateKey", "ReturnDate", "OrderDateKey",
        "CustomerId", "ProductId", "ChannelId", "PromotionId", "GeographyKey", "ReturnReason", "ReturnStatus",
        "ReturnQuantity", "RefundAmount", "LineReturnRate",
    ]
    review_columns = [
        "ReviewId", "ReviewDateKey", "ReviewDate", "CustomerId", "ProductId", "OrderItemId", "Rating",
        "ReviewTitle", "ReviewText", "IsVerifiedPurchase", "HelpfulVotes", "WasReturned",
    ]
    campaign_export = campaigns.copy()
    campaign_export["StartDateKey"] = campaign_export["StartDate"].dt.strftime("%Y%m%d").astype("int32")
    campaign_export["EndDateKey"] = campaign_export["EndDate"].dt.strftime("%Y%m%d").astype("int32")
    rfm_export = rfm.copy()
    rfm_export["SnapshotDateKey"] = rfm_export["SnapshotDate"].dt.strftime("%Y%m%d").astype("int32")

    return {
        "fact_orders": orders[order_columns].sort_values("OrderId"),
        "fact_order_lines": lines[line_columns].sort_values("OrderItemId"),
        "dim_customers": customers[customer_columns].sort_values("CustomerId"),
        "dim_products": _product_dimension(raw).sort_values("ProductId"),
        "dim_channels": raw["sales_channels"].sort_values("ChannelId"),
        "dim_promotions": raw["promotions"].sort_values("PromotionId"),
        "dim_geography": geography,
        "dim_date": raw["date_dimension"].sort_values("DateKey"),
        "fact_returns": returns[return_columns].sort_values(["ReturnId", "OrderItemId"]),
        "fact_reviews": reviews[review_columns].sort_values("ReviewId"),
        "product_performance": products.sort_values("ProductId"),
        "campaign_performance": campaign_export.sort_values("PromotionId"),
        "monthly_performance": monthly.sort_values("MonthStart"),
        "cohort_retention": cohort.sort_values(["CohortMonth", "MonthsSinceFirstOrder"]),
        "rfm_segments": rfm_export.sort_values("CustomerId"),
        "acquisition_performance": analyses["acquisition_performance"].sort_values("AcquisitionSource"),
        "category_performance": analyses["category_performance"].sort_values("CategoryName"),
        "delivery_performance": analyses["delivery_performance"].sort_values(["Carrier", "Region"]),
        "discount_effectiveness": analyses["discount_effectiveness"].sort_values(["MonthStart", "ChannelName", "PromotionGroup"]),
        "regional_channel_performance": analyses["regional_channel_performance"].sort_values(["Region", "ChannelName"]),
        "pareto_curve": analyses["pareto_curve"],
        "review_return_relationship": analyses["review_return_relationship"].sort_values("Rating"),
    }


def run_pipeline(config: AnalyticsConfig, skip_plots: bool = False) -> None:
    """Execute the complete deterministic EDA workflow."""
    _configure_logging(config.log_file)
    np.random.seed(config.random_seed)
    LOGGER.info("Starting Northstar Commerce analytics pipeline")
    try:
        raw = load_generated_data(config.source_directory, config.chunk_size)
        quality = validate_sources(raw)
        LOGGER.info("Source data quality checks passed")

        lines = build_order_lines(raw)
        orders = build_order_summary(raw, lines)
        customers = build_customer_metrics(raw, orders)
        monthly = build_monthly_performance(orders)
        cohort = build_cohort_retention(orders)
        rfm = build_rfm(orders, config.rfm_snapshot_date)
        products = build_product_performance(raw, lines)
        returns = build_returns(raw)
        reviews = build_review_analytics(raw)
        campaigns = build_campaign_performance(raw, orders)
        validate_metric_reconciliation(quality, lines, orders)
        LOGGER.info("Metric reconciliation checks passed")

        analyses = build_analysis_tables(raw, orders, customers, monthly, cohort, rfm, products, returns, reviews, campaigns)
        metrics = executive_metrics(orders, customers, monthly)
        insights = generate_insights(metrics, monthly, analyses)

        exports = _select_exports(raw, orders, lines, customers, products, returns, reviews, campaigns, monthly, cohort, rfm, analyses)
        config.export_directory.mkdir(parents=True, exist_ok=True)
        for stale_file in config.export_directory.glob("*.csv"):
            stale_file.unlink()
        export_counts = export_tables(exports, config.export_directory)

        if skip_plots:
            figures = sorted(path.name for path in config.figure_directory.glob("*.png"))
        else:
            from .plots import render_all

            figures = render_all(
                monthly, products, analyses, config.figure_directory, config.figure_dpi,
                config.top_products, config.cohort_months,
            )
        config.report_directory.mkdir(parents=True, exist_ok=True)
        write_quality_report(quality, config.report_directory)
        write_insights(insights, config.report_directory)
        write_run_manifest(config, export_counts, figures, config.report_directory)
        summary = write_executive_summary(metrics, insights, quality, export_counts, figures, config.report_directory)
        LOGGER.info("Pipeline complete. Executive summary: %s", summary)
    except Exception:
        LOGGER.exception("Analytics pipeline failed")
        raise
