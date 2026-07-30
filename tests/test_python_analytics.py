"""Unit tests for reusable Python analytics calculations."""
from __future__ import annotations

import sys
import unittest
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from northstar_analytics.config import load_config
from northstar_analytics.analysis import build_discount_effectiveness
from northstar_analytics.model import build_monthly_performance, build_rfm


class ConfigurationTests(unittest.TestCase):
    def test_default_config_resolves_project_paths(self) -> None:
        config = load_config(ROOT / "python" / "eda_config.json")
        self.assertTrue(config.source_directory.is_absolute())
        self.assertEqual(100_000, config.chunk_size)
        self.assertGreaterEqual(config.figure_dpi, 120)


class MonthlyPerformanceTests(unittest.TestCase):
    def test_mom_yoy_and_running_revenue(self) -> None:
        dates = pd.date_range("2024-01-01", periods=14, freq="MS")
        orders = pd.DataFrame({
            "OrderId": range(1, 15), "CustomerId": range(1, 15), "OrderDate": dates,
            "StatusName": ["Delivered"] * 14, "IsRepeatPurchase": [0] * 14,
            "NetRevenue": [100.0] * 12 + [200.0, 200.0],
            "RevenueAfterRefund": [100.0] * 12 + [200.0, 200.0],
            "GrossProfit": [50.0] * 12 + [100.0, 100.0],
            "DiscountAmount": [0.0] * 14, "ReturnedUnits": [0] * 14,
        })
        result = build_monthly_performance(orders)
        self.assertAlmostEqual(1.0, result.loc[12, "RevenueYoYPct"])
        self.assertAlmostEqual(0.0, result.loc[13, "RevenueMoMPct"])
        self.assertAlmostEqual(1_600.0, result.iloc[-1]["RunningRevenue"])


class DiscountEffectivenessTests(unittest.TestCase):
    def test_grouping_columns_are_explicit_and_export_ready(self) -> None:
        orders = pd.DataFrame({
            "OrderId": [1, 2, 3, 4],
            "OrderDate": pd.to_datetime(["2025-01-03", "2025-01-18", "2025-02-02", "2025-02-14"]),
            "ChannelName": ["Web", "Web", "Marketplace", "Marketplace"],
            "PromotionId": [np.nan, 7.0, np.nan, 8.0],
            "NetRevenue": [100.0, 80.0, 120.0, 90.0],
            "RevenueAfterRefund": [100.0, 75.0, 120.0, 85.0],
            "GrossProfit": [40.0, 25.0, 50.0, 30.0],
            "DiscountAmount": [0.0, 20.0, 0.0, 10.0],
        })

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = build_discount_effectiveness(orders)

        self.assertFalse(caught)
        self.assertEqual(
            [
                "MonthStart", "ChannelName", "PromotionGroup", "Orders", "AverageOrderValue",
                "RevenueAfterRefund", "GrossProfit", "DiscountCost", "GrossProfitPerOrder",
            ],
            result.columns.tolist(),
        )
        self.assertEqual({"Promotion", "No Promotion"}, set(result["PromotionGroup"]))
        self.assertEqual(
            {pd.Timestamp("2025-01-01"), pd.Timestamp("2025-02-01")}, set(result["MonthStart"])
        )
        sorted_result = result.sort_values(["MonthStart", "ChannelName", "PromotionGroup"])
        self.assertEqual(len(result), len(sorted_result))


class RfmTests(unittest.TestCase):
    def test_rfm_scores_are_bounded_and_deterministic(self) -> None:
        orders = pd.DataFrame({
            "CustomerId": np.repeat(np.arange(1, 11), 2),
            "OrderId": np.arange(1, 21),
            "OrderDate": pd.date_range("2025-01-01", periods=20, freq="10D"),
            "StatusName": ["Delivered"] * 20,
            "RevenueAfterRefund": np.linspace(50, 500, 20),
        })
        first = build_rfm(orders, "2026-01-01")
        second = build_rfm(orders, "2026-01-01")
        pd.testing.assert_frame_equal(first, second)
        self.assertTrue(first[["RScore", "FScore", "MScore"]].stack().between(1, 5).all())
        self.assertTrue(first["RfmSegment"].notna().all())


if __name__ == "__main__":
    unittest.main()
