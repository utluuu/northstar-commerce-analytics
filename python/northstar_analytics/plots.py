"""Professional, presentation-ready matplotlib visualizations."""
from __future__ import annotations

import logging
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).resolve().parents[2] / "work" / "matplotlib"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd

LOGGER = logging.getLogger(__name__)
NAVY, BLUE, TEAL, GOLD, RED, GREY = "#183153", "#2F6B9A", "#3A8D8C", "#D9A441", "#B74D4D", "#6B7280"


def configure_style() -> None:
    """Apply a restrained and accessible chart style."""
    plt.rcParams.update({
        "figure.facecolor": "white", "axes.facecolor": "white", "axes.edgecolor": "#D1D5DB",
        "axes.titleweight": "bold", "axes.titlesize": 13, "axes.labelsize": 10,
        "font.size": 10, "grid.color": "#E5E7EB", "grid.linewidth": 0.7,
        "axes.grid": True, "axes.axisbelow": True, "legend.frameon": False,
    })


def _save(fig: plt.Figure, directory: Path, filename: str, dpi: int) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    fig.text(0.99, 0.01, "Source: deterministic synthetic Northstar Commerce data", ha="right", color=GREY, fontsize=7)
    fig.tight_layout(rect=(0, 0.035, 1, 1))
    fig.savefig(directory / filename, dpi=dpi, bbox_inches="tight", metadata={"Title": filename, "Author": "Northstar Commerce Analytics"})
    plt.close(fig)
    LOGGER.info("Saved figure %s", filename)


def _currency_axis(axis) -> None:
    axis.set_major_formatter(mtick.FuncFormatter(lambda value, _: f"${value / 1_000_000:.1f}M" if abs(value) >= 1_000_000 else f"${value / 1_000:.0f}K"))


def plot_monthly_performance(monthly: pd.DataFrame, directory: Path, dpi: int) -> None:
    fig, ax = plt.subplots(figsize=(12, 5.5))
    ax.plot(monthly["MonthStart"], monthly["RevenueAfterRefund"], color=BLUE, linewidth=2.2, label="Revenue after refund")
    ax.plot(monthly["MonthStart"], monthly["GrossProfit"], color=TEAL, linewidth=2.0, label="Gross profit")
    ax.plot(monthly["MonthStart"], monthly["Rolling3MonthRevenue"], color=GOLD, linewidth=1.7, linestyle="--", label="3-month revenue average")
    ax.set(title="Is commercial performance growing beyond seasonal noise?", xlabel="Month", ylabel="Value ($)")
    _currency_axis(ax.yaxis); ax.set_ylim(bottom=0); ax.legend(ncol=3)
    _save(fig, directory, "01_monthly_revenue_profit.png", dpi)


def plot_growth(monthly: pd.DataFrame, directory: Path, dpi: int) -> None:
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.axhline(0, color=GREY, linewidth=1)
    ax.plot(monthly["MonthStart"], monthly["RevenueMoMPct"] * 100, color=BLUE, label="MoM")
    ax.plot(monthly["MonthStart"], monthly["RevenueYoYPct"] * 100, color=TEAL, linewidth=2, label="YoY")
    limit = np.nanpercentile(np.abs(pd.concat([monthly["RevenueMoMPct"], monthly["RevenueYoYPct"]]) * 100), 98)
    ax.set_ylim(-max(25, limit), max(25, limit))
    ax.set(title="How does revenue growth compare with prior periods?", xlabel="Month", ylabel="Growth rate")
    ax.yaxis.set_major_formatter(mtick.PercentFormatter()); ax.legend()
    _save(fig, directory, "02_mom_yoy_growth.png", dpi)


def plot_seasonality(seasonality: pd.DataFrame, directory: Path, dpi: int) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    colors = [GOLD if value > 1.15 else BLUE for value in seasonality["RevenueSeasonalityIndex"]]
    ax.bar(seasonality["MonthNumber"], seasonality["RevenueSeasonalityIndex"], color=colors)
    ax.axhline(1, color=GREY, linestyle="--", linewidth=1)
    ax.set(title="Which months over- or under-index on revenue?", xlabel="Calendar month", ylabel="Revenue seasonality index")
    ax.set_xticks(range(1, 13)); ax.set_ylim(bottom=0)
    _save(fig, directory, "03_revenue_seasonality.png", dpi)


def plot_acquisition(acquisition: pd.DataFrame, directory: Path, dpi: int) -> None:
    frame = acquisition.sort_values("RevenuePerPurchaser")
    fig, ax = plt.subplots(figsize=(10, 5.5))
    bars = ax.barh(frame["AcquisitionSource"], frame["RevenuePerPurchaser"], color=BLUE)
    ax.bar_label(bars, labels=[f"${value:,.0f}" for value in frame["RevenuePerPurchaser"]], padding=4, fontsize=8)
    ax.set(title="Which acquisition sources create the most customer value?", xlabel="After-refund revenue per purchasing customer", ylabel="")
    _currency_axis(ax.xaxis); ax.set_xlim(0, frame["RevenuePerPurchaser"].max() * 1.18)
    _save(fig, directory, "04_acquisition_source_value.png", dpi)


def plot_rfm(rfm_summary: pd.DataFrame, directory: Path, dpi: int) -> None:
    frame = rfm_summary.sort_values("Customers")
    fig, ax = plt.subplots(figsize=(10, 5.5))
    bars = ax.barh(frame["RfmSegment"], frame["Customers"], color=TEAL)
    ax.bar_label(bars, fmt="{:,.0f}", padding=4, fontsize=8)
    ax.set(title="How is the customer base distributed across RFM segments?", xlabel="Customers", ylabel="")
    ax.set_xlim(0, frame["Customers"].max() * 1.16)
    _save(fig, directory, "05_rfm_segment_distribution.png", dpi)


def plot_cohort(cohort: pd.DataFrame, directory: Path, dpi: int, max_months: int) -> None:
    filtered = cohort.query("MonthsSinceFirstOrder <= @max_months").copy()
    latest_cohorts = sorted(filtered["CohortMonth"].unique())[-18:]
    pivot = filtered[filtered["CohortMonth"].isin(latest_cohorts)].pivot(
        index="CohortMonth", columns="MonthsSinceFirstOrder", values="RetentionRate"
    )
    fig, ax = plt.subplots(figsize=(12, 7))
    image = ax.imshow(pivot.to_numpy(), aspect="auto", cmap="Blues", vmin=0, vmax=max(0.5, np.nanmax(pivot.to_numpy())))
    ax.set(title="Are newer customer cohorts retaining better?", xlabel="Months since first order", ylabel="First-order cohort")
    ax.set_xticks(range(len(pivot.columns)), pivot.columns)
    ax.set_yticks(range(len(pivot.index)), [pd.Timestamp(value).strftime("%Y-%m") for value in pivot.index])
    colorbar = fig.colorbar(image, ax=ax, pad=0.02); colorbar.ax.yaxis.set_major_formatter(mtick.PercentFormatter(1))
    _save(fig, directory, "06_cohort_retention_heatmap.png", dpi)


def plot_product_portfolio(products: pd.DataFrame, directory: Path, dpi: int, top_n: int) -> None:
    frame = products.nlargest(top_n, "NetRevenue")
    fig, ax = plt.subplots(figsize=(10, 6))
    sizes = 60 + 600 * frame["UnitReturnRate"].fillna(0)
    scatter = ax.scatter(frame["NetRevenue"], frame["GrossMarginRate"] * 100, s=sizes, c=frame["UnitReturnRate"], cmap="RdYlBu_r", alpha=0.8, edgecolor="white")
    right_edge = frame["NetRevenue"].max() * 0.90
    for _, row in frame.nlargest(5, "NetRevenue").iterrows():
        is_right = row["NetRevenue"] >= right_edge
        ax.annotate(str(row["ProductName"])[:24], (row["NetRevenue"], row["GrossMarginRate"] * 100),
                    xytext=(-5 if is_right else 5, 4), textcoords="offset points", fontsize=7,
                    ha="right" if is_right else "left")
    ax.set(title="Do top-revenue products also deliver margin and quality?", xlabel="Net revenue", ylabel="Gross margin rate")
    _currency_axis(ax.xaxis); ax.yaxis.set_major_formatter(mtick.PercentFormatter())
    colorbar = fig.colorbar(scatter, ax=ax, pad=0.02); colorbar.set_label("Unit return rate")
    colorbar.ax.yaxis.set_major_formatter(mtick.PercentFormatter(1))
    _save(fig, directory, "07_product_revenue_margin_returns.png", dpi)


def plot_returns(category: pd.DataFrame, directory: Path, dpi: int) -> None:
    frame = category.sort_values("RefundAmount")
    fig, ax = plt.subplots(figsize=(10, 5.5))
    bars = ax.barh(frame["CategoryName"], frame["RefundAmount"], color=RED)
    ax.bar_label(bars, labels=[f"${value / 1000:,.0f}K" for value in frame["RefundAmount"]], padding=4, fontsize=8)
    ax.set(title="Which categories create the largest refund exposure?", xlabel="Refund amount", ylabel="")
    _currency_axis(ax.xaxis); ax.set_xlim(0, frame["RefundAmount"].max() * 1.18)
    _save(fig, directory, "08_category_refund_exposure.png", dpi)


def plot_delivery(delivery: pd.DataFrame, directory: Path, dpi: int) -> None:
    frame = delivery.query("DeliveredOrders >= 100").sort_values("OnTimeRate").head(12).copy()
    frame["Lane"] = frame["Carrier"] + " · " + frame["Region"]
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(frame["Lane"], frame["OnTimeRate"] * 100, color=[RED if value < 0.8 else TEAL for value in frame["OnTimeRate"]])
    ax.bar_label(bars, labels=[f"{value:.1%}" for value in frame["OnTimeRate"]], padding=4, fontsize=8)
    ax.set(title="Which carrier-region lanes miss delivery promises?", xlabel="On-time delivery rate", ylabel="")
    ax.xaxis.set_major_formatter(mtick.PercentFormatter()); ax.set_xlim(0, 105)
    _save(fig, directory, "09_delivery_lane_performance.png", dpi)


def plot_campaigns(campaigns: pd.DataFrame, directory: Path, dpi: int) -> None:
    frame = campaigns.nlargest(10, "AttributedGrossProfit").sort_values("AttributedGrossProfit")
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(frame["PromotionName"], frame["AttributedGrossProfit"], color=GOLD)
    ax.bar_label(bars, labels=[f"${value / 1000:,.0f}K" for value in frame["AttributedGrossProfit"]], padding=4, fontsize=8)
    ax.set(title="Which campaigns have the highest directly attributed gross profit?", xlabel="Attributed gross profit", ylabel="")
    _currency_axis(ax.xaxis); ax.set_xlim(0, frame["AttributedGrossProfit"].max() * 1.18)
    _save(fig, directory, "10_campaign_attributed_profit.png", dpi)


def plot_pareto(pareto: pd.DataFrame, directory: Path, dpi: int) -> None:
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.plot(pareto["CumulativeCustomerShare"] * 100, pareto["CumulativeRevenueShare"] * 100, color=BLUE, linewidth=2.4)
    ax.plot([0, 100], [0, 100], color=GREY, linestyle="--", linewidth=1, label="Equal distribution")
    threshold = pareto.loc[pareto["CumulativeRevenueShare"].ge(0.8)].iloc[0]
    ax.scatter(threshold["CumulativeCustomerShare"] * 100, 80, color=RED, zorder=3)
    ax.annotate(f"{threshold['CumulativeCustomerShare']:.1%} of customers", (threshold["CumulativeCustomerShare"] * 100, 80), xytext=(8, -18), textcoords="offset points")
    ax.set(title="How concentrated is customer revenue?", xlabel="Cumulative share of purchasing customers", ylabel="Cumulative share of after-refund revenue")
    ax.xaxis.set_major_formatter(mtick.PercentFormatter()); ax.yaxis.set_major_formatter(mtick.PercentFormatter())
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.legend()
    _save(fig, directory, "11_customer_pareto_curve.png", dpi)


def plot_review_returns(rating: pd.DataFrame, directory: Path, dpi: int) -> None:
    fig, ax = plt.subplots(figsize=(8.5, 5))
    bars = ax.bar(rating["Rating"], rating["ReturnRate"] * 100, color=[RED, RED, GOLD, TEAL, TEAL])
    ax.bar_label(bars, labels=[f"{value:.1%}" for value in rating["ReturnRate"]], padding=4)
    ax.set(title="Are low review ratings associated with product returns?", xlabel="Review rating", ylabel="Return rate among reviewed items")
    ax.set_xticks([1, 2, 3, 4, 5]); ax.yaxis.set_major_formatter(mtick.PercentFormatter()); ax.set_ylim(bottom=0)
    _save(fig, directory, "12_review_rating_return_relationship.png", dpi)


def render_all(
    monthly: pd.DataFrame,
    products: pd.DataFrame,
    analyses: dict[str, pd.DataFrame],
    directory: Path,
    dpi: int,
    top_products: int,
    cohort_months: int,
) -> list[str]:
    """Render the complete deterministic figure suite."""
    configure_style()
    directory.mkdir(parents=True, exist_ok=True)
    for path in directory.glob("*.png"):
        path.unlink()
    plot_monthly_performance(monthly, directory, dpi)
    plot_growth(monthly, directory, dpi)
    plot_seasonality(analyses["seasonality"], directory, dpi)
    plot_acquisition(analyses["acquisition_performance"], directory, dpi)
    plot_rfm(analyses["rfm_summary"], directory, dpi)
    plot_cohort(analyses["cohort_retention"], directory, dpi, cohort_months)
    plot_product_portfolio(products, directory, dpi, top_products)
    plot_returns(analyses["category_performance"], directory, dpi)
    plot_delivery(analyses["delivery_performance"], directory, dpi)
    plot_campaigns(analyses["campaign_performance"], directory, dpi)
    plot_pareto(analyses["pareto_curve"], directory, dpi)
    plot_review_returns(analyses["review_return_relationship"], directory, dpi)
    return sorted(path.name for path in directory.glob("*.png"))
