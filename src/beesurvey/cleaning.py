"""Load the de-identified survey file and apply every exclusion rule as code.

Each rule is a named function that returns a boolean mask of rows to drop.
`clean()` applies them in order and returns a log with the row count per rule,
so the report can state exactly why each apiary was excluded.
"""
import re

import numpy as np
import pandas as pd

from .config import Season

# Column names that must never reach the repository or a saved notebook output.
PII_PATTERNS = [
    r"e-?mail", r"naam", r"\bname\b", r"gps", r"\blat", r"\blon", r"coord",
    r"postcode", r"zip", r"adres", r"address", r"straat", r"street",
    r"telefoon", r"phone", r"woonplaats", r"toelichting", r"opmerking",
    r"comment", r"_text$", r"anders",
]


def find_pii_columns(columns) -> list:
    """Column names that look like personal data or free text."""
    return [c for c in columns
            if any(re.search(p, str(c), flags=re.IGNORECASE) for p in PII_PATTERNS)]


def assert_no_pii(df: pd.DataFrame) -> None:
    hits = find_pii_columns(df.columns)
    if hits:
        raise ValueError(f"Personal or free-text columns found, drop them first: {hits}")


# Coded survey answers that are safe to keep. Everything else in the export
# (open-text "_origin" answers, disease free text, stray columns) is dropped on load.
EXTRA_COLUMNS = [
    "province", "bijenstanden_count",
    "honingdracht_voorjaar", "honingdracht_zomer", "honingdracht_nazomer",
    "stuifmeel_voorjaar", "stuifmeel_zomer", "stuifmeel_nazomer",
    "outside_nl",
]


def analysis_columns(season: Season) -> list:
    return [season.apiary_id, season.beekeeper_id, season.hives_in, season.hives_out,
            season.hives_dead, *season.categorical, *EXTRA_COLUMNS]


def load(season: Season, path=None) -> pd.DataFrame:
    """Read the survey CSV and keep only the coded analysis columns.

    Row 2 of a raw survey export holds the question text; it is detected and
    dropped if present."""
    path = path or season.data_file
    df = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    if len(df) and pd.to_numeric(df[season.hives_in].iloc[:1], errors="coerce").isna().all():
        df = df.iloc[1:].reset_index(drop=True)
    df = df[[c for c in analysis_columns(season) if c in df.columns]]
    assert_no_pii(df)
    return df


def parse_count(value) -> float:
    """Free-typed colony counts: 'Nee'/'o' -> 0, '3!' -> 3, 'januari 1 volk' -> 1."""
    if pd.isna(value):
        return np.nan
    text = str(value).strip().lower()
    if text in {"nee", "no", "n", "o", "geen"}:
        return 0.0
    match = re.search(r"\d+(?:[,.]\d+)?", text)
    return float(match.group(0).replace(",", ".")) if match else np.nan


def to_numeric(df: pd.DataFrame, season: Season) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Convert analysis columns to numbers. Returns the frame and a table of
    values that could not be parsed, instead of silently turning them into NaN."""
    df = df.copy()
    cols = [season.apiary_id, season.beekeeper_id, season.hives_in, season.hives_out,
            *season.categorical]
    if season.hives_dead in df.columns:
        df[season.hives_dead] = df[season.hives_dead].map(parse_count)
    problems = []
    for col in cols:
        if col not in df.columns:
            continue
        raw = df[col]
        num = pd.to_numeric(raw, errors="coerce")
        bad = raw.notna() & num.isna()
        if bad.any():
            problems.append(pd.DataFrame({
                "column": col, season.apiary_id: df.loc[bad, season.apiary_id],
                "value": raw[bad].astype(str),
            }))
        df[col] = num
    unparsed = pd.concat(problems, ignore_index=True) if problems else pd.DataFrame(
        columns=["column", season.apiary_id, "value"])
    return df, unparsed


# ------------------------------------------------------------------
# Exclusion rules: each returns True for rows to DROP.
# ------------------------------------------------------------------
def rule_no_apiary_id(df, s):
    """Summary/blank rows at the bottom of the export."""
    return df[s.apiary_id].isna()


def rule_missing_hive_counts(df, s):
    return df[s.hives_in].isna() | df[s.hives_out].isna()


def rule_no_hives_in_autumn(df, s):
    """0 colonies going into winter: mortality is undefined, not 0%."""
    return df[s.hives_in] <= 0


def rule_more_out_than_in(df, s):
    """More colonies in spring than in autumn (splits/purchases counted)."""
    return df[s.hives_out] > df[s.hives_in]


def rule_negative_counts(df, s):
    return (df[s.hives_in] < 0) | (df[s.hives_out] < 0)


def rule_flagged_outside_nl(df, s):
    """Apiaries outside the Netherlands. The de-identified file carries this as a
    boolean column `outside_nl` (derived from coordinates before they were removed)."""
    if "outside_nl" not in df.columns:
        return pd.Series(False, index=df.index)
    return df["outside_nl"].astype(str).str.strip().str.lower().isin({"1", "true", "y", "yes", "ja"})


RULES = [
    ("no apiary id (summary rows)", rule_no_apiary_id),
    ("hive counts missing", rule_missing_hive_counts),
    ("negative hive counts", rule_negative_counts),
    ("0 hives going into winter", rule_no_hives_in_autumn),
    ("more hives out than in", rule_more_out_than_in),
    ("apiary outside the Netherlands", rule_flagged_outside_nl),
]


def clean(df: pd.DataFrame, season: Season) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Apply RULES in order. Returns (clean frame, log of rows dropped per rule)."""
    df, _ = to_numeric(df, season)
    log = [{"step": "loaded", "dropped": 0, "remaining": len(df)}]
    for name, rule in RULES:
        mask = rule(df, season).fillna(False)
        df = df.loc[~mask]
        log.append({"step": name, "dropped": int(mask.sum()), "remaining": len(df)})

    df = df.copy()
    df["deaths"] = df[season.hives_in] - df[season.hives_out]
    df["mortality"] = df["deaths"] / df[season.hives_in]

    # Rows the old manual `delete` column flagged that no coded rule caught.
    if "delete" in df.columns:
        flagged = df["delete"].astype(str).str.strip().str.upper().eq("Y")
        log.append({"step": "note: manual delete=Y still present", "dropped": 0,
                    "remaining": int(flagged.sum())})
    return df.reset_index(drop=True), pd.DataFrame(log)


def death_definition_check(df: pd.DataFrame, season: Season) -> pd.DataFrame:
    """Compare in - uit with the reported number of dead colonies (winter_dood).

    The two differ when colonies were merged, sold, split or lost to queen
    failure and not counted as 'dead'. Returns one row per mismatching apiary."""
    if season.hives_dead not in df.columns:
        return pd.DataFrame()
    dood = df[season.hives_dead].map(parse_count)
    out = pd.DataFrame({
        season.apiary_id: df[season.apiary_id],
        "in": df[season.hives_in],
        "uit": df[season.hives_out],
        "in_minus_uit": df["deaths"],
        "dood_reported": dood,
    })
    out["difference"] = out["in_minus_uit"] - out["dood_reported"]
    return out.loc[out["difference"].ne(0) & out["dood_reported"].notna()]


def missing_report(df: pd.DataFrame, season: Season) -> pd.DataFrame:
    """Valid N per analysis variable, so every chart can state its N."""
    rows = []
    for col in season.categorical:
        if col not in df.columns:
            continue
        valid = df[col].notna()
        rows.append({
            "variable": col,
            "apiaries": int(valid.sum()),
            "apiaries_missing": int((~valid).sum()),
            "hives_in": int(df.loc[valid, season.hives_in].sum()),
        })
    return pd.DataFrame(rows)

