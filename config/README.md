# Configuration Directory

Runtime configuration remains colocated with the component that owns it:

- `data_generator/config.json` controls deterministic dataset scale, seed, date range, review rate, and return rate.
- `python/eda_config.json` controls source paths, export paths, RFM snapshot date, chunk size, and chart settings.
- `.env` is created locally from `.env.example` and contains SQL Server connection settings.

This directory is the repository-level configuration index. Keeping component configuration beside its implementation prevents ambiguous duplicate settings while preserving a clear discovery point for operators.
