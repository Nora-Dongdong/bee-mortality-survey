"""Hive-weighted mortality tables and chi-square tests.

One function per job, replacing the three copies of the same loop in the old
notebooks 02 and 05.
"""
from itertools import combinations

import pandas as pd
from scipy.stats import chi2_contingency

from .config import CODEBOOKS, Season


def overall(df: pd.DataFrame, s: Season) -> dict:
    hives_in = int(df[s.hives_in].sum())
    deaths = int(df["deaths"].sum())
    return {
        "apiaries": len(df),
        "beekeepers": int(df[s.beekeeper_id].nunique()),
        "hives_in": hives_in,
        "hives_out": int(df[s.hives_out].sum()),
        "deaths": deaths,
        "mortality_pct": round(100 * deaths / hives_in, 2),
    }


def by_group(df: pd.DataFrame, s: Season, col: str) -> pd.DataFrame:
    """Hive-weighted mortality per category: sum(deaths) / sum(hives in).

    Rows with a missing value for `col` are left out, so the table's hive total
    can be smaller than the overall total; the `hives_in` column shows the N."""
    d = df.dropna(subset=[col])
    g = d.groupby(col).agg(
        apiaries=(s.apiary_id, "size"),
        hives_in=(s.hives_in, "sum"),
        deaths=("deaths", "sum"),
    )
    g["share_of_apiaries_pct"] = (100 * g["apiaries"] / g["apiaries"].sum()).round(1)
    g["mortality_pct"] = (100 * g["deaths"] / g["hives_in"]).round(2)
    g.index = g.index.astype(int)
    g.insert(0, "label", g.index.map(CODEBOOKS.get(col, {})))
    g.index.name = "code"
    return g.reset_index()


def chi_square(df: pd.DataFrame, s: Season, col: str) -> dict:
    """Global chi-square on hives (died vs survived) across categories, plus
    Bonferroni-corrected pairwise tests when the global test is significant.

    Hives within an apiary are not independent, so these p-values are too small;
    they are descriptive only. Inference comes from the GEE models."""
    d = df.dropna(subset=[col])
    table = d.groupby(col)[[s.hives_out, "deaths"]].sum()
    table.index = table.index.astype(int)
    _, p_global, dof, _ = chi2_contingency(table)

    pairs = []
    if p_global < s.alpha and len(table) > 2:
        combos = list(combinations(table.index, 2))
        threshold = s.alpha / len(combos)
        labels = CODEBOOKS.get(col, {})
        for a, b in combos:
            _, p, _, _ = chi2_contingency(table.loc[[a, b]])
            pairs.append({
                "group_a": labels.get(a, a), "group_b": labels.get(b, b),
                "p_value": p, "significant_bonferroni": p < threshold,
            })
    return {"variable": col, "p_global": p_global, "dof": dof,
            "pairwise": pd.DataFrame(pairs)}


def crosstab_mortality(df: pd.DataFrame, s: Season, rows: str, cols: str) -> pd.DataFrame:
    """Long table of hive-weighted mortality for every rows x cols cell."""
    d = df.dropna(subset=[rows, cols])
    g = d.groupby([rows, cols]).agg(
        apiaries=(s.apiary_id, "size"),
        hives_in=(s.hives_in, "sum"),
        deaths=("deaths", "sum"),
    ).reset_index()
    g["mortality_pct"] = (100 * g["deaths"] / g["hives_in"]).round(2)
    g["small_sample"] = g["apiaries"] < s.min_apiaries_per_cell
    for c in (rows, cols):
        g[c] = g[c].astype(int)
        g[f"{c}_label"] = g[c].map(CODEBOOKS.get(c, {}))
    return g


def composition(df: pd.DataFrame, rows: str, cols: str) -> pd.DataFrame:
    """Share of apiaries in each `cols` category within each `rows` category (%).

    Used to explain confounding, e.g. why 'Natural' beekeepers look worse:
    they feed honey and skip treatment more often."""
    d = df.dropna(subset=[rows, cols])
    t = pd.crosstab(d[rows].astype(int), d[cols].astype(int), normalize="index") * 100
    t.index = t.index.map(CODEBOOKS.get(rows, {}))
    t.columns = t.columns.map(CODEBOOKS.get(cols, {}))
    return t.round(1)
