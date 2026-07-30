"""Executive reporting and reproducibility metadata outputs."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .analysis import BusinessInsight
from .config import AnalyticsConfig
from .validation import QualityReport


def write_quality_report(report: QualityReport, directory: Path) -> Path:
    """Write the machine-readable data-quality report."""
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "data_quality_report.json"
    path.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return path


def write_insights(insights: list[BusinessInsight], directory: Path) -> Path:
    """Write insights as a structured CSV for reuse in presentations."""
    path = directory / "business_insights.csv"
    pd.DataFrame([insight.to_dict() for insight in insights]).sort_values("priority").to_csv(path, index=False)
    return path


def write_run_manifest(
    config: AnalyticsConfig,
    export_counts: dict[str, int],
    figures: list[str],
    directory: Path,
) -> Path:
    """Write deterministic run metadata without wall-clock timestamps."""
    try:
        source_directory = str(config.source_directory.relative_to(config.report_directory.parent)).replace("\\", "/")
    except ValueError:
        source_directory = str(config.source_directory)
    payload = {
        "pipeline_version": "1.0.0",
        "source_directory": source_directory,
        "random_seed": config.random_seed,
        "rfm_snapshot_date": config.rfm_snapshot_date,
        "exports": export_counts,
        "figures": figures,
    }
    path = directory / "analysis_manifest.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def write_executive_summary(
    metrics: dict[str, float | int | str],
    insights: list[BusinessInsight],
    quality: QualityReport,
    export_counts: dict[str, int],
    figures: list[str],
    directory: Path,
) -> Path:
    """Create a recruiter-readable executive summary with actions and limitations."""
    insight_sections = []
    for insight in sorted(insights, key=lambda value: value.priority):
        insight_sections.append(
            f"### {insight.priority}. {insight.title}\n\n"
            f"**Finding:** {insight.finding}\n\n"
            f"**Business impact:** {insight.business_impact}\n\n"
            f"**Recommended action:** {insight.recommended_action}"
        )
    export_rows = "\n".join(f"| `{name}.csv` | {rows:,} |" for name, rows in sorted(export_counts.items()))
    figure_rows = "\n".join(f"- `{name}`" for name in figures)
    content = f"""# Executive Analysis Summary

## Portfolio scope

This report was generated from deterministic synthetic Northstar Commerce transactions through {metrics['as_of_date']}. It applies the same metric semantics as the SQL analytics layer and is intended to demonstrate reproducible business analysis rather than describe a real company.

## Executive scorecard

| KPI | Value |
|---|---:|
| Valid orders | {metrics['orders']:,} |
| Purchasing customers | {metrics['customers_with_orders']:,} |
| Booked net revenue | ${metrics['net_revenue']:,.0f} |
| Revenue after refund | ${metrics['revenue_after_refund']:,.0f} |
| Gross profit | ${metrics['gross_profit']:,.0f} |
| Gross margin rate | {metrics['gross_margin_rate']:.1%} |
| Average order value | ${metrics['average_order_value']:,.2f} |
| Repeat order rate | {metrics['repeat_order_rate']:.1%} |
| Repeat customer rate | {metrics['repeat_customer_rate']:.1%} |
| Refund leakage rate | {metrics['refund_leakage_rate']:.1%} |
| On-time delivery rate | {metrics['on_time_delivery_rate']:.1%} |

## Priority findings and actions

{chr(10).join(insight_sections)}

## Methodology

- Source CSVs are loaded under explicit table contracts; large facts are read in configurable chunks.
- Primary keys, foreign keys, required fields, valid ranges, chronology, and outlier counts are checked before analysis.
- Order-line economics are aggregated to order grain and reconciled within one cent.
- `NetRevenue` is booked revenue after line discount and excludes cancelled orders.
- `RevenueAfterRefund` subtracts refunds associated with non-rejected returns.
- `GrossProfitAfterRefund` is a conservative proxy that subtracts refunds without assuming inventory recovery.
- RFM uses deterministic portfolio quintiles at the configured snapshot date.
- Cohorts are assigned by first valid order month; customers count once per active month.
- CLV is a transparent annualized historical after-refund revenue run rate with a 90-day minimum observation period.
- Campaign attribution is direct promotion attribution, not causal incrementality.

## Data quality

- Status: **{quality.status}**
- Checks passed: **{quality.checks_passed}**
- Warnings: **{len(quality.warnings)}**
- Unexpected missing required values: **{sum(quality.unexpected_missing_values.values()):,}**
- Expected nullable values: **{sum(quality.expected_null_values.values()):,}**
- High-value line outliers retained: **{quality.outlier_counts.get('high_value_order_lines', 0):,}**

Outliers are reported rather than automatically removed because high-value orders may be commercially valid. Full results are available in `data_quality_report.json`.

## Limitations

- The dataset is synthetic and should not be used for external market benchmarks.
- Campaign cost is absent, so ROAS and true incremental profit cannot be calculated.
- Discount comparisons are observational and subject to customer self-selection.
- Shipping expense, overhead, marketing cost, and returned-inventory disposition are not modeled.
- Churn and projected value are interpretable rules/run rates, not trained probability models.
- Cohorts near the end of the observation window are right-censored and should only be compared at mature elapsed months.
- Review-return association is descriptive and does not establish that ratings cause returns.

## Power BI-ready exports

| File | Rows |
|---|---:|
{export_rows}

## Generated figures

{figure_rows}
"""
    path = directory / "EXECUTIVE_SUMMARY.md"
    path.write_text(content, encoding="utf-8")
    return path
