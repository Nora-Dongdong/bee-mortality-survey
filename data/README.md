# Data

`raw/` holds the original survey exports. They contain names, e-mail addresses
and coordinates, are ignored by git, and must never be committed.

## How to run

```
python scripts/01_cleaning.py      # survey CSV -> data/processed/2025-2026_survey_clean.csv
python scripts/02_descriptive.py   # tables/2025-2026/02_*, figures/2025-2026/02_*
python scripts/03_models.py        # tables/2025-2026/03_*, figures/2025-2026/03_*
```

Step 1 reads the survey file set in `src/beesurvey/config.py` (or `--data path`),
keeps only coded answer columns (open-text answers and stray columns are dropped)
and refuses anything that looks like personal data. Its output in `processed/`
is git-ignored until we decide to publish a de-identified dataset.

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
| `outside_nl` (optional) | 1 if the apiary lies outside the Netherlands |

Open-text answers are coded into the numeric columns before de-identification;
the coding rules are in the 2026 key-conclusions report appendix.

Death count: `deaths = 2025_winter_in - 2026_winter_uit` everywhere. The run
writes `tables/<season>/01_death_definition_mismatches.csv` listing apiaries
where this differs from `2025_winter_dood`.
