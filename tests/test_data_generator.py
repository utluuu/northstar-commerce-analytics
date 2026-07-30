"""Unit tests for deterministic data-generation primitives."""
from __future__ import annotations

import random
import unittest
from datetime import date

from data_generator.generate import WeightedSampler, build_dates, promotion_catalog


class WeightedSamplerTests(unittest.TestCase):
    def test_same_seed_produces_same_sequence(self) -> None:
        sampler = WeightedSampler(["a", "b", "c"], [1, 2, 7])
        first = random.Random(42)
        second = random.Random(42)
        self.assertEqual([sampler.sample(first) for _ in range(100)], [sampler.sample(second) for _ in range(100)])

    def test_invalid_weights_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            WeightedSampler([1, 2], [0, 0])


class BusinessCalendarTests(unittest.TestCase):
    def test_calendar_includes_full_date_range(self) -> None:
        dates, weights = build_dates(date(2025, 1, 1), date(2025, 12, 31))
        self.assertEqual(365, len(dates))
        self.assertEqual(len(dates), len(weights))
        self.assertGreater(weights[dates.index(date(2025, 11, 28))], weights[dates.index(date(2025, 2, 28))])

    def test_promotion_codes_are_unique(self) -> None:
        promotions = promotion_catalog(date(2023, 1, 1), date(2025, 12, 31))
        codes = [row["PromotionCode"] for row in promotions]
        self.assertEqual(18, len(promotions))
        self.assertEqual(len(codes), len(set(codes)))


if __name__ == "__main__":
    unittest.main()
