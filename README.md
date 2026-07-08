# Pharmacy Refill Barrier Intervention Sequencing

Eris NLP challenge package. Solvers read anonymized pharmacy refill case notes and submit a JSON ordering of four intervention cards from highest to lowest operational priority.

Files:

- `dataset.md` - dataset editor description
- `problem.md` - problem editor description
- `prepare.py` - deterministic public/private split
- `grade.py` - 0-1 maximization grader
- `config.yaml` - Eris scoring config
- `rubrics.yaml` - task rubrics
- `raw/generate_raw.py` - deterministic generator
- `raw/data.csv` - public-safe generated raw data with no answer columns
- `pharmacy-refill-intervention-sequencing-raw.zip` - raw upload zip

For the public source URL, publish only `raw/generate_raw.py` and the regenerated `raw/data.csv`.
Do not publish `public/`, `private/`, prepared `answers.csv`, held-out `intervention_plan` values, or `priority_score_*` columns.
