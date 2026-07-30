# Deployment Validation Checklist

This checklist records items that require SQL Server, Power BI Desktop, DAX Studio, or Power BI Service and therefore cannot be proven by repository-only tests.

## SQL Server acceptance

- [ ] `00_create_database.sql` completes on the intended local development instance.
- [ ] `01_schema.sql` creates all schemas, tables, constraints, and indexes without errors.
- [ ] ODBC Driver 18 connects using the selected authentication mode.
- [ ] The Python loader completes a full 120,000-order load without truncation or conversion errors.
- [ ] Generated and loaded row counts reconcile table by table.
- [ ] Foreign keys are trusted after loading and no orphan records exist.
- [ ] `03_views.sql` compiles every analytics view.
- [ ] `04_stored_procedures.sql` compiles every procedure.
- [ ] `06_data_quality_checks.sql` returns no failed critical checks.
- [ ] Financial totals reconcile across order-line, order-summary, SQL view, and Python export grains.
- [ ] Stored procedures are tested with null, valid, empty-result, and invalid parameter ranges.
- [ ] RFM snapshot refresh commits successfully and rolls back on forced failure.
- [ ] Execution plans use intended indexes for representative date, customer, product, and promotion filters.
- [ ] No implicit conversion or non-SARGable predicate causes a material scan regression.
- [ ] Full load and core procedure runtimes are recorded for the workstation.

## CSV semantic contract acceptance

- [ ] All 22 exports regenerate from a clean source dataset.
- [ ] Dimension keys are unique and non-null.
- [ ] Fact foreign keys resolve to their conformed dimensions, allowing only documented optional promotion blanks.
- [ ] `FactOrders`, `FactOrderLines`, `FactReturns`, and `FactReviews` preserve their documented grain.
- [ ] SQL-source and CSV-source schemas are mapped to identical Power BI names and compatible data types.
- [ ] SQL reporting objects expose stable geography and event-date keys required by the CSV model, or equivalent source queries are documented.

## Power BI Desktop acceptance

- [ ] `theme.json` imports without schema warnings.
- [ ] All relationships match `SETUP_GUIDE.md` exactly.
- [ ] Power BI reports no ambiguous relationship paths.
- [ ] All measures in `measures.dax` compile in the current Power BI Desktop version.
- [ ] DAX measures reconcile to SQL and Python reference totals.
- [ ] Date slicers filter transaction measures as intended.
- [ ] Campaign start-date filtering and RFM snapshot-date filtering behave as documented.
- [ ] Cohort retention matrix works without a relationship to `DimDate`.
- [ ] New Customers respects date and customer filters without accidental fact filtering.
- [ ] Pareto measures return stable results under customer, channel, region, and date selections.
- [ ] Campaign audience totals are labeled as summed campaign reach rather than unique cross-campaign reach.
- [ ] Every page, tooltip, drill-through, bookmark, and slicer interaction is tested.
- [ ] Accessibility checks pass for contrast, alt text, tab order, and non-color status encoding.
- [ ] Performance Analyzer shows acceptable interactive performance.
- [ ] DAX Studio or VertiPaq Analyzer confirms reasonable model size and no unnecessary high-cardinality columns.

## Power BI Service acceptance

- [ ] The report publishes to the intended workspace.
- [ ] Gateway and data-source credentials are configured outside the repository.
- [ ] Scheduled refresh completes successfully.
- [ ] Refresh failure notifications are configured.
- [ ] Workspace and report permissions follow least privilege.
- [ ] A published report URL or portfolio screenshot is added only after access and privacy review.

## Acceptance record

| Area | Tester | Date | Result | Evidence or issue |
|---|---|---|---|---|
| SQL Server deployment |  |  | Not run |  |
| SQL metric reconciliation |  |  | Not run |  |
| Power BI model |  |  | Not run |  |
| DAX validation |  |  | Not run |  |
| Report UX and accessibility |  |  | Not run |  |
| Power BI Service refresh |  |  | Not run |  |
