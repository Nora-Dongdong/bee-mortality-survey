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
/bee-mortality-analysis
│
├── data/               # 建议在 .gitignore 里忽略此文件夹，只在本地保存
│   ├── raw/            # 原始数据，永远不要修改
│   │   ├── 2022/
│   │   ├── 2023/
│   │   ├── 2024/
│   │   ├── 2025/
│   │   └── 2026/       # 你现在的数据放在这里
│   └── processed/      # 清洗后、用于建模的数据
│
├── notebooks/          # 所有的 Jupyter Notebook
│   ├── annual_eda/     # 每年的探索性分析
│   └── cross_year/     # 跨年份的一致化分析（你未来的重心）
│
├── src/                # 存放通用的 Python 脚本 (如 core_tools.py)
│   ├── cleaning.py     # 专门负责清洗和一致化的函数
│   └── visualization.py
│
├── outputs/            # 存放生成的图表和报告
│   └── figures/
│
├── README.md           # 项目总览
├── requirements.txt    # 依赖库清单
└── .gitignore          # 忽略 Data/ 和 __pycache__/
