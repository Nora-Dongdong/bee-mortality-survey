"""Step 1: clean the survey file.

    python scripts/01_cleaning.py [season] [--data path/to/survey.csv]

Keeps only coded answer columns, applies every exclusion rule in
beesurvey.cleaning.RULES, and writes data/processed/<season>_survey_clean.csv,
which steps 2 and 3 read.
"""
from _common import cleaning, parse_args, save_table

args, s = parse_args(__doc__, with_data=True)

raw = cleaning.load(s, args.data)
df, log = cleaning.clean(raw, s)

s.clean_file.parent.mkdir(parents=True, exist_ok=True)
cleaning.assert_no_pii(df)
df.to_csv(s.clean_file, index=False)

save_table(log, s, "01_cleaning_log")
save_table(cleaning.missing_report(df, s), s, "01_valid_n_per_variable")
check = cleaning.death_definition_check(df, s)
save_table(check, s, "01_death_definition_mismatches")

print(log.to_string(index=False))
print(f"\nin - uit differs from reported dead colonies in {len(check)} of {len(df)} apiaries")
print(f"Clean file: {s.clean_file}")
