# bee-mortality-survey

Data analysis for Stichting Bee Foundation: a survey of Dutch beekeepers on winter colony
losses, used to find which beekeeping practices go together with higher losses.

## Structure

```
bee-mortality-survey/
├── data/
│   ├── raw/          survey export (not in the repo: contains personal data)
│   ├── processed/    cleaned data written by notebook 01 (not in the repo)
│   └── README.md     columns and answer codes
├── notebooks/        run in order; each one runs on its own
│   ├── 01_data_cleaning.ipynb       raw survey -> data/processed/
│   ├── 02_descriptive_stats.ipynb   loss rates per answer, chi-square tests, heatmap
│   └── 03_regression_models.ipynb   GEE Models 1-4, weighting check, predicted loss
├── results/          tables (CSV) written by the notebooks, prefixed by notebook number
├── plots/            charts (PNG) written by the notebooks, prefixed by notebook number
├── outputs/          reports and presentations
├── archive/          the July 2026 notebooks, kept for reference
└── requirements.txt
```

## How to run

1. Put the survey file in `data/raw/` (file name is set at the top of notebook 01).
2. `pip install -r requirements.txt`
3. Open the notebooks in order and run all cells: 01, then 02 and 03.

## Method in short

- Winter loss = (colonies in autumn 2025 - colonies in spring 2026) / colonies in autumn 2025.
  Group rates are hive-weighted: total deaths / total colonies.
- Exclusion rules are in notebook 01 and each one prints how many apiaries it removes.
- Regression: binomial GEE, one row per colony, clustered by beekeeper, robust standard errors.
  Reference groups: controlled method, honey + sugar feed, alternative full varroa treatment.
  Notebook 03 also refits the models with every apiary weighted equally, as in the July 2026 report.

## Data

Raw data is not open access. Names, contact details, addresses, coordinates and open-text answers
are removed in notebook 01 before anything is saved.
