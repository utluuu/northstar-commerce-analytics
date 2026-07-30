# Data

The source of truth is the deterministic synthetic dataset created by `data_generator/generate.py`.

## Generated source data

Run `python -m data_generator.generate` to create normalized CSV files in `data/generated/`. The directory is gitignored because its contents are reproducible. Every build includes a row-count/checksum manifest and a validation report.

Default scale:

- 12,000 customers across behavioral segments
- 600 products across 24 subcategories
- 120,000 orders and 250,000+ order lines
- Payments, shipments, returns, verified reviews, promotions, and campaign interactions

Running `python/ecommerce_eda.py` exports Power BI-ready facts, dimensions, and analytical aggregates to `data/processed/`, including:

- `fact_orders.csv` — order-grain KPIs
- `fact_order_lines.csv` — product and margin detail
- `dim_customers.csv` — customer value and churn indicators
- `dim_products.csv` and `dim_date.csv` — reporting dimensions
- `monthly_performance.csv` — MoM, YoY, rolling, and running metrics
- `cohort_retention.csv` and `rfm_segments.csv` — customer analytics
- `fact_returns.csv` and `fact_reviews.csv` — return and review detail
- `campaign_performance.csv` — funnel and directly attributed value

Generated CSVs are gitignored because they can be rebuilt. The data contains no real people or transactions.
