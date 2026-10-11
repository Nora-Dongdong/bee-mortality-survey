"""Fake survey data with the same columns as the de-identified file, for tests
and for running the pipeline before the real file is available."""
import numpy as np
import pandas as pd


def make(n_apiaries=800, seed=1):
    rng = np.random.default_rng(seed)
    n_bk = int(n_apiaries * 0.83)
    bk = rng.integers(1, n_bk + 1, n_apiaries)
    method = rng.choice([1, 2, 3, 4], n_apiaries, p=[.35, .2, .35, .1])
    food = rng.choice([1, 2, 3], n_apiaries, p=[.45, .4, .15])
    treat = rng.choice([1, 2, 3, 4, 5], n_apiaries, p=[.5, .1, .15, .15, .1])
    hives_in = rng.integers(1, 15, n_apiaries)
    logit = (-1.6 + 0.4 * (method == 3) + 0.5 * (food == 3)
             + np.select([treat == 5, treat == 4, treat == 3, treat == 1], [0.8, 0.6, 0.4, 0.1], 0))
    p = 1 / (1 + np.exp(-logit))
    dead = rng.binomial(hives_in, p)
    df = pd.DataFrame({
        "id_location": np.arange(1, n_apiaries + 1),
        "id_beekeeper": bk,
        "2025_winter_in": hives_in,
        "2026_winter_uit": hives_in - dead,
        "2025_winter_dood": dead,
        "imker_methode": method, "winter_food": food, "varroa_treatment": treat,
        "varroa_observation": rng.choice([1, 2, 3, 4, 5], n_apiaries),
        "aziatische_hoornaar": rng.choice([1, 2, 3, 4, 5], n_apiaries),
        "deformed_wings": rng.choice([1, 2, 3, 4, 5], n_apiaries),
    })
    # A few rows each cleaning rule should drop, and one dood mismatch.
    df.loc[0, "2026_winter_uit"] = df.loc[0, "2025_winter_in"] + 2
    df.loc[1, "2025_winter_in"] = 0
    df.loc[2, "2025_winter_dood"] = df.loc[2, "2025_winter_dood"] + 1
    df.loc[3, "winter_food"] = np.nan
    return df
