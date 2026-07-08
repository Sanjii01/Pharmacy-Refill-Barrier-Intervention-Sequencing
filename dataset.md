# Pharmacy Refill Barrier Intervention Sequencing Dataset

## Overview

This dataset contains privacy-preserving pharmacy refill workflow cases. Each row represents one anonymized refill barrier case with a short case note and four candidate intervention cards, labeled A through D. The goal is to order the intervention cards from highest to lowest operational priority.

The data was generated locally using the included `generate_raw.py` script with a fixed random seed. The generator creates realistic refill-access situations involving prescriber renewal, clinical clarification, benefits review, stock gaps, cold-chain delivery, affordability support, adherence counseling, contact verification, and lab-monitoring follow-up. No real patient names, dates of birth, prescription numbers, drug names, plan identifiers, phone numbers, addresses, or pharmacy account IDs are included.

## Raw File Structure

The raw dataset upload contains exactly these top-level files:

| File | Description |
|---|---|
| `data.csv` | Public-safe raw generated refill cases. Each row contains only `raw_case_id`, public context fields, a case note, four intervention cards, and `action_count`; it does not contain `intervention_plan`, `priority_score_*`, private group labels, or prepared test answers. |
| `generate_raw.py` | Deterministic Python script that generates the public-safe `data.csv` from a fixed random seed and documents the refill-barrier vocabularies used by the benchmark. |

The Eris `prepare.py` script is supplied separately in the challenge editor. It transforms the raw upload into public and private prepared files, creates labeled training rows, and keeps held-out answer rows private.

## Public Prepared Files

| File | Description |
|---|---|
| `train.csv` | 4,800 labeled refill cases with public context columns, case note, action cards, and `intervention_plan`. |
| `test.csv` | 1,500 held-out refill cases with the same public context columns, without `intervention_plan`. |
| `sample_submission.csv` | Example submission with every test `case_id` and valid JSON plan strings. |

## Public Columns

| Column | Type | Present In | Description |
|---|---|---|---|
| `case_id` | string | train, test, submission | Hashed refill case identifier. |
| `pharmacy_setting` | string | train, test | Workflow setting, such as retail chain counter, independent pharmacy, specialty pharmacy queue, mail-order center, hospital discharge desk, or rural delivery route. |
| `medication_context` | string | train, test | Coarse medication context such as anticoagulant, insulin, transplant immunosuppressant, seizure control, heart failure, asthma controller, oncology support, antibiotic course, hypertension, dermatology, migraine, or fertility support. |
| `case_note` | string | train, test | Natural-language note describing refill gap, remaining supply, outreach attempts, coordination context, and barrier clues. |
| `action_cards` | string | train, test | JSON list of four candidate intervention cards. Each card has `action_id` A-D and an `action_text` describing a possible next step. |
| `action_count` | integer | train, test | Number of candidate actions. This is always 4 because every row contains exactly four possible intervention cards; the column is included only for schema consistency and should not be used as a ranking signal. |
| `intervention_plan` | string | train only, submission | JSON object with `ordered_actions`, a list of A, B, C, and D ordered from highest to lowest operational priority. |

## Hidden Columns In Private Data

| Column | Type | Description |
|---|---|---|
| `priority_score_A`, `priority_score_B`, `priority_score_C`, `priority_score_D` | float | Hidden operational priority score for each candidate action. Higher scores should appear earlier in `ordered_actions`. |
| `primary_barrier` | string | Main blocker family for the case, such as clinical safety, no refills, prior authorization, stock gap, cold chain, affordability, side effects, contact issue, or lab monitoring. |
| `risk_band` | string | Coarse medication risk band derived from medication context. |
| `difficulty_tier` | string | Generator difficulty bucket: easy, medium, or hard. |
| `days_gap_band` | string | Coarse refill-gap timing bucket: current, watch, or late. |

## Data Characteristics

The benchmark is designed to require comparative reasoning over the case note and all four action cards. A high-priority action may be clinical clarification, prescriber renewal, payer review, inventory resolution, cold-chain coordination, affordability support, adherence counseling, contact verification, or lab follow-up depending on the note. Some cases contain multiple real blockers, and the held-out split emphasizes harder cases with close action priorities.

The private score includes a hidden robustness term over primary barrier, medication risk, difficulty tier, and refill-gap groups. These hidden columns are produced only inside the private prepared answers file; they are not included in the public source repository or public test rows. This discourages solutions that only learn one common barrier pattern.

## License And Source

The dataset is synthetic and generated locally for this benchmark. It may be released under CC0 1.0 Public Domain. Use a public GitHub repository containing only the public-safe `generate_raw.py` and `data.csv` source files as the source URL. Do not publish prepared private answers, held-out `intervention_plan` values, `priority_score_*` columns, or private group labels in the source repository.
