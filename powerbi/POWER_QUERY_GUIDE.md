# Power Query Import Guide

## Parameters

Create `SourceType`, `SqlServerName`, `DatabaseName`, and `CsvRoot` parameters before loading tables. `SourceType` accepts `SQLServer` or `CSV`. Credentials belong in Power BI Desktop or the Power BI Service gateway and must never be committed in M code.

## Import rules

- Set identifiers and foreign keys to whole number, dates to Date, timestamps to Date/Time, money to Fixed decimal number, and rates to Decimal number.
- Preserve the verified CSV schemas in `power_query/QUERY_CATALOG.md`; review text is optional in visuals and should remain hidden outside a detail page.
- Disable load for staging queries and parameters.
- Preserve query folding for SQL Server. Avoid row-by-row custom functions before the final projection.
- Name final queries with semantic names such as `DimCustomer` and `FactOrders`.
- Load all 22 CSV queries when complete source coverage is required. Name aggregate exports with the `Validation*` prefix, keep them disconnected, and hide them from report view.

## Source equivalence

Map SQL analytics views and CSV exports to the same semantic table and column names. If SQL does not expose a stable surrogate key such as `GeographyKey`, add it in the reporting layer rather than using a refresh-dependent Power Query index.

## Refresh design

Import mode with full refresh is appropriate at portfolio scale. For an enterprise-scale demonstration, add `RangeStart` and `RangeEnd` parameters and incremental refresh policies to transactional event dates. Keep dimensions on full refresh unless their volume justifies another strategy.

After changing source type, verify row counts, key uniqueness, null foreign keys, and the six governed financial measures. A successful refresh alone does not prove semantic equivalence.
