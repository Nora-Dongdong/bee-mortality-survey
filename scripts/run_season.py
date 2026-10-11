"""Run the whole analysis for one season and write every table and figure.

    python scripts/run_season.py 2025-2026 [--data path/to/file.csv] [--landscape path.csv]

Outputs go to tables/<season>/ and figures/<season>/. Both reports quote numbers
only from these files.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd  # noqa: E402

from beesurvey import cleaning, descriptive, figures, landscape, models  # noqa: E402
from beesurvey.config import SEASONS, VARIABLE_LABELS  # noqa: E402

# Pre-declared primary comparisons (report section 4.5). Everything else is exploratory.
COMPARISONS = [
    ("Honey only: no treatment vs full 3-step",
     {"winter_food": 3, "varroa_treatment": 5}, {"winter_food": 3, "varroa_treatment": 1}),
    ("Honey only: summer only vs full 3-step",
     {"winter_food": 3, "varroa_treatment": 4}, {"winter_food": 3, "varroa_treatment": 1}),
    ("Honey only: winter only vs full 3-step",
     {"winter_food": 3, "varroa_treatment": 3}, {"winter_food": 3, "varroa_treatment": 1}),
    ("Full 3-step: honey only vs sugar only",
     {"winter_food": 3, "varroa_treatment": 1}, {"winter_food": 1, "varroa_treatment": 1}),
]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("season", choices=list(SEASONS))
    ap.add_argument("--data", type=Path)
    ap.add_argument("--landscape", type=Path)
    args = ap.parse_args(argv)
    s = SEASONS[args.season]
    s.tables_dir.mkdir(parents=True, exist_ok=True)

    def save(df, name):
        cleaning.assert_no_pii(df)
        df.to_csv(s.tables_dir / f"{name}.csv", index=False)

    # 1. Cleaning
    raw = cleaning.load(s, args.data)
    df, log = cleaning.clean(raw, s)
    save(log, "01_cleaning_log")
    save(cleaning.missing_report(df, s), "01_valid_n_per_variable")
    check = cleaning.death_definition_check(df, s)
    save(check, "01_death_definition_mismatches")
    print(log.to_string(index=False))
    print(f"in - uit differs from reported dead colonies in {len(check)} of {len(df)} apiaries")

    # 2. Descriptive
    tot = descriptive.overall(df, s)
    save(pd.DataFrame([tot]), "02_overall")
    print(f"\nOverall: {tot}")
    tests = []
    for var in s.categorical:
        if var not in df.columns:
            continue
        t = descriptive.by_group(df, s, var)
        save(t, f"02_mortality_by_{var}")
        figures.mortality_bars(t, s, var, tot["mortality_pct"], f"02_mortality_by_{var}")
        chi = descriptive.chi_square(df, s, var)
        tests.append({"variable": var, "p_global": chi["p_global"], "dof": chi["dof"]})
        if len(chi["pairwise"]):
            save(chi["pairwise"], f"02_pairwise_{var}")
    save(pd.DataFrame(tests), "02_chi_square")
    cells = descriptive.crosstab_mortality(df, s, "varroa_treatment", "winter_food")
    save(cells, "02_mortality_treatment_x_feed")
    figures.heatmap(cells, s, "mortality_pct", "02_heatmap_treatment_x_feed",
                    "Observed winter loss by varroa treatment and winter feed")
    for other in ["winter_food", "varroa_treatment"]:
        comp = descriptive.composition(df, "imker_methode", other)
        comp.reset_index().to_csv(s.tables_dir / f"02_method_x_{other}_share.csv", index=False)

    # 3. GEE models
    results = models.fit_all(df, s)
    ors = models.summary_table(results)
    save(ors, "03_gee_odds_ratios")
    save(models.fit_info(results, s), "03_gee_fit_info")
    for name, r in results.items():
        figures.odds_ratio_forest(ors.loc[ors["model"].eq(name)], s,
                                  f"03_forest_{name.replace(' ', '').lower()}", f"{name}: odds ratios")
    apiaries = models.model_sample(df, s)
    m3, m4 = results["Model 3"], results["Model 4"]
    pred = pd.concat([models.predicted_by_level(m3, apiaries, s, v) for v in models.PRACTICES])
    save(pred, "03_predicted_mortality_model3")
    for v in models.PRACTICES:
        figures.predicted_bars(pred.loc[pred["variable"].eq(v)], s, f"03_predicted_{v}",
                               f"Predicted winter loss by {VARIABLE_LABELS[v].lower()} (Model 3)")
    grid = models.predicted_grid(m4, apiaries, s)
    save(grid, "03_predicted_treatment_x_feed_model4")
    figures.heatmap(grid, s, "predicted_mortality_pct", "03_heatmap_predicted_model4",
                    "Predicted winter loss by varroa treatment and winter feed (Model 4)")
    comp = models.compare_cells(m4, s, COMPARISONS)
    save(comp, "03_primary_comparisons_model4")
    print("\n", comp.to_string(index=False))

    # 4. Landscape (crop diversity / toxicity)
    if args.landscape:
        grid = landscape.fit_grid(df, landscape.load_indices(args.landscape), s)
        save(grid, "04_landscape_gee")
        print("\n", grid.to_string(index=False))

    print(f"\nTables: {s.tables_dir}\nFigures: {s.figures_dir}")


if __name__ == "__main__":
    main()
