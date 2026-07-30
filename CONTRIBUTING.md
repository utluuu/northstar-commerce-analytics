# Contributing

Thank you for improving Northstar Commerce Analytics. Contributions should preserve reproducibility, metric governance, and the documented fact grains.

## Development setup

Follow `SETUP_GUIDE.md` for the Windows environment. Before changing code:

```powershell
.\.venv\Scripts\Activate.ps1
python -m unittest discover -s tests -v
python scripts\check_repository.py
```

## Branches and commits

- Create a focused branch from `main`, such as `feature/delivery-sla` or `fix/refund-reconciliation`.
- Keep commits small and use imperative messages, for example `Add carrier SLA validation`.
- Do not combine formatting-only changes with metric or schema changes.

## Change requirements

- Document the business question and expected decision impact.
- Preserve deterministic generation; any stochastic behavior must use the configured seed.
- Define the grain of every new table or export.
- Update SQL, Python, Power BI, and documentation when a governed metric changes.
- Add or update tests for business logic, contracts, and failure cases.
- Keep SQL date filters half-open and SARGable where applicable.
- Prefer dimension-to-fact, single-direction Power BI relationships.
- Do not add raw credentials, generated datasets, local paths, `.pbix` files, database backups, or virtual environments.

## Metric governance

Changes to Revenue, Revenue After Refund, Gross Profit, Gross Profit After Refund, Refund Amount, AOV, return rate, retention, or CLV require:

1. A written definition and grain.
2. SQL and Python reconciliation evidence.
3. DAX and measure-dictionary updates where applicable.
4. A changelog entry under `Unreleased`.

## Pull request checklist

- [ ] The change has a clear business purpose.
- [ ] Tests pass locally.
- [ ] Repository audit passes.
- [ ] Documentation and data dictionary are current.
- [ ] No generated or sensitive files are included.
- [ ] SQL Server or Power BI manual validation requirements are recorded.
- [ ] `CHANGELOG.md` is updated for user-visible changes.

## Reporting issues

Include the operating system, Python version, SQL Server version, failing command, complete error message, and whether the dataset was regenerated with the default seed. Never include passwords or connection strings.
