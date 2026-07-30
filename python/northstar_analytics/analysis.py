"""Business analyses and evidence-backed insight generation."""
from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class BusinessInsight:
    """One quantified finding with business impact and recommended action."""

    priority: int
    title: str
    finding: str
    business_impact: str
    recommended_action: str

    def to_dict(self) -> dict:
        return asdict(self)


def build_discount_effectiveness(valid_orders: pd.DataFrame) -> pd.DataFrame:
    """Aggregate monthly promotion economics at month, channel, and promotion-group grain."""
    discount_source = valid_orders.assign(
        MonthStart=valid_orders["OrderDate"].dt.to_period("M").dt.to_timestamp(),
        PromotionGroup=np.where(valid_orders["PromotionId"].notna(), "Promotion", "No Promotion"),
    )
    discount = discount_source.groupby(
        ["MonthStart", "ChannelName", "PromotionGroup"], as_index=False, sort=True
    ).agg(
        Orders=("OrderId", "count"), AverageOrderValue=("NetRevenue", "mean"),
        RevenueAfterRefund=("RevenueAfterRefund", "sum"), GrossProfit=("GrossProfit", "sum"),
        DiscountCost=("DiscountAmount", "sum"),
    )
    discount["GrossProfitPerOrder"] = discount["GrossProfit"] / discount["Orders"].replace(0, np.nan)
    return discount


def build_analysis_tables(
    raw: dict[str, pd.DataFrame],
    orders: pd.DataFrame,
    customers: pd.DataFrame,
    monthly: pd.DataFrame,
    cohort: pd.DataFrame,
    rfm: pd.DataFrame,
    products: pd.DataFrame,
    returns: pd.DataFrame,
    reviews: pd.DataFrame,
    campaigns: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    """Build curated business-analysis tables used by plots and Power BI."""
    valid_orders = orders.query("StatusName != 'Cancelled'").copy()
    order_acquisition = valid_orders.merge(
        raw["customers"][["CustomerId", "AcquisitionSource"]], on="CustomerId", validate="many_to_one"
    )
    acquisition = order_acquisition.groupby("AcquisitionSource", as_index=False).agg(
        Customers=("CustomerId", "nunique"), Orders=("OrderId", "count"),
        RevenueAfterRefund=("RevenueAfterRefund", "sum"), GrossProfit=("GrossProfit", "sum"),
        AverageOrderValue=("NetRevenue", "mean"), RepeatOrders=("IsRepeatPurchase", "sum"),
    )
    acquired = raw["customers"].groupby("AcquisitionSource")["CustomerId"].nunique().rename("AcquiredCustomers")
    acquisition = acquisition.merge(acquired, on="AcquisitionSource", how="outer").fillna(0)
    acquisition["PurchaserConversionRate"] = acquisition["Customers"] / acquisition["AcquiredCustomers"].replace(0, np.nan)
    acquisition["RevenuePerPurchaser"] = acquisition["RevenueAfterRefund"] / acquisition["Customers"].replace(0, np.nan)
    acquisition["RepeatOrderRate"] = acquisition["RepeatOrders"] / acquisition["Orders"].replace(0, np.nan)

    category = products.groupby("CategoryName", as_index=False).agg(
        Products=("ProductId", "count"), Orders=("Orders", "sum"), UnitsSold=("UnitsSold", "sum"),
        NetRevenue=("NetRevenue", "sum"), RevenueAfterRefund=("RevenueAfterRefund", "sum"),
        GrossProfit=("GrossProfit", "sum"), ReturnedUnits=("ReturnedUnits", "sum"),
        RefundAmount=("RefundAmount", "sum"), DiscountAmount=("DiscountAmount", "sum"),
    )
    category["GrossMarginRate"] = category["GrossProfit"] / category["NetRevenue"].replace(0, np.nan)
    category["UnitReturnRate"] = category["ReturnedUnits"] / category["UnitsSold"].replace(0, np.nan)
    category["RefundToRevenueRate"] = category["RefundAmount"] / category["NetRevenue"].replace(0, np.nan)

    delivered = valid_orders.dropna(subset=["DeliveredDate"]).copy()
    delivery = delivered.groupby(["Carrier", "Region"], as_index=False).agg(
        DeliveredOrders=("OrderId", "count"), AverageDeliveryDays=("DeliveryDays", "mean"),
        MedianDeliveryDays=("DeliveryDays", "median"), OnTimeRate=("IsOnTime", "mean"),
        LateOrders=("IsOnTime", lambda series: int(series.eq(0).sum())),
    )

    discount = build_discount_effectiveness(valid_orders)

    regional_channel = valid_orders.groupby(["Region", "ChannelName"], as_index=False).agg(
        Orders=("OrderId", "count"), Customers=("CustomerId", "nunique"),
        RevenueAfterRefund=("RevenueAfterRefund", "sum"), GrossProfit=("GrossProfit", "sum"),
        RepeatOrders=("IsRepeatPurchase", "sum"),
    )
    regional_channel["GrossMarginRate"] = regional_channel["GrossProfit"] / regional_channel["RevenueAfterRefund"].replace(0, np.nan)
    regional_channel["RepeatOrderRate"] = regional_channel["RepeatOrders"] / regional_channel["Orders"].replace(0, np.nan)

    pareto = customers.query("LifetimeRevenueAfterRefund > 0")[["CustomerId", "LifetimeRevenueAfterRefund"]].sort_values(
        ["LifetimeRevenueAfterRefund", "CustomerId"], ascending=[False, True]
    ).reset_index(drop=True)
    pareto["CustomerRank"] = np.arange(1, len(pareto) + 1)
    pareto["CumulativeCustomerShare"] = pareto["CustomerRank"] / len(pareto)
    pareto["CumulativeRevenueShare"] = pareto["LifetimeRevenueAfterRefund"].cumsum() / pareto["LifetimeRevenueAfterRefund"].sum()

    rating_returns = reviews.groupby("Rating", as_index=False).agg(
        Reviews=("ReviewId", "count"), ReturnedReviews=("WasReturned", "sum"), ReturnRate=("WasReturned", "mean")
    )

    monthly_copy = monthly.copy()
    monthly_copy["MonthNumber"] = monthly_copy["MonthStart"].dt.month
    seasonality = monthly_copy.groupby("MonthNumber", as_index=False).agg(
        AverageMonthlyRevenue=("RevenueAfterRefund", "mean"), AverageOrders=("Orders", "mean")
    )
    seasonality["RevenueSeasonalityIndex"] = seasonality["AverageMonthlyRevenue"] / monthly_copy["RevenueAfterRefund"].mean()

    first_orders = valid_orders.sort_values(["CustomerId", "OrderDateTime", "OrderId"])
    first_orders["NextOrderDate"] = first_orders.groupby("CustomerId")["OrderDate"].shift(-1)
    repeat = first_orders.query("CustomerOrderNumber == 1")[["CustomerId", "OrderDate", "NextOrderDate"]].copy()
    repeat["DaysToSecondOrder"] = (repeat["NextOrderDate"] - repeat["OrderDate"]).dt.days
    repeat["RepeatedWithin30Days"] = repeat["DaysToSecondOrder"].le(30)
    repeat["RepeatedWithin60Days"] = repeat["DaysToSecondOrder"].le(60)
    repeat["RepeatedWithin90Days"] = repeat["DaysToSecondOrder"].le(90)

    churn = customers.groupby("LifecycleStatus", as_index=False).agg(
        Customers=("CustomerId", "count"), RevenueAtRisk=("LifetimeRevenueAfterRefund", "sum"),
        Projected12MonthRevenue=("Projected12MonthRevenue", "sum"), AverageRecencyDays=("RecencyDays", "mean"),
    )
    rfm_summary = rfm.groupby("RfmSegment", as_index=False).agg(
        Customers=("CustomerId", "count"), SegmentValue=("MonetaryValue", "sum"),
        AverageRecencyDays=("RecencyDays", "mean"), AverageFrequency=("Frequency", "mean"),
    )

    return {
        "acquisition_performance": acquisition,
        "category_performance": category,
        "delivery_performance": delivery,
        "discount_effectiveness": discount,
        "regional_channel_performance": regional_channel,
        "pareto_curve": pareto,
        "review_return_relationship": rating_returns,
        "seasonality": seasonality,
        "repeat_purchase": repeat,
        "churn_summary": churn,
        "rfm_summary": rfm_summary,
        "cohort_retention": cohort,
        "campaign_performance": campaigns,
        "return_detail": returns,
    }


def executive_metrics(
    orders: pd.DataFrame, customers: pd.DataFrame, monthly: pd.DataFrame
) -> dict[str, float | int | str]:
    """Return headline commercial and customer metrics."""
    valid = orders.query("StatusName != 'Cancelled'")
    delivered = valid.dropna(subset=["DeliveredDate"])
    latest = monthly.iloc[-1]
    return {
        "as_of_date": str(orders["OrderDate"].max().date()),
        "orders": int(len(valid)),
        "customers_with_orders": int(valid["CustomerId"].nunique()),
        "net_revenue": float(valid["NetRevenue"].sum()),
        "revenue_after_refund": float(valid["RevenueAfterRefund"].sum()),
        "gross_profit": float(valid["GrossProfit"].sum()),
        "gross_margin_rate": float(valid["GrossProfit"].sum() / valid["NetRevenue"].sum()),
        "average_order_value": float(valid["NetRevenue"].mean()),
        "repeat_order_rate": float(valid["IsRepeatPurchase"].mean()),
        "repeat_customer_rate": float(customers["IsRepeatCustomer"].mean()),
        "refund_leakage_rate": float(valid["RefundAmount"].sum() / valid["NetRevenue"].sum()),
        "on_time_delivery_rate": float(delivered["IsOnTime"].mean()),
        "latest_month_yoy_growth": float(latest["RevenueYoYPct"]) if pd.notna(latest["RevenueYoYPct"]) else np.nan,
    }


def generate_insights(
    metrics: dict[str, float | int | str],
    monthly: pd.DataFrame,
    analyses: dict[str, pd.DataFrame],
) -> list[BusinessInsight]:
    """Generate twelve quantified findings with decisions and recommended actions."""
    season = analyses["seasonality"].sort_values("RevenueSeasonalityIndex", ascending=False).iloc[0]
    acquisition = analyses["acquisition_performance"].sort_values("RevenuePerPurchaser", ascending=False).iloc[0]
    category = analyses["category_performance"].sort_values("GrossProfit", ascending=False).iloc[0]
    return_category = analyses["category_performance"].sort_values("UnitReturnRate", ascending=False).iloc[0]
    delivery = analyses["delivery_performance"].query("DeliveredOrders >= 100").sort_values(["OnTimeRate", "AverageDeliveryDays"]).iloc[0]
    campaign = analyses["campaign_performance"].sort_values("AttributedGrossProfit", ascending=False).iloc[0]
    churn = analyses["churn_summary"]
    risk = churn[churn["LifecycleStatus"].isin(["At Risk", "High Risk"])]["RevenueAtRisk"].sum()
    pareto = analyses["pareto_curve"]
    eighty = pareto.loc[pareto["CumulativeRevenueShare"].ge(0.80)].iloc[0]
    rating = analyses["review_return_relationship"].set_index("Rating")
    low_rating_return = rating.loc[rating.index.isin([1, 2]), "ReturnedReviews"].sum() / rating.loc[rating.index.isin([1, 2]), "Reviews"].sum()
    high_rating_return = rating.loc[rating.index.isin([4, 5]), "ReturnedReviews"].sum() / rating.loc[rating.index.isin([4, 5]), "Reviews"].sum()
    discount = analyses["discount_effectiveness"].groupby("PromotionGroup").agg(
        Orders=("Orders", "sum"), GrossProfit=("GrossProfit", "sum"), Revenue=("RevenueAfterRefund", "sum")
    )
    discount["GrossProfitPerOrder"] = discount["GrossProfit"] / discount["Orders"]
    promo_delta = discount.loc["Promotion", "GrossProfitPerOrder"] / discount.loc["No Promotion", "GrossProfitPerOrder"] - 1
    cohort = analyses["cohort_retention"].query("MonthsSinceFirstOrder == 1")
    m1_retention = cohort["RetentionRate"].mean()
    latest_yoy = metrics["latest_month_yoy_growth"]

    return [
        BusinessInsight(1, "After-refund revenue establishes the commercial baseline",
            f"Booked net revenue is ${metrics['net_revenue']:,.0f}; refunds reduce it to ${metrics['revenue_after_refund']:,.0f} ({metrics['refund_leakage_rate']:.1%} leakage).",
            "Using booked revenue alone overstates realized commercial value.",
            "Use RevenueAfterRefund as the executive revenue KPI and monitor refund leakage beside growth."),
        BusinessInsight(2, "Latest year-over-year momentum",
            f"The latest complete monthly comparison shows {latest_yoy:.1%} year-over-year after-refund revenue growth.",
            "Growth direction affects inventory, acquisition, and capacity planning.",
            "Decompose the change by orders, active customers, AOV, channel, and category before setting targets."),
        BusinessInsight(3, "Demand is concentrated in a seasonal peak",
            f"Month {int(season['MonthNumber'])} has the highest revenue seasonality index at {season['RevenueSeasonalityIndex']:.2f}x an average month.",
            "Seasonal concentration raises stockout, fulfillment, and working-capital risk.",
            "Plan inventory and carrier capacity against the seasonal index and track forecast error by category."),
        BusinessInsight(4, "Acquisition-source quality differs",
            f"{acquisition['AcquisitionSource']} leads after-refund revenue per purchasing customer at ${acquisition['RevenuePerPurchaser']:,.0f}.",
            "Volume-only acquisition reporting can reward low-value sources.",
            "Compare source-level cost with purchaser conversion, repeat rate, and after-refund value before reallocating spend."),
        BusinessInsight(5, "Repeat behavior drives portfolio economics",
            f"{metrics['repeat_customer_rate']:.1%} of acquired customers are repeat customers and {metrics['repeat_order_rate']:.1%} of valid orders are repeat purchases.",
            "Second-order conversion is a leading indicator of retention and future value.",
            "Build 30/60/90-day post-purchase journeys and measure incremental second-order conversion."),
        BusinessInsight(6, "Month-one cohort retention sets the early baseline",
            f"Average month-one cohort retention is {m1_retention:.1%} across observed cohorts.",
            "Weak early retention limits CLV even when acquisition volume grows.",
            "Monitor cohort retention by acquisition source and first-purchase category, using only mature cohorts."),
        BusinessInsight(7, "Customer value is exposed to churn risk",
            f"At Risk and High Risk customers represent ${risk:,.0f} in historical after-refund revenue.",
            "Losing high-value customers creates disproportionate revenue risk.",
            "Prioritize win-back tests by risk status and historical value rank; use holdouts to measure incrementality."),
        BusinessInsight(8, "Category profit leadership",
            f"{category['CategoryName']} contributes the highest gross profit at ${category['GrossProfit']:,.0f} with {category['GrossMarginRate']:.1%} margin.",
            "Revenue leadership and profit leadership may require different assortment decisions.",
            "Protect availability for high-profit products and review low-margin volume for basket-building value."),
        BusinessInsight(9, "Returns identify a category-quality hotspot",
            f"{return_category['CategoryName']} has the highest unit return rate at {return_category['UnitReturnRate']:.1%} and ${return_category['RefundAmount']:,.0f} in refunds.",
            "Returns reduce realized revenue and may signal quality, content, or expectation problems.",
            "Break the category down by SKU and reason; assign corrective work to supplier, packaging, or content owners."),
        BusinessInsight(10, "A fulfillment lane requires attention",
            f"{delivery['Carrier']} in {delivery['Region']} has the lowest qualifying on-time rate at {delivery['OnTimeRate']:.1%} across {int(delivery['DeliveredOrders']):,} deliveries.",
            "Late delivery can drive support contacts, churn, and 'Too Late' returns.",
            "Review lane-level SLA performance and test routing rules against on-time delivery and cost."),
        BusinessInsight(11, "Campaign attribution must be evaluated on profit",
            f"{campaign['PromotionName']} has the highest directly attributed gross profit at ${campaign['AttributedGrossProfit']:,.0f}.",
            "High attributed revenue may still be discount-dependent and is not proof of incrementality.",
            "Add campaign cost and randomized holdouts before making budget decisions; retain direct attribution as descriptive reporting."),
        BusinessInsight(12, "Value concentration and experience signals",
            f"{eighty['CumulativeCustomerShare']:.1%} of purchasing customers generate 80% of after-refund revenue. Low-rating reviews return at {low_rating_return:.1%} versus {high_rating_return:.1%} for ratings 4-5; promoted gross profit per order differs by {promo_delta:.1%} from non-promoted orders.",
            "Concentrated value and review-return alignment help prioritize retention and product-quality work.",
            "Protect high-value relationships, investigate low-rating SKUs, and treat promotion comparisons as hypotheses for controlled tests."),
    ]
