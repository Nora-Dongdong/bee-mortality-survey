# bee-mortality-survey
Data analysis project I did for Stichting Bee Foundation. Analyzed survey from beekeepers and identified high-risk beekeeping practices.

Custom utility functions for data consistency and cleaning are maintained in src/core_tools.py to ensure reproducibility across different survey years.

Data Source: 
...All the information regarding name, address, contact information, and location has been taken away.

Methodology: ..+GEE (Generalized Estimating Equations) 

Future plans: This repository is designed to evolve into a 4-year longitudinal analysis of bee mortality (2022-2026).

Installation

How to run:

Directory Tree:
```plaintext
/bee-mortality-analysis
│
├── data/               
│   ├── raw/             # raw data, won't be public access
│   │   ├── 2022/
│   │   ├── 2023/
│   │   ├── 2024/
│   │   ├── 2025/
│   │   └── 2026/       
│   └── processed/       # data after cleansing, dropping any personal information
│
├── notebooks/           # Jupyter Notebook
│   ├── annual_eda/      # analysis for single year dataset
│   └── cross_year/      # longitudinal analysis
│
├── src/                 # (eg.core_tools.py)
│   ├── cleaning.py      # functions for data cleaning and consistency
│   └── visualization.py # functions for data visualization
│
├── outputs/             # graphs and models
│   └── figures/
│
├── README.md           
├── requirements.txt    
└── .gitignore          
```
