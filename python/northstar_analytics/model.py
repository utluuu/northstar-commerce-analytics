"""Build analytics-ready tables using the same metric semantics as SQL Server."""
from __future__ import annotations

import numpy as np
import pandas as pd


def _category_lookup(categories: pd.DataFrame) -> pd.DataFrame:
    children = categories[["CategoryId", "CategoryName", "ParentCategoryId"]].rename(columns={"CategoryName": "SubcategoryName"})
    parents = categories[["CategoryId", "CategoryName"]].rename(columns={"CategoryId": "ParentCategoryId"})
    return children.merge(parents, on="ParentCategoryId", how="left", validate="many_to_one")


def _return_line_totals(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    returns = data["returns"].query("ReturnStatus != 'Rejected'")[["ReturnId", "OrderId", "ReturnStatus"]]
    detail = data["return_items"].merge(returns, on="ReturnId", how="inner", validate="many_to_one")
    return detail.groupby("OrderItemId", as_index=False).agg(
        ReturnedQuantity=("ReturnQuantity", "sum"), RefundAmount=("RefundAmount", "sum")
    )


def build_order_lines(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Create the order-line fact with booked and after-refund economics."""
    lines = data["order_items"].copy()
    orders = data["orders"].merge(data["order_statuses"], on="StatusId", validate="many_to_one")
    orders = orders.merge(data["sales_channels"], on="ChannelId", validate="many_to_one")
    orders = orders.merge(data["customers"][["CustomerId", "AcquisitionSource", "SegmentId"]], on="CustomerId", validate="many_to_one")
    orders = orders.merge(data["customer_segments"][["SegmentId", "SegmentName"]], on="SegmentId", validate="many_to_one")
    orders = orders.merge(
        data["addresses"][["AddressId", "City", "StateProvince", "Region", "CountryCode"]],
        left_on="ShippingAddressId", right_on="AddressId", validate="many_to_one",
    )
    lines = lines.merge(orders, on="OrderId", validate="many_to_one")

    products = data["products"].merge(_category_lookup(data["categories"]), on="CategoryId", validate="many_to_one")
    lines = lines.merge(products, on="ProductId", validate="many_to_one", suffixes=("", "_product"))
    lines = lines.merge(_return_line_totals(data), on="OrderItemId", how="left", validate="one_to_one")
    lines[["ReturnedQuantity", "RefundAmount"]] = lines[["ReturnedQuantity", "RefundAmount"]].fillna(0)
    lines = lines.merge(
        data["promotions"][["PromotionId", "PromotionName"]], on="PromotionId", how="left", validate="many_to_one"
    )

    lines["OrderDateTime"] = lines["OrderDate"]
    lines["OrderDateKey"] = lines["OrderDate"].dt.strftime("%Y%m%d").astype("int32")
    lines["GrossRevenue"] = lines["Quantity"] * lines["UnitPrice"]
    valid = lines["StatusName"].ne("Cancelled")
    lines["IsValidOrder"] = valid.astype("int8")
    lines["NetRevenue"] = np.where(valid, lines["GrossRevenue"] - lines["DiscountAmount"], 0.0)
    lines["COGS"] = np.where(valid, lines["Quantity"] * lines["UnitCost"], 0.0)
    lines["GrossProfit"] = lines["NetRevenue"] - lines["COGS"]
    lines["RefundAmount"] = np.where(valid, lines["RefundAmount"], 0.0)
    lines["RevenueAfterRefund"] = lines["NetRevenue"] - lines["RefundAmount"]
    lines["GrossProfitAfterRefund"] = lines["GrossProfit"] - lines["RefundAmount"]
    lines["DiscountRate"] = np.divide(
        lines["DiscountAmount"], lines["GrossRevenue"],
        out=np.zeros(len(lines), dtype=float), where=lines["GrossRevenue"].ne(0),
    )
    return lines


def build_order_summary(data: dict[str, pd.DataFrame], lines: pd.DataFrame) -> pd.DataFrame:
    """Create the one-row-per-order fact and valid customer order sequence."""
    totals = lines.groupby("OrderId", as_index=False).agg(
        Units=("Quantity", "sum"), GrossRevenue=("GrossRevenue", "sum"),
        DiscountAmount=("DiscountAmount", "sum"), NetRevenue=("NetRevenue", "sum"),
        RevenueAfterRefund=("RevenueAfterRefund", "sum"), GrossProfit=("GrossProfit", "sum"),
        GrossProfitAfterRefund=("GrossProfitAfterRefund", "sum"), ReturnedUnits=("ReturnedQuantity", "sum"),
        RefundAmount=("RefundAmount", "sum"), COGS=("COGS", "sum"),
    )
    orders = data["orders"].merge(totals, on="OrderId", validate="one_to_one")
    orders = orders.merge(data["order_statuses"], on="StatusId", validate="many_to_one")
    orders = orders.merge(data["sales_channels"], on="ChannelId", validate="many_to_one")
    orders = orders.merge(data["customers"][["CustomerId", "SegmentId"]], on="CustomerId", validate="many_to_one")
    orders = orders.merge(data["customer_segments"][["SegmentId", "SegmentName"]], on="SegmentId", validate="many_to_one")
    orders = orders.merge(
        data["addresses"][["AddressId", "City", "StateProvince", "Region", "CountryCode"]],
        left_on="ShippingAddressId", right_on="AddressId", validate="many_to_one",
    )
    orders = orders.merge(data["promotions"][["PromotionId", "PromotionName"]], on="PromotionId", how="left", validate="many_to_one")
    orders = orders.merge(data["shipments"], on="OrderId", how="left", validate="one_to_one")
    orders["OrderDateTime"] = orders["OrderDate"]
    orders["OrderDateKey"] = orders["OrderDate"].dt.strftime("%Y%m%d").astype("int32")
    orders = orders.sort_values(["CustomerId", "OrderDateTime", "OrderId"]).reset_index(drop=True)
    valid = orders["StatusName"].ne("Cancelled").astype("int8")
    orders["CustomerOrderNumber"] = valid.groupby(orders["CustomerId"]).cumsum()
    orders["IsRepeatPurchase"] = ((valid == 1) & orders["CustomerOrderNumber"].gt(1)).astype("int8")
    orders["DeliveryDays"] = (orders["DeliveredDate"].dt.normalize() - orders["OrderDate"].dt.normalize()).dt.days
    orders["IsOnTime"] = np.where(
        orders["DeliveredDate"].isna(), np.nan,
        (orders["DeliveredDate"].dt.normalize() <= orders["PromisedDeliveryDate"].dt.normalize()).astype(float),
    )
    return orders


def build_customer_metrics(data: dict[str, pd.DataFrame], orders: pd.DataFrame) -> pd.DataFrame:
    """Build historical customer value, purchase cadence, and explainable churn indicators."""
    valid = orders.query("StatusName != 'Cancelled'").sort_values(["CustomerId", "OrderDateTime", "OrderId"]).copy()
    valid["PreviousOrderDate"] = valid.groupby("CustomerId")["OrderDate"].shift()
    valid["GapDays"] = (valid["OrderDate"].dt.normalize() - valid["PreviousOrderDate"].dt.normalize()).dt.days
    metrics = valid.groupby("CustomerId", as_index=False).agg(
        FirstOrderDate=("OrderDate", "min"), LastOrderDate=("OrderDate", "max"),
        LifetimeOrders=("OrderId", "count"), LifetimeRevenue=("NetRevenue", "sum"),
        LifetimeRevenueAfterRefund=("RevenueAfterRefund", "sum"),
        LifetimeGrossProfit=("GrossProfit", "sum"), AverageOrderValue=("NetRevenue", "mean"),
        AvgDaysBetweenOrders=("GapDays", "mean"), ReturnedUnits=("ReturnedUnits", "sum"),
    )
    customers = data["customers"].merge(data["customer_segments"][["SegmentId", "SegmentName"]], on="SegmentId", validate="many_to_one")
    result = customers.merge(metrics, on="CustomerId", how="left", validate="one_to_one")
    numeric = ["LifetimeOrders", "LifetimeRevenue", "LifetimeRevenueAfterRefund", "LifetimeGrossProfit", "AverageOrderValue", "ReturnedUnits"]
    result[numeric] = result[numeric].fillna(0)
    as_of = orders["OrderDate"].max().normalize() + pd.Timedelta(days=1)
    result["AsOfDate"] = as_of
    result["RecencyDays"] = (as_of - result["LastOrderDate"].dt.normalize()).dt.days
    result["IsRepeatCustomer"] = result["LifetimeOrders"].ge(2).astype("int8")
    observed_days = (as_of - result["AcquisitionDate"].dt.normalize()).dt.days.clip(lower=90)
    result["Projected12MonthRevenue"] = result["LifetimeRevenueAfterRefund"] / (observed_days / 365.25)
    avg_gap = result["AvgDaysBetweenOrders"].fillna(45)
    high_threshold = np.maximum(2 * avg_gap, 90)
    risk_threshold = np.maximum(1.5 * avg_gap, 60)
    result["LifecycleStatus"] = np.select(
        [
            result["LifetimeOrders"].eq(0),
            result["LifetimeOrders"].eq(1) & result["RecencyDays"].gt(90),
            result["LifetimeOrders"].ge(2) & result["RecencyDays"].gt(high_threshold),
            result["LifetimeOrders"].ge(2) & result["RecencyDays"].gt(risk_threshold),
        ],
        ["Prospect", "One-Time Lapsed", "High Risk", "At Risk"], default="Active",
    )
    return result


def build_monthly_performance(orders: pd.DataFrame) -> pd.DataFrame:
    """Build complete monthly KPI, growth, rolling, and running metrics."""
    valid = orders.query("StatusName != 'Cancelled'").copy()
    valid["MonthStart"] = valid["OrderDate"].dt.to_period("M").dt.to_timestamp()
    monthly = valid.groupby("MonthStart", as_index=True).agg(
        Orders=("OrderId", "count"), ActiveCustomers=("CustomerId", "nunique"),
        RepeatOrders=("IsRepeatPurchase", "sum"), NetRevenue=("NetRevenue", "sum"),
        RevenueAfterRefund=("RevenueAfterRefund", "sum"), GrossProfit=("GrossProfit", "sum"),
        AverageOrderValue=("NetRevenue", "mean"), Discounts=("DiscountAmount", "sum"),
        ReturnedUnits=("ReturnedUnits", "sum"),
    )
    full_range = pd.date_range(monthly.index.min(), monthly.index.max(), freq="MS")
    monthly = monthly.reindex(full_range, fill_value=0).rename_axis("MonthStart").reset_index()
    monthly["PreviousMonthRevenue"] = monthly["NetRevenue"].shift(1)
    monthly["PreviousYearRevenue"] = monthly["NetRevenue"].shift(12)
    monthly["RevenueMoMPct"] = monthly["NetRevenue"].div(monthly["PreviousMonthRevenue"].replace(0, np.nan)).sub(1)
    monthly["RevenueYoYPct"] = monthly["NetRevenue"].div(monthly["PreviousYearRevenue"].replace(0, np.nan)).sub(1)
    monthly["Rolling3MonthRevenue"] = monthly["NetRevenue"].rolling(3, min_periods=1).mean()
    monthly["Rolling12MonthRevenue"] = monthly["NetRevenue"].rolling(12, min_periods=1).mean()
    monthly["RunningRevenue"] = monthly["NetRevenue"].cumsum()
    monthly["GrossMarginRate"] = monthly["GrossProfit"].div(monthly["NetRevenue"].replace(0, np.nan))
    monthly["RepeatOrderRate"] = monthly["RepeatOrders"].div(monthly["Orders"].replace(0, np.nan))
    return monthly


def build_cohort_retention(orders: pd.DataFrame) -> pd.DataFrame:
    """Calculate monthly first-order cohorts and active-customer retention."""
    activity = orders.query("StatusName != 'Cancelled'")[["CustomerId", "OrderDate"]].copy()
    activity["ActivityMonth"] = activity["OrderDate"].dt.to_period("M").dt.to_timestamp()
    activity = activity.drop_duplicates(["CustomerId", "ActivityMonth"])
    activity["CohortMonth"] = activity.groupby("CustomerId")["ActivityMonth"].transform("min")
    activity["MonthsSinceFirstOrder"] = (
        (activity["ActivityMonth"].dt.year - activity["CohortMonth"].dt.year) * 12
        + activity["ActivityMonth"].dt.month - activity["CohortMonth"].dt.month
    )
    cohort = activity.groupby(["CohortMonth", "MonthsSinceFirstOrder"], as_index=False).agg(ActiveCustomers=("CustomerId", "nunique"))
    sizes = cohort.query("MonthsSinceFirstOrder == 0")[["CohortMonth", "ActiveCustomers"]].rename(columns={"ActiveCustomers": "CohortSize"})
    cohort = cohort.merge(sizes, on="CohortMonth", validate="many_to_one")
    cohort["RetentionRate"] = cohort["ActiveCustomers"] / cohort["CohortSize"]
    return cohort


def build_rfm(orders: pd.DataFrame, snapshot_date: str) -> pd.DataFrame:
    """Create deterministic quintile RFM scores and business segments."""
    snapshot = pd.Timestamp(snapshot_date)
    valid = orders[(orders["StatusName"] != "Cancelled") & (orders["OrderDate"] < snapshot + pd.Timedelta(days=1))]
    rfm = valid.groupby("CustomerId", as_index=False).agg(
        LastOrderDate=("OrderDate", "max"), Frequency=("OrderId", "count"), MonetaryValue=("RevenueAfterRefund", "sum")
    )
    rfm["SnapshotDate"] = snapshot
    rfm["RecencyDays"] = (snapshot - rfm["LastOrderDate"].dt.normalize()).dt.days
    count = len(rfm)
    rfm["RScore"] = 6 - np.ceil(rfm["RecencyDays"].rank(method="first") * 5 / count).astype("int8")
    rfm["FScore"] = np.ceil(rfm["Frequency"].rank(method="first") * 5 / count).astype("int8")
    rfm["MScore"] = np.ceil(rfm["MonetaryValue"].rank(method="first") * 5 / count).astype("int8")
    rfm["RfmCode"] = rfm[["RScore", "FScore", "MScore"]].astype(str).agg("".join, axis=1)
    rfm["RfmSegment"] = np.select(
        [
            rfm["RScore"].ge(4) & rfm["FScore"].ge(4) & rfm["MScore"].ge(4),
            rfm["RScore"].ge(3) & rfm["FScore"].ge(4),
            rfm["RScore"].eq(5) & rfm["FScore"].le(2),
            rfm["RScore"].ge(4) & rfm["FScore"].between(2, 3),
            rfm["RScore"].le(2) & rfm["FScore"].ge(3),
            rfm["RScore"].le(2) & rfm["FScore"].le(2),
        ],
        ["Champions", "Loyal Customers", "New Customers", "Potential Loyalists", "At Risk", "Hibernating"],
        default="Needs Attention",
    )
    return rfm


def build_product_performance(data: dict[str, pd.DataFrame], lines: pd.DataFrame) -> pd.DataFrame:
    """Aggregate product revenue, margin, refunds, returns, and reviews."""
    valid = lines.query("StatusName != 'Cancelled'")
    performance = valid.groupby("ProductId", as_index=False).agg(
        SKU=("SKU", "first"), ProductName=("ProductName", "first"), BrandName=("BrandName", "first"),
        SubcategoryName=("SubcategoryName", "first"), CategoryName=("CategoryName", "first"),
        Orders=("OrderId", "nunique"), UnitsSold=("Quantity", "sum"), GrossRevenue=("GrossRevenue", "sum"),
        DiscountAmount=("DiscountAmount", "sum"), NetRevenue=("NetRevenue", "sum"),
        RevenueAfterRefund=("RevenueAfterRefund", "sum"), GrossProfit=("GrossProfit", "sum"),
        ReturnedUnits=("ReturnedQuantity", "sum"), RefundAmount=("RefundAmount", "sum"),
    )
    reviews = data["product_reviews"].groupby("ProductId", as_index=False).agg(
        Reviews=("ReviewId", "count"), AverageRating=("Rating", "mean")
    )
    performance = performance.merge(reviews, on="ProductId", how="left", validate="one_to_one")
    performance[["Reviews", "AverageRating"]] = performance[["Reviews", "AverageRating"]].fillna(0)
    performance["GrossMarginRate"] = performance["GrossProfit"] / performance["NetRevenue"].replace(0, np.nan)
    performance["UnitReturnRate"] = performance["ReturnedUnits"] / performance["UnitsSold"].replace(0, np.nan)
    performance["DiscountRate"] = performance["DiscountAmount"] / performance["GrossRevenue"].replace(0, np.nan)
    return performance


def build_returns(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Create a clean return-line fact enriched with conformed dimension keys."""
    returns = data["returns"].merge(data["return_items"], on="ReturnId", validate="one_to_many")
    returns = returns.merge(
        data["order_items"][["OrderItemId", "OrderId", "ProductId", "Quantity"]],
        on=["OrderItemId", "OrderId"], validate="many_to_one",
    )
    returns = returns.merge(
        data["orders"][["OrderId", "CustomerId", "OrderDate", "ChannelId", "PromotionId", "ShippingAddressId"]],
        on="OrderId", validate="many_to_one",
    )
    returns["ReturnDateKey"] = returns["ReturnDate"].dt.strftime("%Y%m%d").astype("int32")
    returns["OrderDateKey"] = returns["OrderDate"].dt.strftime("%Y%m%d").astype("int32")
    returns["LineReturnRate"] = returns["ReturnQuantity"] / returns["Quantity"].replace(0, np.nan)
    return returns


def build_review_analytics(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Create a review fact with event-date keys and observed return behavior."""
    reviews = data["product_reviews"].copy()
    returned_items = set(data["return_items"].loc[
        data["return_items"]["ReturnId"].isin(data["returns"].query("ReturnStatus != 'Rejected'")["ReturnId"]), "OrderItemId"
    ])
    reviews["WasReturned"] = reviews["OrderItemId"].isin(returned_items).astype("int8")
    reviews["ReviewDateKey"] = reviews["ReviewDate"].dt.strftime("%Y%m%d").astype("int32")
    return reviews


def build_campaign_performance(data: dict[str, pd.DataFrame], orders: pd.DataFrame) -> pd.DataFrame:
    """Build direct-attribution campaign funnel and order economics."""
    interactions = data["campaign_interactions"]
    audience = interactions[interactions["InteractionType"].isin(["Sent", "Impression"])].groupby("PromotionId")["CustomerId"].nunique()
    clicks = interactions["InteractionType"].eq("Click").groupby(interactions["PromotionId"]).sum()
    conversions = interactions["InteractionType"].eq("Conversion").groupby(interactions["PromotionId"]).sum()
    funnel = pd.concat([audience.rename("Audience"), clicks.rename("Clicks"), conversions.rename("Conversions")], axis=1).fillna(0).reset_index()
    attributed = orders[(orders["StatusName"] != "Cancelled") & orders["PromotionId"].notna()].groupby("PromotionId", as_index=False).agg(
        AttributedOrders=("OrderId", "count"), AttributedRevenue=("NetRevenue", "sum"),
        AttributedRevenueAfterRefund=("RevenueAfterRefund", "sum"), AttributedGrossProfit=("GrossProfit", "sum"),
        DiscountCost=("DiscountAmount", "sum"),
    )
    result = data["promotions"].merge(funnel, on="PromotionId", how="left", validate="one_to_one")
    result = result.merge(attributed, on="PromotionId", how="left", validate="one_to_one")
    numeric = ["Audience", "Clicks", "Conversions", "AttributedOrders", "AttributedRevenue", "AttributedRevenueAfterRefund", "AttributedGrossProfit", "DiscountCost"]
    result[numeric] = result[numeric].fillna(0)
    result["ClickThroughRate"] = result["Clicks"] / result["Audience"].replace(0, np.nan)
    result["ClickToConversionRate"] = result["Conversions"] / result["Clicks"].replace(0, np.nan)
    return result
