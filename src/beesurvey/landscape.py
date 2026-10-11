"""Crop diversity and toxicity around the apiary, on the same footing as the
main models: same death definition (in - uit), same reference groups, same
clustering and working correlation (see models.py).

The landscape indices are computed outside this repo from apiary coordinates
and crop parcel maps, then saved as a table without coordinates:

    id_location, radius_m, crop_diversity_index, toxicity_index

The coordinates themselves never enter the repository.
"""
import numpy as np
import pandas as pd

from .config import Season
from . import models

INDICES = ["crop_diversity_index", "toxicity_index"]


def load_indices(path) -> pd.DataFrame:
    idx = pd.read_csv(path)
    missing = {"id_location", "radius_m"} - set(idx.columns)
    if missing:
        raise ValueError(f"Landscape file is missing columns: {missing}")
    return idx


def model_data(df: pd.DataFrame, idx: pd.DataFrame, s: Season, radius_m: int, index: str,
               honey_only: bool = False) -> pd.DataFrame:
    r = idx.loc[idx["radius_m"].eq(radius_m), ["id_location", index]]
    d = models.model_sample(df, s).merge(r, left_on=s.apiary_id, right_on="id_location",
                                         how="inner", validate="many_to_one")
    d = d.dropna(subset=[index])
    if honey_only:
        d = d.loc[d["winter_food"].eq(3)]
    return d


def formulas(s: Season, index: str, honey_only: bool) -> dict:
    t = models._terms(s)
    controls = [t["imker_methode"], t["varroa_treatment"]]
    if not honey_only:
        controls.insert(1, t["winter_food"])
    return {
        "unadjusted": f"died ~ {index}",
        "adjusted": f"died ~ {index} + " + " + ".join(controls),
    }


def fit_grid(df: pd.DataFrame, idx: pd.DataFrame, s: Season, radii=(500, 1000)) -> pd.DataFrame:
    """Every index x radius x sample x adjustment combination, one row each,
    with the odds ratio per 1-unit increase of the index."""
    rows = []
    for index in [i for i in INDICES if i in idx.columns]:
        for radius in radii:
            for honey_only in (False, True):
                apiaries = model_data(df, idx, s, radius, index, honey_only)
                if apiaries[s.beekeeper_id].nunique() < 2:
                    continue
                colonies = models.to_colonies(apiaries, s)
                for adj, formula in formulas(s, index, honey_only).items():
                    r = models.fit(colonies, formula, s)
                    lo, hi = r.conf_int().loc[index]
                    rows.append({
                        "index": index, "radius_m": radius,
                        "sample": "honey only" if honey_only else "all apiaries",
                        "model": adj,
                        "apiaries": len(apiaries),
                        "colonies": int(r.nobs),
                        "beekeeper_clusters": int(apiaries[s.beekeeper_id].nunique()),
                        "odds_ratio_per_unit": float(np.exp(r.params[index])),
                        "ci_low": float(np.exp(lo)), "ci_high": float(np.exp(hi)),
                        "p_value": float(r.pvalues[index]),
                    })
    return pd.DataFrame(rows)
