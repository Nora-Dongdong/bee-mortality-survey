"""Step 3: GEE regression models.

    python scripts/03_models.py [season]

Main analysis: Models 1-4, one row per colony (hive-weighted), clustered by
beekeeper. Sensitivity analysis: the same models with every apiary weighted
equally, as in the July 2026 report.
"""
import pandas as pd

from _common import load_clean, parse_args, save_table
from beesurvey import figures, models
from beesurvey.config import VARIABLE_LABELS

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

args, s = parse_args(__doc__)
df = load_clean(s)

# Main models
results = models.fit_all(df, s)
ors = models.summary_table(results)
save_table(ors, s, "03_gee_odds_ratios")
save_table(models.fit_info(results, s), s, "03_gee_fit_info")
for name in results:
    figures.odds_ratio_forest(ors.loc[ors["model"].eq(name)], s,
                              f"03_forest_{name.replace(' ', '').lower()}", f"{name}: odds ratios")

# Sensitivity: apiary-level, unweighted
sens = models.summary_table(models.fit_all_apiary_level(df, s))
save_table(sens, s, "03_gee_odds_ratios_apiary_level_sensitivity")
side = ors.merge(sens, on=["model", "term", "label"], suffixes=("_hive_weighted", "_apiary_level"))
save_table(side[["model", "label", "odds_ratio_hive_weighted", "p_value_hive_weighted",
                 "odds_ratio_apiary_level", "p_value_apiary_level"]], s,
           "03_gee_weighting_comparison")

# Predicted loss for the practical report
apiaries = models.model_sample(df, s)
pred = pd.concat([models.predicted_by_level(results["Model 3"], apiaries, s, v)
                  for v in models.PRACTICES])
save_table(pred, s, "03_predicted_mortality_model3")
for v in models.PRACTICES:
    figures.predicted_bars(pred.loc[pred["variable"].eq(v)], s, f"03_predicted_{v}",
                           f"Predicted winter loss by {VARIABLE_LABELS[v].lower()} (Model 3)")
grid = models.predicted_grid(results["Model 4"], apiaries, s)
save_table(grid, s, "03_predicted_treatment_x_feed_model4")
figures.heatmap(grid, s, "predicted_mortality_pct", "03_heatmap_predicted_model4",
                "Predicted winter loss by varroa treatment and winter feed (Model 4)")

comp = models.compare_cells(results["Model 4"], s, COMPARISONS)
save_table(comp, s, "03_primary_comparisons_model4")
print(comp.to_string(index=False))
print(f"\nTables: {s.tables_dir}\nFigures: {s.figures_dir}")
