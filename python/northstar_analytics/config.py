"""Configuration models and path resolution for the EDA pipeline."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class AnalyticsConfig:
    """Resolved runtime settings for a reproducible analytics run."""

    source_directory: Path
    export_directory: Path
    figure_directory: Path
    report_directory: Path
    log_file: Path
    chunk_size: int = 100_000
    figure_dpi: int = 180
    top_products: int = 15
    cohort_months: int = 12
    rfm_snapshot_date: str = "2026-01-01"
    random_seed: int = 20260721


def _resolve(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else PROJECT_ROOT / path


def load_config(path: Path) -> AnalyticsConfig:
    """Load, validate, and resolve a JSON configuration file."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if int(payload["chunk_size"]) < 10_000:
        raise ValueError("chunk_size must be at least 10,000 rows")
    if int(payload["figure_dpi"]) < 120:
        raise ValueError("figure_dpi must be at least 120")
    return AnalyticsConfig(
        source_directory=_resolve(payload["source_directory"]),
        export_directory=_resolve(payload["export_directory"]),
        figure_directory=_resolve(payload["figure_directory"]),
        report_directory=_resolve(payload["report_directory"]),
        log_file=_resolve(payload["log_file"]),
        chunk_size=int(payload["chunk_size"]),
        figure_dpi=int(payload["figure_dpi"]),
        top_products=int(payload["top_products"]),
        cohort_months=int(payload["cohort_months"]),
        rfm_snapshot_date=str(payload["rfm_snapshot_date"]),
        random_seed=int(payload["random_seed"]),
    )
