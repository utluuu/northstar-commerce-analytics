"""Static contract tests for the portfolio SQL analytics layer."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VIEWS = (ROOT / "sql" / "03_views.sql").read_text(encoding="utf-8")
PROCEDURES = (ROOT / "sql" / "04_stored_procedures.sql").read_text(encoding="utf-8")
ANALYSES = (ROOT / "sql" / "05_advanced_analysis.sql").read_text(encoding="utf-8")


class SqlObjectContractTests(unittest.TestCase):
    def test_required_views_exist(self) -> None:
        required = {
            "vw_OrderLineAnalytics", "vw_OrderSummary", "vw_CustomerMetrics",
            "vw_MonthlyKpis", "vw_MonthlyPerformance", "vw_CohortRetention",
            "vw_ProductPerformance", "vw_ReturnAnalysis", "vw_ProductReviewAnalytics",
            "vw_CampaignPerformance",
        }
        actual = set(re.findall(r"CREATE OR ALTER VIEW analytics\.(\w+)", VIEWS, re.IGNORECASE))
        self.assertTrue(required.issubset(actual))

    def test_required_procedures_exist(self) -> None:
        required = {
            "usp_SalesPerformance", "usp_Customer360", "usp_RefreshRfmSegments",
            "usp_ProductAffinity", "usp_CohortRetention", "usp_ProductPerformance",
        }
        actual = set(re.findall(r"CREATE OR ALTER PROCEDURE analytics\.(\w+)", PROCEDURES, re.IGNORECASE))
        self.assertEqual(required, actual)

    def test_every_procedure_has_error_handling(self) -> None:
        blocks = re.split(r"CREATE OR ALTER PROCEDURE", PROCEDURES, flags=re.IGNORECASE)[1:]
        for block in blocks:
            self.assertIn("BEGIN TRY", block.upper())
            self.assertIn("BEGIN CATCH", block.upper())

    def test_date_range_filter_is_half_open(self) -> None:
        self.assertIn("OrderDate >= @StartDate AND o.OrderDate < @EndExclusive", PROCEDURES)
        self.assertNotRegex(PROCEDURES, r"OrderDate\s+BETWEEN\s+@StartDate")


class AnalysisCoverageTests(unittest.TestCase):
    def test_analysis_catalog_has_sixteen_business_questions(self) -> None:
        self.assertEqual(16, len(re.findall(r"ANALYSIS \d{2}", ANALYSES)))
        self.assertEqual(16, len(re.findall(r"Business question:", ANALYSES)))

    def test_advanced_sql_techniques_are_demonstrated(self) -> None:
        for token in ("WITH ", "LAG(", "LEAD(", "RANK(", "DENSE_RANK(", "ROW_NUMBER(", "PIVOT", "ROWS UNBOUNDED PRECEDING"):
            self.assertIn(token, ANALYSES.upper())
        self.assertIn("#OrderProducts", PROCEDURES)
        self.assertIn("BEGIN TRANSACTION", PROCEDURES)


if __name__ == "__main__":
    unittest.main()
