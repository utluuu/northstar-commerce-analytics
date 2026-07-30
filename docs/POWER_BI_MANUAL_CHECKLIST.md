# Power BI Manual Build Checklist

## Data import

- [ ] Import the 13 approved semantic model CSVs listed in `SETUP_GUIDE.md`.
- [ ] Rename every query to its semantic table name before applying changes.
- [ ] Verify ID, date, timestamp, currency, and rate data types.
- [ ] Confirm dimension keys are unique and facts contain the expected row counts.
- [ ] Exclude aggregate reconciliation exports from the primary model.
- [ ] Remove or disable load for unused staging queries.

## Semantic model

- [ ] Create only documented dimension-to-fact relationships.
- [ ] Confirm every relationship is one-to-many and single-direction.
- [ ] Confirm there are no fact-to-fact or bidirectional relationships.
- [ ] Leave `FactCohortRetention` disconnected.
- [ ] Mark `DimDate[FullDate]` as the date table.
- [ ] Disable Auto date/time.
- [ ] Sort `MonthName` by `MonthNumber` and `YearMonth` chronologically.
- [ ] Build product and geography hierarchies.
- [ ] Hide surrogate keys, foreign keys, technical date keys, and raw fact columns.
- [ ] Set raw fact numeric fields to `Do not summarize`.

## Measures

- [ ] Create the `_Measures` table.
- [ ] Add every measure from `powerbi/measures.dax` in dependency order.
- [ ] Apply formats and display folders from `powerbi/MEASURE_DICTIONARY.md`.
- [ ] Add measure descriptions in Model view.
- [ ] Reconcile Revenue, Revenue After Refund, Gross Profit, Gross Profit After Refund, Refund Amount, and Orders.
- [ ] Confirm time-intelligence measures return blank when no comparable period exists.
- [ ] Confirm cohort retention does not show misleading grand totals.

## Report design

- [ ] Import `powerbi/theme.json` without errors.
- [ ] Set every primary page to 16:9.
- [ ] Build and validate Executive Overview before other pages.
- [ ] Implement all seven primary pages from `docs/DASHBOARD_MOCKUP.md`.
- [ ] Create documented drill-through and report-page tooltip pages.
- [ ] Sync only slicers that apply to every visual on target pages.
- [ ] Add Reset filters, Back, Definitions, and navigation controls.
- [ ] Disable misleading cross-highlight interactions.
- [ ] Add minimum-volume warnings to return and rating visuals.

## Accessibility and performance

- [ ] Add descriptive alt text to every meaningful visual.
- [ ] Set a logical keyboard tab order.
- [ ] Verify that color is never the only indicator of status.
- [ ] Verify text contrast and readability at 100% zoom.
- [ ] Check page layout at common laptop resolution.
- [ ] Run Performance Analyzer on every page.
- [ ] Investigate visuals taking more than two seconds.
- [ ] Remove unused columns and high-cardinality fields from overview pages.

## Publication

- [ ] Remove local credentials and personal filesystem paths.
- [ ] Set source parameters and gateway credentials in Power BI Service.
- [ ] Configure refresh and test it successfully.
- [ ] Add a visible last-refresh timestamp.
- [ ] Validate permissions before sharing.
- [ ] Export screenshots for the repository only after final acceptance.
