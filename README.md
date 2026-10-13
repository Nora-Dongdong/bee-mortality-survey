# bee-mortality-survey

This project is my research work for Stichting Bee Foundation, where I used causal inference to analyze the cause of higher hive mortality. 
The study lasts 2 years: beekeeping year 2024-2025 and 2025-2026.
Key features I look at include several beekeeping practices (winter food, varroa treatment, and beekeeping method), mites existance, and surrounding environment (biodiversity and toxicity).


## Structure

```
bee-mortality-survey/
├── data/
│   ├── raw/          survey export and landscape files (not in the repo: contains personal data)
│   ├── processed/    cleaned data written by notebook 01
│   └── README.md     columns, answer codes and landscape inputs
├── notebooks/
│   ├── 01_data_cleaning.ipynb             raw survey -> data/processed/
│   ├── 02_descriptive_stats.ipynb         loss rates per answer, chi-square tests, heatmap
│   ├── 03_regression_models.ipynb         GEE Models 1-4, weighting check, predicted loss
│   ├── 04_landscape_feature.ipynb         toxicity and crop diversity index per apiary (500 m, 1000 m)
│   └── 05_gee_toxicity_diversity.ipynb    GEE models of the two indices vs winter loss
├── analysis_results/ tables (CSV, HTML) written by the notebooks, prefixed by notebook number
├── plots/            charts (PNG) written by the notebooks, prefixed by notebook number
├── reports/
│   ├── 2024-2025/    reports and presentation for beekeeping year 2024-2025
│   └── 2025-2026/    reports and presentation for beekeeping year 2025-2026
├── archive/          original notebooks (july 2026), kept for reference
└── requirements.txt
```

## How to run

1. Put the survey file in `data/raw/` (file name is set at the top of notebook 01).
   For notebook 04, also put `output_2025_dot.csv` and `land_types.csv` in `data/raw/`.
2. `pip install -r requirements.txt`
3. Open the notebooks in order and run all cells: 01, 02, 03, then 04 and 05
   (05 reads the index tables that 04 writes to `analysis_results/`).

## Method in short

- Main question: Which beekeeping methods and environmental factors contribute to hive mortality?
- Winter loss = (colonies in autumn 2025 - colonies in spring 2026) / colonies in autumn 2025.
  Group rates are hive-weighted: total deaths / total colonies.
- Exclusion rules are in notebook 01 and each one prints how many apiaries it removes.
- Regression: binomial GEE, one row per colony, clustered by beekeeper.
  Reference groups: controlled method, honey + sugar feed, alternative full varroa treatment.
  Notebook 03 also refits the models with every apiary weighted equally, as in the July 2026 report.

## Data

Data source: self-report survey from Dutch beekeepers
Raw data is not open access. Names, contact details, addresses, coordinates and open-text answers
are removed in the dataset.
