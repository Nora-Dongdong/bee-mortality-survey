# Data

`raw/` holds the survey export. It contains personal data and open-text answers,
is ignored by git, and must never be committed.

`processed/2025-2026_survey_clean.csv` is written by `notebooks/01_data_cleaning.ipynb`
and contains only the coded columns below. It is also git-ignored for now.

## Columns the analysis expects (2025-2026)

| Column | Meaning |
| --- | --- |
| `id_location` | apiary id (one row per apiary) |
| `id_beekeeper` | beekeeper id, used to cluster apiaries in the GEE models |
| `2025_winter_in` | colonies going into winter (autumn 2025) |
| `2026_winter_uit` | colonies alive in spring 2026 |
| `2025_winter_dood` | colonies the beekeeper reported as dead (used only as a check) |
| `imker_methode` | 1 Controlled, 2 Natural, 3 Regulier, 4 Unknown / mixed |
| `winter_food` | 1 Sugar only, 2 Honey + sugar, 3 Honey only |
| `varroa_treatment` | 1 Full 3-step, 2 Alternative full, 3 Winter only, 4 Summer only, 5 None |
| `varroa_observation`, `aziatische_hoornaar`, `deformed_wings` | 1 Nee, 2 Weinig, 3 Matig, 4 Veel, 5 Weet niet |
| `province`, `bijenstanden_count`, `honingdracht_*`, `stuifmeel_*` | kept for later analyses |

Open-text answers are coded into the numeric columns before de-identification;
the coding rules are in the 2026 key-conclusions report appendix.

Death count: `deaths = 2025_winter_in - 2026_winter_uit` everywhere. Notebook 01
writes `analysis_results/01_death_definition_mismatches.csv` listing apiaries where this
differs from `2025_winter_dood`.

## Landscape inputs (notebook 04)

Also in `raw/` (git-ignored):

| File | Content |
| --- | --- |
| `output_2025_dot.csv` | land-use share per apiary (`id_location`) and buffer radius (`straal_m`, 500 or 1000 m) |
| `land_types.csv` | foraging factor (0/1) and pesticide factor per land-use type |

These files hold no coordinates. Landscape data cover 423 of the 828 apiaries.
