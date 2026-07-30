"""Static contract tests for Power BI model assets."""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PowerBiAssetTests(unittest.TestCase):
    def test_theme_is_valid_json(self) -> None:
        payload = json.loads((ROOT / "powerbi" / "theme.json").read_text(encoding="utf-8"))
        self.assertEqual("Northstar Executive", payload["name"])
        self.assertGreaterEqual(len(payload["dataColors"]), 6)

    def test_expected_measures_are_defined_once(self) -> None:
        dax = (ROOT / "powerbi" / "measures.dax").read_text(encoding="utf-8")
        required = {
            "Revenue", "Revenue After Refund", "Gross Profit", "Gross Margin %", "Active Customers",
            "New Customers", "Repeat Customers", "Average Order Value", "Orders", "Units Sold",
            "Return Rate", "Refund Rate", "Average Historical CLV", "Retention %", "Churn Indicator %",
            "Pareto Revenue %", "Campaign Conversion %", "Revenue YoY %", "Revenue MoM %",
            "Rolling 3M Revenue", "Rolling 12M Revenue", "Revenue YTD", "Revenue MTD",
        }
        definitions = [name.strip() for name in re.findall(r"(?m)^([A-Za-z0-9 %]+)\s*=\s*$", dax)]
        self.assertTrue(required.issubset(set(definitions)))
        self.assertEqual(len(definitions), len(set(definitions)))

    def test_model_avoids_fact_to_fact_relationships(self) -> None:
        guide = (ROOT / "powerbi" / "MODEL_GUIDE.md").read_text(encoding="utf-8")
        self.assertIn("Never relate `FactOrders` to `FactOrderLines`", guide)
        self.assertIn("single-direction", guide)

    def test_all_seven_dashboard_pages_are_documented(self) -> None:
        blueprint = (ROOT / "docs" / "DASHBOARD_MOCKUP.md").read_text(encoding="utf-8")
        for page_name in [
            "Executive Overview", "Sales Performance", "Customer Analytics", "Product & Category Analytics",
            "Marketing & Campaign Performance", "Operations & Delivery", "Returns & Customer Satisfaction",
        ]:
            self.assertIn(page_name, blueprint)


if __name__ == "__main__":
    unittest.main()
