"""Shared setup for the three analysis scripts."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd  # noqa: E402

from beesurvey import cleaning  # noqa: E402
from beesurvey.config import SEASONS  # noqa: E402


def parse_args(description, with_data=False):
    ap = argparse.ArgumentParser(description=description)
    ap.add_argument("season", nargs="?", default="2025-2026", choices=list(SEASONS))
    if with_data:
        ap.add_argument("--data", type=Path, help="survey CSV (default: path in config.py)")
    args = ap.parse_args()
    season = SEASONS[args.season]
    season.tables_dir.mkdir(parents=True, exist_ok=True)
    return args, season


def save_table(df: pd.DataFrame, season, name: str, index=False):
    """Every table goes through the personal-data check before it is written."""
    cleaning.assert_no_pii(df)
    df.to_csv(season.tables_dir / f"{name}.csv", index=index)


def load_clean(season) -> pd.DataFrame:
    if not season.clean_file.exists():
        raise SystemExit(f"{season.clean_file} not found: run scripts/01_cleaning.py first")
    return pd.read_csv(season.clean_file)
