"""Memory-conscious source loading and deterministic export helpers."""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from .contracts import CONTRACTS, DataQualityError

LOGGER = logging.getLogger(__name__)
LARGE_TABLES = {"orders", "order_items", "payments", "shipments", "campaign_interactions", "product_reviews"}


def _read_csv(path: Path, date_columns: tuple[str, ...], chunk_size: int | None) -> pd.DataFrame:
    kwargs = {"low_memory": False, "parse_dates": list(date_columns)}
    if chunk_size is None:
        return pd.read_csv(path, **kwargs)
    chunks = []
    for number, chunk in enumerate(pd.read_csv(path, chunksize=chunk_size, **kwargs), start=1):
        LOGGER.debug("Read %s chunk %s with %,d rows", path.name, number, len(chunk))
        chunks.append(chunk)
    return pd.concat(chunks, ignore_index=True, copy=False)


def load_generated_data(source_directory: Path, chunk_size: int) -> dict[str, pd.DataFrame]:
    """Load normalized generated CSVs using contracts and chunks for large facts."""
    if not source_directory.exists():
        raise FileNotFoundError(f"Source directory does not exist: {source_directory}")
    data: dict[str, pd.DataFrame] = {}
    for table, contract in CONTRACTS.items():
        path = source_directory / f"{table}.csv"
        if not path.exists():
            raise FileNotFoundError(f"Required source table is missing: {path}")
        frame = _read_csv(path, contract.date_columns, chunk_size if table in LARGE_TABLES else None)
        missing = set(contract.columns) - set(frame.columns)
        if missing:
            raise DataQualityError(f"{table} is missing required columns: {sorted(missing)}")
        data[table] = frame
        LOGGER.info("Loaded %-24s %9s rows", table, f"{len(frame):,}")
    return data


def export_tables(tables: dict[str, pd.DataFrame], output_directory: Path) -> dict[str, int]:
    """Write stable Power BI-ready CSV exports and return row counts."""
    output_directory.mkdir(parents=True, exist_ok=True)
    counts = {}
    for name, frame in sorted(tables.items()):
        path = output_directory / f"{name}.csv"
        frame.to_csv(path, index=False, date_format="%Y-%m-%d %H:%M:%S", float_format="%.6f")
        counts[name] = len(frame)
        LOGGER.info("Exported %-24s %9s rows", path.name, f"{len(frame):,}")
    return counts
