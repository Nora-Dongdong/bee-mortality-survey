"""The four GEE models from the report, written with the formula interface.

Outcome: did each colony die over winter (in - uit), one row per colony.
Clusters: beekeeper (several apiaries of one beekeeper share practices).
Working correlation: independence, with robust (sandwich) standard errors.

Model 1  feed + varroa treatment
Model 2  feed x varroa treatment (interaction)
Model 3  method + feed + varroa treatment
Model 4  method + feed x varroa treatment

All four are fitted on the same apiaries (complete cases for the three
practice variables), so their coefficients can be compared directly.
"""
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests

from .config import CODEBOOKS, Season

PRACTICES = ["imker_methode", "winter_food", "varroa_treatment"]


def _terms(s: Season) -> dict:
    ref = s.reference
    return {v: f"C({v}, Treatment({ref[v]}))" for v in PRACTICES}


def formulas(s: Season) -> dict:
    t = _terms(s)
    m, f, v = t["imker_methode"], t["winter_food"], t["varroa_treatment"]
    return {
        "Model 1": f"died ~ {f} + {v}",
        "Model 2": f"died ~ {f} * {v}",
        "Model 3": f"died ~ {m} + {f} + {v}",
        "Model 4": f"died ~ {m} + {f} * {v}",
    }


def model_sample(df: pd.DataFrame, s: Season) -> pd.DataFrame:
    """Apiaries with all three practice variables answered."""
    d = df.dropna(subset=PRACTICES + [s.beekeeper_id]).copy()
    for v in PRACTICES:
        d[v] = d[v].astype(int)
    return d


def to_colonies(apiaries: pd.DataFrame, s: Season) -> pd.DataFrame:
    """One row per colony: died = 1 for the first `deaths` colonies of an apiary."""
    n = apiaries[s.hives_in].astype(int).to_numpy()
    rows = apiaries.loc[apiaries.index.repeat(n)].copy()
    pos = rows.groupby(level=0).cumcount().to_numpy()
    rows["died"] = (pos < rows["deaths"].astype(int).to_numpy()).astype(int)
    return rows.reset_index(drop=True)


def fit(colonies: pd.DataFrame, formula: str, s: Season):
    model = sm.GEE.from_formula(
        formula,
        groups=s.beekeeper_id,
        data=colonies,
        family=sm.families.Binomial(),
        cov_struct=sm.cov_struct.Independence(),
    )
    return model.fit()


def fit_all(df: pd.DataFrame, s: Season) -> dict:
    colonies = to_colonies(model_sample(df, s), s)
    return {name: fit(colonies, f, s) for name, f in formulas(s).items()}


# ------------------------------------------------------------------
# Readable output
# ------------------------------------------------------------------
def _pretty_term(term: str) -> str:
    """'C(winter_food, Treatment(2))[T.3]' -> 'Winter feed: Honey only'."""
    from .config import VARIABLE_LABELS
    parts = []
    for piece in term.split(":"):
        if piece.startswith("C("):
            var = piece[2:piece.index(",")]
            code = int(float(piece[piece.index("[T.") + 3:-1]))
            parts.append(f"{VARIABLE_LABELS.get(var, var)}: {CODEBOOKS[var].get(code, code)}")
        else:
            parts.append(piece)
    return " x ".join(parts)


def odds_ratio_table(result, model_name: str) -> pd.DataFrame:
    ci = result.conf_int()
    out = pd.DataFrame({
        "model": model_name,
        "term": result.params.index,
        "label": [_pretty_term(t) for t in result.params.index],
        "odds_ratio": np.exp(result.params.values),
        "ci_low": np.exp(ci[0].values),
        "ci_high": np.exp(ci[1].values),
        "p_value": result.pvalues.values,
    })
    return out


def summary_table(results: dict) -> pd.DataFrame:
    return pd.concat([odds_ratio_table(r, n) for n, r in results.items()], ignore_index=True)


def fit_info(results: dict, s: Season) -> pd.DataFrame:
    rows = []
    for name, r in results.items():
        data = r.model.data.frame
        rows.append({
            "model": name,
            "colonies": int(r.nobs),
            "apiaries": int(data[s.apiary_id].nunique()),
            "beekeeper_clusters": int(data[s.beekeeper_id].nunique()),
            "deaths": int(data["died"].sum()),
        })
    return pd.DataFrame(rows)


# ------------------------------------------------------------------
# Predicted mortality: the number the practical report shows
# ------------------------------------------------------------------
def predicted_mortality(result, apiaries: pd.DataFrame, s: Season, setting: dict) -> float:
    """Mortality (%) if every apiary in the sample used `setting`, with everything
    else as observed. Colony-weighted average of model predictions."""
    d = apiaries.copy()
    for k, v in setting.items():
        d[k] = v
    p = np.asarray(result.predict(d))
    return float(100 * np.average(p, weights=d[s.hives_in]))


def predicted_by_level(result, apiaries: pd.DataFrame, s: Season, var: str) -> pd.DataFrame:
    rows = []
    for code in sorted(apiaries[var].unique()):
        rows.append({
            "variable": var, "code": int(code), "label": CODEBOOKS[var].get(int(code), code),
            "predicted_mortality_pct": predicted_mortality(result, apiaries, s, {var: code}),
            "observed_mortality_pct": float(
                100 * apiaries.loc[apiaries[var] == code, "deaths"].sum()
                / apiaries.loc[apiaries[var] == code, s.hives_in].sum()),
            "apiaries": int((apiaries[var] == code).sum()),
        })
    return pd.DataFrame(rows)


def predicted_grid(result, apiaries: pd.DataFrame, s: Season,
                   rows: str = "varroa_treatment", cols: str = "winter_food") -> pd.DataFrame:
    out = []
    for r in sorted(apiaries[rows].unique()):
        for c in sorted(apiaries[cols].unique()):
            n = int(((apiaries[rows] == r) & (apiaries[cols] == c)).sum())
            out.append({
                rows: int(r), cols: int(c), "apiaries": n,
                "predicted_mortality_pct": predicted_mortality(result, apiaries, s, {rows: r, cols: c}),
            })
    return pd.DataFrame(out)


# ------------------------------------------------------------------
# Cell-vs-cell comparisons (replaces notebook 04 and the pickle file)
# ------------------------------------------------------------------
def _design_row(result, values: dict) -> np.ndarray:
    """Model-matrix row for one hypothetical apiary ."""
    data = result.model.data
    row = pd.DataFrame([values])
    spec = getattr(data, "model_spec", None) or getattr(data, "design_info", None)
    if hasattr(spec, "get_model_matrix"):  # formulaic
        x = spec.get_model_matrix(row).reindex(columns=result.model.exog_names, fill_value=0)
    else:  # patsy
        from patsy import build_design_matrices
        x = build_design_matrices([spec], row)[0]
    return np.asarray(x, dtype=float)[0]


def compare_cells(result, s: Season, comparisons: list, method: str = "holm") -> pd.DataFrame:
    """Each comparison is (name, setting_a, setting_b), e.g.
    ("Honey: no treatment vs 3-step", {"winter_food": 3, "varroa_treatment": 5},
                                       {"winter_food": 3, "varroa_treatment": 1}).

    Unspecified practices are held at the reference group; in these additive-on-
    the-logit models the contrast does not depend on that choice. P-values are
    adjusted across the whole list (Holm by default)."""
    base = {v: s.reference[v] for v in PRACTICES}
    rows = []
    for name, a, b in comparisons:
        xa = _design_row(result, {**base, **a})
        xb = _design_row(result, {**base, **b})
        t = result.t_test(xa - xb)
        lo, hi = np.asarray(t.conf_int()).ravel()
        rows.append({
            "comparison": name,
            "odds_ratio": float(np.exp(t.effect.item())),
            "ci_low": float(np.exp(lo)), "ci_high": float(np.exp(hi)),
            "p_value": float(t.pvalue.item()),
        })
    out = pd.DataFrame(rows)
    if len(out):
        out[f"p_{method}"] = multipletests(out["p_value"], method=method)[1]
        out["significant"] = out[f"p_{method}"] < s.alpha
    return out
