# SQL Server Performance & Execution Plan Guide

## Query design choices

### SARGable time filtering

Procedures use half-open date ranges against the original `datetime2` column:

```sql
WHERE OrderDate >= @StartDate
  AND OrderDate < DATEADD(day, 1, @EndDate)
```

This preserves index seeks and includes every time on the end date. Avoid `CAST(OrderDate AS date) = @Date`, `YEAR(OrderDate) = @Year`, and inclusive `BETWEEN` filters on datetime columns.

### Optional parameters

`usp_SalesPerformance` uses `OPTION (RECOMPILE)` so SQL Server can simplify optional channel and region predicates for the actual parameter values. This trades compilation CPU for more appropriate plans and reduces parameter-sensitive-plan risk at portfolio scale.

### Grain-first aggregation

Revenue is aggregated separately from returns before joins. This prevents fan-out when one order has multiple lines, payments, return items, or campaign events. Analysis should use:

- `vw_OrderSummary` for order/AOV/customer/channel metrics;
- `vw_OrderLineAnalytics` for product/category metrics;
- `vw_CampaignPerformance` for promotion-grain funnel metrics.

### Market basket isolation

`usp_ProductAffinity` materializes the selected date range into `#OrderProducts` with a clustered primary key `(OrderId, ProductId)`. This:

- limits the expensive self-join to the requested period;
- guarantees one product occurrence per basket;
- gives SQL Server statistics on the temporary data;
- supports the pair join by `OrderId`.

## Supporting indexes

| Index | Primary workload |
|---|---|
| `IX_Orders_OrderDate` | Date-bounded revenue and basket extraction |
| `IX_Orders_CustomerId` | Customer history, sequence, cohort, RFM |
| `IX_Orders_ChannelDate` | Channel trends with date filter |
| `IX_Orders_ShippingAddressDate` | Region/state trends driven from addresses |
| `IX_Orders_PromotionId` | Campaign attribution and promoted-order analysis |
| `UQ_OrderItems_OrderProduct` | Order-to-line aggregation and basket pairs |
| `IX_OrderItems_ProductId` | Product performance aggregation |
| `IX_ReturnItems_OrderItemId` | Product-line refund reconciliation |
| `IX_Shipments_Carrier` | Carrier/service-level analysis |
| `IX_CampaignInteractions_Promotion` | Campaign funnel aggregation |
| `IX_CustomerRfmSnapshot_Segment` | Snapshot segment reporting |

## How to inspect plans

Use a representative cold and warm execution, not only a small date range:

```sql
SET STATISTICS IO ON;
SET STATISTICS TIME ON;

EXEC analytics.usp_SalesPerformance
    @StartDate = '2024-01-01',
    @EndDate = '2025-12-31',
    @ChannelName = NULL,
    @Region = NULL;

EXEC analytics.usp_ProductAffinity
    @StartDate = '2025-01-01',
    @EndDate = '2025-12-31',
    @MinimumPairOrders = 25,
    @TopN = 50;

SET STATISTICS TIME OFF;
SET STATISTICS IO OFF;
```

In SSMS, enable **Include Actual Execution Plan** and check:

- estimated versus actual row-count differences;
- scans on large tables when a selective seek is expected;
- key lookups repeated many times;
- hash/sort spills and memory-grant warnings;
- implicit conversions on join and filter columns;
- the most expensive operators in the market-basket self-join;
- parameter behavior for null versus selective filters.

## Known performance risks

1. **Views are not materialized.** Several views layer aggregations and window functions. At millions of orders, consider an incremental reporting fact table or indexed staging layer.
2. **Market-basket growth is nonlinear.** Pair generation increases with basket width. Restrict date range and minimum support; consider offline precomputation at larger scale.
3. **`COUNT(DISTINCT)` is memory intensive.** Cohort and active-customer queries may require larger memory grants as data grows.
4. **Window sorts can spill.** Customer sequence, Pareto, cohort, and RFM calculations depend on ordered partitions. Monitor tempdb and sort warnings.
   The customer-order sequence in `vw_OrderSummary` is calculated across customer history; date filters remain logically SARGable but may not be pushed below this window operator by the optimizer.
5. **Optional filters can create plan variability.** `OPTION (RECOMPILE)` is appropriate for analytical calls but may be expensive under high concurrency.
6. **Region filtering crosses the address relationship.** The shipping-address index helps, but a star-schema geography key would be better for a mature warehouse.
7. **Static PIVOT columns are demonstration-specific.** The portfolio query lists 2023–2025 explicitly. Production reporting should prefer conditional aggregation, a semantic tool, or controlled dynamic SQL.
8. **Indexes have write cost.** The proposed indexes favor analytical reads. For high-volume OLTP ingestion, load first and create/rebuild secondary indexes afterward.

## Scale-up path

For multi-million-order production scale:

- create partitioned order and order-line facts by order date;
- persist daily/monthly aggregates incrementally;
- add columnstore indexes to reporting facts, not the OLTP tables by default;
- maintain statistics after bulk loads;
- use Query Store to compare plan regressions;
- evaluate parameter-sensitive plan optimization on SQL Server 2022;
- separate the OLTP and analytical workloads.
