"""Step 2: descriptive statistics.

    python scripts/02_descriptive.py [season]

Hive-weighted loss per answer category, chi-square tests (descriptive only),
the varroa treatment x winter feed grid, and how practices differ by method.
"""
import pandas as pd

from _common import load_clean, parse_args, save_table
from beesurvey import descriptive, figures

args, s = parse_args(__doc__)
df = load_clean(s)

tot = descriptive.overall(df, s)
save_table(pd.DataFrame([tot]), s, "02_overall")
print(f"Overall: {tot}")

tests = []
for var in s.categorical:
    if var not in df.columns:
        continue
    t = descriptive.by_group(df, s, var)
    save_table(t, s, f"02_mortality_by_{var}")
    figures.mortality_bars(t, s, var, tot["mortality_pct"], f"02_mortality_by_{var}")
    chi = descriptive.chi_square(df, s, var)
    tests.append({"variable": var, "p_global": chi["p_global"], "dof": chi["dof"]})
    if len(chi["pairwise"]):
        save_table(chi["pairwise"], s, f"02_pairwise_{var}")
save_table(pd.DataFrame(tests), s, "02_chi_square")

cells = descriptive.crosstab_mortality(df, s, "varroa_treatment", "winter_food")
save_table(cells, s, "02_mortality_treatment_x_feed")
figures.heatmap(cells, s, "mortality_pct", "02_heatmap_treatment_x_feed",
                "Observed winter loss by varroa treatment and winter feed")

for other in ["winter_food", "varroa_treatment"]:
    save_table(descriptive.composition(df, "imker_methode", other), s,
               f"02_method_x_{other}_share", index=True)

print(f"Tables: {s.tables_dir}\nFigures: {s.figures_dir}")
