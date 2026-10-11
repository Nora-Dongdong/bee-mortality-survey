import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import statsmodels.api as sm

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from beesurvey import cleaning, descriptive, models  # noqa: E402
from beesurvey.config import SEASON_2025_2026 as S  # noqa: E402
import synthetic  # noqa: E402


@pytest.fixture(scope="module")
def df():
    clean, _ = cleaning.clean(synthetic.make(), S)
    return clean


def test_cleaning_rules_drop_bad_rows():
    clean, log = cleaning.clean(synthetic.make(), S)
    assert log.set_index("step").loc["more hives out than in", "dropped"] == 1
    assert log.set_index("step").loc["0 hives going into winter", "dropped"] == 1
    assert (clean["deaths"] >= 0).all()


def test_pii_guard():
    bad = synthetic.make().assign(email="x@y.nl", GPS_origin="52,4")
    with pytest.raises(ValueError):
        cleaning.assert_no_pii(bad)


def test_death_definition_check(df):
    assert len(cleaning.death_definition_check(df, S)) == 1


def test_group_rates_are_hive_weighted(df):
    t = descriptive.by_group(df, S, "winter_food")
    d = df.dropna(subset=["winter_food"])
    honey = d[d.winter_food == 3]
    assert t.set_index("code").loc[3, "mortality_pct"] == round(
        100 * honey.deaths.sum() / honey["2025_winter_in"].sum(), 2)


def test_colony_expansion_matches_binomial_glm(df):
    """GEE on one row per colony gives the same point estimates as a binomial
    GLM on (deaths, survivors) per apiary."""
    ap = models.model_sample(df, S)
    gee = models.fit(models.to_colonies(ap, S), models.formulas(S)["Model 3"], S)
    rhs = models.formulas(S)["Model 3"].split("~")[1]
    ap = ap.assign(survivors=ap["2026_winter_uit"])
    glm = sm.GLM.from_formula(f"deaths + survivors ~ {rhs}", ap,
                              family=sm.families.Binomial()).fit()
    np.testing.assert_allclose(gee.params.values, glm.params.values, rtol=1e-4)


def test_all_models_same_sample(df):
    res = models.fit_all(df, S)
    assert len({int(r.nobs) for r in res.values()}) == 1


def test_compare_cells_matches_coefficient(df):
    """Honey vs mix at the reference treatment = the honey main effect in Model 4."""
    m4 = models.fit_all(df, S)["Model 4"]
    out = models.compare_cells(m4, S, [("h", {"winter_food": 3}, {"winter_food": 2})])
    term = "C(winter_food, Treatment(2))[T.3]"
    assert out.loc[0, "odds_ratio"] == pytest.approx(np.exp(m4.params[term]))
