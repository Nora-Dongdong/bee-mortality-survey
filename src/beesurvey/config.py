"""Season settings: file paths, column names, codebooks and model reference groups.

Everything that changes from one survey year to the next lives here, so the
analysis modules never hard-code a column name or a label.
"""
from dataclasses import dataclass, field
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parents[2]


# ------------------------------------------------------------------
# Codebooks (checked against row 2 of the raw survey CSV, 2026-10-11)
# ------------------------------------------------------------------
IMKER_METHODE = {1: "Controlled", 2: "Natural", 3: "Regulier", 4: "Unknown / mixed"}

WINTER_FOOD = {1: "Sugar only", 2: "Honey + sugar", 3: "Honey only"}

VARROA_TREATMENT = {
    1: "Full 3-step (3 gangenmenu)",
    2: "Alternative full treatment",
    3: "Winter only",
    4: "Summer only",
    5: "No treatment",
}

# Observation questions Q21/Q23/Q24: 1 = Nee (confirmed by Ming against the raw CSV).
OBSERVATION = {1: "Not seen", 2: "A few", 3: "Moderate", 4: "Many", 5: "Don't know"}

CODEBOOKS = {
    "imker_methode": IMKER_METHODE,
    "winter_food": WINTER_FOOD,
    "varroa_treatment": VARROA_TREATMENT,
    "varroa_observation": OBSERVATION,
    "aziatische_hoornaar": OBSERVATION,
    "deformed_wings": OBSERVATION,
}

# Plain-English names for chart titles and tables.
VARIABLE_LABELS = {
    "imker_methode": "Beekeeping method",
    "winter_food": "Winter feed",
    "varroa_treatment": "Varroa treatment",
    "varroa_observation": "Varroa seen",
    "aziatische_hoornaar": "Asian hornet seen",
    "deformed_wings": "Deformed wings seen",
}


@dataclass(frozen=True)
class Season:
    name: str
    data_file: Path
    hives_in: str
    hives_out: str
    hives_dead: str
    apiary_id: str = "id_location"
    beekeeper_id: str = "id_beekeeper"
    categorical: tuple = tuple(CODEBOOKS)
    # Reference groups for the GEE models (report section 4: controlled method,
    # honey + sugar feed, alternative full varroa treatment).
    reference: dict = field(default_factory=lambda: {
        "imker_methode": 1,
        "winter_food": 2,
        "varroa_treatment": 2,
    })
    alpha: float = 0.05
    min_apiaries_per_cell: int = 20

    @property
    def figures_dir(self) -> Path:
        return REPO_DIR / "figures" / self.name

    @property
    def clean_file(self) -> Path:
        """Output of scripts/01_cleaning.py, input of the other two scripts."""
        return REPO_DIR / "data" / "processed" / f"{self.name}_survey_clean.csv"

    @property
    def tables_dir(self) -> Path:
        return REPO_DIR / "tables" / self.name


SEASON_2025_2026 = Season(
    name="2025-2026",
    data_file=REPO_DIR / "data" / "raw" / "2026_surveydata_cleaned_exclude_gps.csv",
    hives_in="2025_winter_in",
    hives_out="2026_winter_uit",
    hives_dead="2025_winter_dood",
)

SEASONS = {s.name: s for s in [SEASON_2025_2026]}
