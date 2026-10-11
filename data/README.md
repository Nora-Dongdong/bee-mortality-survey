# Data

`raw/` holds the original survey exports. They contain names, e-mail addresses
and coordinates, are ignored by git, and must never be committed.

`processed/<season>_survey_deidentified.csv` is the only file the analysis reads
(path set in `src/beesurvey/config.py`). `cleaning.load()` refuses a file that
has a column that looks like personal data or free text.

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

Landscape indices (crop diversity, toxicity) are a separate table without
coordinates: `id_location, radius_m, crop_diversity_index, toxicity_index`.

Death count: `deaths = 2025_winter_in - 2026_winter_uit` everywhere. The run
writes `tables/<season>/01_death_definition_mismatches.csv` listing apiaries
where this differs from `2025_winter_dood`.
