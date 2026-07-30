# Windows Setup and Deployment Guide

This guide reproduces Northstar Commerce Analytics from a clean Windows workstation through SQL Server, deterministic data generation, Python analytics, and the first Power BI report page.

## 1. Prerequisites

Install the following software before cloning the repository:

| Component | Supported version | Purpose |
|---|---|---|
| Git for Windows | Current stable | Clone and version control |
| Python | 3.11 x64 | Generator, validation, loader, EDA, and tests |
| SQL Server Developer Edition | SQL Server 2019+ | Local analytical database |
| SQL Server Management Studio | Current stable | Deploy and validate SQL objects |
| Microsoft ODBC Driver for SQL Server | Driver 18 x64 | Python-to-SQL Server connection |
| Power BI Desktop | Current Microsoft Store release | Semantic model and report |

During SQL Server setup, install the Database Engine and record the instance name. Windows Authentication is the recommended local configuration. Typical server names are `localhost`, `localhost\SQLEXPRESS`, or `localhost\MSSQLSERVER`.

Verify the command-line prerequisites in PowerShell:

```powershell
git --version
py -3.11 --version
Get-OdbcDriver | Where-Object Name -Like "*ODBC Driver 18 for SQL Server*"
```

## 2. Clone and enter the repository

```powershell
git clone https://github.com/<your-user>/<your-repository>.git
Set-Location <your-repository>
```

All following commands assume the repository root is the current directory.

## 3. Create the Python environment

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r python\requirements.txt
python -m unittest discover -s tests -v
```

If PowerShell blocks activation, run the following for the current process and activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Expected result: all unit and static contract tests pass. CI runs the same test command on Windows.

## 4. Configure the SQL Server connection

Copy the environment template and edit only `.env`:

```powershell
Copy-Item .env.example .env
notepad .env
```

Recommended Windows Authentication configuration:

```dotenv
DB_SERVER=localhost
DB_NAME=NorthstarCommerce
DB_DRIVER=ODBC Driver 18 for SQL Server
DB_TRUSTED_CONNECTION=yes
DB_USER=
DB_PASSWORD=
```

For SQL authentication, set `DB_TRUSTED_CONNECTION=no` and provide `DB_USER` and `DB_PASSWORD`. `.env` is ignored by Git. Do not place real credentials in `.env.example`, documentation, notebooks, or Power BI files.

## 5. Deploy the empty database

Open SSMS, connect to the target instance, and run scripts in SQLCMD mode or open each file separately in this order:

1. `sql/00_create_database.sql`
2. `sql/01_schema.sql`

> **Destructive development step:** `00_create_database.sql` drops `NorthstarCommerce` if it already exists. Confirm that the database contains no data you need before running it. Do not run this script against a shared or production instance.

The project SQL scripts currently use the fixed database name `NorthstarCommerce`; keep `DB_NAME` aligned with it.

Confirm the empty schema:

```sql
USE NorthstarCommerce;
SELECT name FROM sys.schemas WHERE name IN (N'ecommerce', N'analytics');
SELECT COUNT(*) AS EcommerceTableCount
FROM sys.tables AS t
JOIN sys.schemas AS s ON s.schema_id = t.schema_id
WHERE s.name = N'ecommerce';
```

## 6. Generate and validate the deterministic dataset

The default configuration uses seed `20260721` and creates 12,000 customers, 600 products, 120,000 orders, and more than 250,000 order lines.

```powershell
python -m data_generator.generate
python -m data_generator.validate
```

Generated source files are written to `data/generated/`. Inspect:

- `data/generated/manifest.json` for row counts and SHA-256 checksums.
- `data/generated/validation_report.json` for scale, integrity, repeat-purchase, basket, and seasonality checks.

The generated directory is intentionally excluded from Git because the files are reproducible and large.

## 7. Load SQL Server

Ensure SQL Server is running and the `.env` values identify the same instance used in SSMS:

```powershell
python -m data_generator.load_sql_server --batch-size 5000
```

The loader clears project tables before loading. It is a full deterministic reload, not an incremental process. `sql/02_prepare_bulk_load.sql` documents the equivalent delete order but does not need to be run when using the Python loader.

After loading, deploy the analytics layer in SSMS:

1. `sql/03_views.sql`
2. `sql/04_stored_procedures.sql`
3. `sql/06_data_quality_checks.sql`

`sql/05_advanced_analysis.sql` contains portfolio analysis result sets and can be run after deployment; it is not required to create database objects.

Run representative procedures:

```sql
EXEC analytics.usp_SalesPerformance
    @StartDate = '2025-01-01',
    @EndDate = '2025-12-31',
    @ChannelName = NULL;

EXEC analytics.usp_RefreshRfmSegments @AsOfDate = '2025-12-31';
EXEC analytics.usp_Customer360 @CustomerId = 17;
```

Complete every SQL item in `docs/DEPLOYMENT_VALIDATION.md` before considering SQL Server deployment accepted.

## 8. Run the Python analytics pipeline

```powershell
python python\ecommerce_eda.py
```

Expected outputs:

- Power BI-ready CSVs in `data/processed/`
- Twelve PNG charts in `reports/figures/`
- `reports/EXECUTIVE_SUMMARY.md`
- `reports/data_quality_report.json`
- `reports/analysis_manifest.json`
- `reports/business_insights.csv`

For calculations and exports without regenerating charts:

```powershell
python python\ecommerce_eda.py --skip-plots
```

## 9. Import CSVs into Power BI Desktop

Use **Home > Get data > Text/CSV** and import the following files from `data/processed/`. Rename each Power Query immediately.

| CSV file | Power BI table | Load into core model |
|---|---|---:|
| `dim_date.csv` | `DimDate` | Yes |
| `dim_customers.csv` | `DimCustomer` | Yes |
| `dim_products.csv` | `DimProduct` | Yes |
| `dim_channels.csv` | `DimChannel` | Yes |
| `dim_geography.csv` | `DimGeography` | Yes |
| `dim_promotions.csv` | `DimPromotion` | Yes |
| `fact_orders.csv` | `FactOrders` | Yes |
| `fact_order_lines.csv` | `FactOrderLines` | Yes |
| `fact_returns.csv` | `FactReturns` | Yes |
| `fact_reviews.csv` | `FactReviews` | Yes |
| `campaign_performance.csv` | `FactCampaignPerformance` | Yes |
| `cohort_retention.csv` | `FactCohortRetention` | Yes, disconnected |
| `rfm_segments.csv` | `FactRfmSnapshot` | Yes |

Do not load `monthly_performance`, `product_performance`, `category_performance`, `delivery_performance`, `discount_effectiveness`, `regional_channel_performance`, `pareto_curve`, or other aggregate exports into the primary model. They duplicate calculations available from atomic facts and are intended for reconciliation or portable extracts.

In Power Query:

1. Set ID and key columns to Whole number.
2. Set event dates to Date and timestamps to Date/Time.
3. Set monetary columns to Fixed decimal number.
4. Set rates to Decimal number.
5. Keep review text only if the Product Detail page will display it.
6. Select **Close & Apply**.

## 10. Create Power BI relationships

In Model view, create only these active, one-to-many, single-direction relationships. The dimension is always the `1` side and filters the fact.

| One side | Many side | Cardinality | Cross-filter |
|---|---|---|---|
| `DimDate[DateKey]` | `FactOrders[OrderDateKey]` | One-to-many | Single |
| `DimDate[DateKey]` | `FactOrderLines[OrderDateKey]` | One-to-many | Single |
| `DimDate[DateKey]` | `FactReturns[ReturnDateKey]` | One-to-many | Single |
| `DimDate[DateKey]` | `FactReviews[ReviewDateKey]` | One-to-many | Single |
| `DimDate[DateKey]` | `FactCampaignPerformance[StartDateKey]` | One-to-many | Single |
| `DimDate[DateKey]` | `FactRfmSnapshot[SnapshotDateKey]` | One-to-many | Single |
| `DimCustomer[CustomerId]` | `FactOrders[CustomerId]` | One-to-many | Single |
| `DimCustomer[CustomerId]` | `FactOrderLines[CustomerId]` | One-to-many | Single |
| `DimCustomer[CustomerId]` | `FactReturns[CustomerId]` | One-to-many | Single |
| `DimCustomer[CustomerId]` | `FactReviews[CustomerId]` | One-to-many | Single |
| `DimCustomer[CustomerId]` | `FactRfmSnapshot[CustomerId]` | One-to-many | Single |
| `DimProduct[ProductId]` | `FactOrderLines[ProductId]` | One-to-many | Single |
| `DimProduct[ProductId]` | `FactReturns[ProductId]` | One-to-many | Single |
| `DimProduct[ProductId]` | `FactReviews[ProductId]` | One-to-many | Single |
| `DimChannel[ChannelId]` | `FactOrders[ChannelId]` | One-to-many | Single |
| `DimChannel[ChannelId]` | `FactOrderLines[ChannelId]` | One-to-many | Single |
| `DimChannel[ChannelId]` | `FactReturns[ChannelId]` | One-to-many | Single |
| `DimGeography[GeographyKey]` | `FactOrders[GeographyKey]` | One-to-many | Single |
| `DimGeography[GeographyKey]` | `FactOrderLines[GeographyKey]` | One-to-many | Single |
| `DimGeography[GeographyKey]` | `FactReturns[GeographyKey]` | One-to-many | Single |
| `DimPromotion[PromotionId]` | `FactOrders[PromotionId]` | One-to-many | Single |
| `DimPromotion[PromotionId]` | `FactOrderLines[PromotionId]` | One-to-many | Single |
| `DimPromotion[PromotionId]` | `FactReturns[PromotionId]` | One-to-many | Single |
| `DimPromotion[PromotionId]` | `FactCampaignPerformance[PromotionId]` | One-to-many | Single |

Do not create relationships between fact tables. Leave `FactCohortRetention` disconnected. Use its own `CohortMonth` and `MonthsSinceFirstOrder` fields in the retention matrix.

Select `DimDate`, choose **Table tools > Mark as date table**, and select `FullDate`. Disable **Auto date/time** under **File > Options and settings > Options > Data Load**.

## 11. Add the DAX measures

Power BI Desktop does not import a plain `.dax` file automatically. Add measures manually:

1. Choose **Home > Enter data**.
2. Create one placeholder column and name the table `_Measures`.
3. Hide the placeholder column.
4. Open `powerbi/measures.dax` in a text editor.
5. For each `Measure Name = expression` block, select `_Measures`, choose **Table tools > New measure**, and paste the complete block into the formula bar.
6. Apply the format and display folder defined in `powerbi/MEASURE_DICTIONARY.md`.
7. Add the dictionary definition to each measure's Description property in Model view.

Add base measures first, followed by sales/customer, operations, marketing, retention, time-intelligence, and ranking measures. Later measures reference earlier ones.

## 12. Apply the report theme

1. Open **View > Themes > Browse for themes**.
2. Select `powerbi/theme.json`.
3. Confirm the theme imports without an error.
4. Do not use red and green without labels or icons; preserve the semantic colors documented in the dashboard blueprint.

## 13. Build Executive Overview first

Create a 16:9 page named `Executive Overview` and follow this order:

1. Add a relative-date slicer using `DimDate[FullDate]` and dropdown slicers for `DimChannel[ChannelName]`, `DimGeography[Region]`, and `DimProduct[CategoryName]`.
2. Add six cards: `Revenue After Refund`, `Revenue YoY %`, `Gross Profit After Refund`, `Gross Margin After Refund %`, `Orders`, and `Average Order Value`.
3. Add a monthly line chart with `DimDate[YearMonth]` on the X-axis and `Revenue` plus `Rolling 12M Revenue` as values.
4. Add a ranked horizontal bar chart with `DimProduct[CategoryName]` and `Product Revenue`.
5. Add a channel comparison using `DimChannel[ChannelName]`, `Revenue After Refund`, and `Gross Margin After Refund %`.
6. Add a waterfall using revenue, discounts, refunds, COGS, and after-refund gross profit. If a helper bridge table is used, keep it disconnected and drive it with a `SWITCH` measure.
7. Add an exception area showing `Return Rate`, `On-Time Delivery %`, `Churn Indicator %`, and `Revenue at Risk` with explicit labels.
8. Configure tooltips with current value, prior period, variance, orders, margin, and active customers.
9. Apply conditional formatting: adverse growth and margin in red, warnings in amber, favorable results in green.
10. Verify every visual under each slicer and run **View > Performance Analyzer**.

Use `docs/DASHBOARD_MOCKUP.md` for layout, drill-through, navigation, tooltip, and accessibility specifications.

## 14. Final reproducibility sequence

From a clean clone, the complete sequence is:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r python\requirements.txt
Copy-Item .env.example .env
python -m unittest discover -s tests -v
python -m data_generator.generate
python -m data_generator.validate
# Deploy sql/00_create_database.sql and sql/01_schema.sql in SSMS.
python -m data_generator.load_sql_server
# Deploy sql/03_views.sql, sql/04_stored_procedures.sql, and run sql/06_data_quality_checks.sql.
python python\ecommerce_eda.py
python scripts\check_repository.py
```

Power BI construction remains a manual Desktop workflow. Complete `docs/DEPLOYMENT_VALIDATION.md` and `docs/POWER_BI_MANUAL_CHECKLIST.md` before publishing or presenting the project.
