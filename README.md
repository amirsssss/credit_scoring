# CreditScoring

Credit scoring from phone data: call and SMS records (CDR), app usage (Instagram, Telegram,
launcher time, unlock counts, games …) and internet package purchases.

The model estimates each applicant's **probability of default (PD)** on the date a credit
decision is made, and turns it into a points-based score with reason codes.

> **Status:** scaffold only. No data loaded yet.
> **Blocking question:** which repayment outcomes do we have? See [Labels](#labels).

## Why this can work

Peer-reviewed evidence that phone data predicts repayment:

- **Björkegren & Grissen (2020), *World Bank Economic Review*.** Call records matched to repayment
  of credit from a South American telecom. For thin-file borrowers the phone-data model beat a
  credit-bureau model, and it also scored people with no credit history at all.
- **Óskarsdóttir et al. (2019), *Applied Soft Computing*.** Call-record and call-network features
  improved both AUC and profit over traditional data.
- **Berg et al. (2020), *Review of Financial Studies*.** A few simple digital-footprint variables
  predicted default as well as a credit-bureau score; the two worked best combined.

Realistic target: **AUC around 0.7**. The score matters most for a borrower's first loan; after a
few repayments, their own repayment history becomes the stronger signal.

## Data

Tables and columns are specified in [docs/data_contract.md](docs/data_contract.md).

- Calls and SMS (metadata only)
- App usage per app per day, and device activity (unlocks, screen time)
- Internet package purchases and top-ups
- Loan outcomes: the labels

## Labels

The behavioral data are inputs. A credit score predicts default, so it has to be trained and
validated on people whose repayment outcome is known. Possible sources:

1. **Credit already extended:** postpaid bills, emergency airtime/data credit, device installments.
2. **A partner lender** (bank, BNPL, microlender) with outcomes for some of our users, matched with consent.
3. **A pilot:** small loans to a broad sample, accepting early losses as the cost of the data.

Target size: a few thousand loans with at least a few hundred defaults (1,000+ for a robust model).
The number of defaults matters more than the total.

Default definitions (`label` in [configs/default.yaml](configs/default.yaml)):

| Credit type | Bad when | Function |
|---|---|---|
| Single payment (emergency credit, short microloans) | not fully repaid within `dpd_threshold` days (default 30) of the due date | `labels.label_single_payment` |
| Installments | days past due reaches `dpd_threshold` (usually 90) within `performance_days` (usually 365) of the decision | `labels.label_from_dpd_snapshots` |

Loans whose outcome isn't known yet are **immature**: they get no label and are left out of training.

## Timeline: no data from the future

```
      observation window (features)           performance window (label)
  |<-------- observation_days -------->|<--------- performance_days --------->|
                                       ^
                                 decision date
```

- Features use only events **before** the decision date (`pit.events_in_window`). Events on the
  decision day itself are excluded, because a date alone can't say whether they came first.
- Labels use only what happened **after** it.
- Leakage is the most common way projects like this fake good results. Defaulters often go quiet or
  switch SIM, so a feature like "inactive last month" leaks the answer. If AUC comes out above about
  0.85, look for leakage before celebrating.

## Features to try

| Source | Features |
|---|---|
| Package purchases (often the strongest) | spend level and 3-month trend · regularity (variation in days between purchases) · small daily vs. monthly packages · days without an active package · purchases around paydays |
| Calls / SMS | SIM tenure · active days per month · incoming/outgoing ratio · unique contacts, share who call back, contact turnover · night and weekend share · SMS from bank short codes (counts only) |
| App usage | banking and payment apps · lending and betting apps (usually risk signals) · time share by category · launcher (Home UI) time |
| Device | unlocks per day · night-time use · regularity of daily routine · device price tier and age |

All of these are hypotheses; keep only what holds up on out-of-time data.

## Modeling

1. **Baseline, a scorecard:** WoE-binned logistic regression with `optbinning`. Easy to explain,
   gives reason codes for declines, stable on a few thousand loans.
2. **Challenger, gradient boosting:** LightGBM with monotonic constraints, explained with SHAP.
   Kept only if it beats the scorecard out-of-time.
3. **Score scaling:** `score = offset + factor × ln(good:bad odds)` with `factor = pdo / ln 2`.
   Default: 600 points at 50:1 odds, 20 points to double the odds.

## Validation

- **Out-of-time:** train on older decisions, test on newer ones (`split` in the config).
- **Ranking:** AUC, Gini and KS (`metrics.discrimination`).
- **Calibration:** predicted vs. observed default rate by decile (`metrics.calibration_table`).
- **Business view:** default rate at each approval rate.
- **Stability:** PSI between the training population and recent applicants (`metrics.psi`).

## Deployment and monitoring

- Small first limits that grow with good repayment.
- Monthly PSI on the score and the top features; retrain on drift or falling performance.
- Approve a small random slice of applicants the model would decline. Otherwise outcomes only ever
  exist for approved people, and the model can't learn about anyone else.

## Pitfalls specific to this data

- **Inflation and tariff changes:** nominal spend rises with prices. Use within-month percentiles or ratios.
- **Outside shocks:** app blocking or unblocking, internet shutdowns, and OS updates that change usage
  stats can shift features overnight.
- **Multi-SIM and recycled numbers:** low activity may just mean a secondary SIM, and a reassigned number
  carries the previous owner's history. Use subscriber identity and the current owner's activation date.
- **Gaming:** easy-to-fake signals ("has a banking app") stop working once people learn them. Prefer
  long-history behavior that is costly to fake.

## Legal and ethics checklist

- [ ] Users consented to their usage data being used for credit decisions.
- [ ] Local rules on credit scoring and alternative data are checked. (For reference: the EU AI Act
      treats credit scoring as high-risk; Google Play and India's RBI restrict lending apps from
      reading call logs and contacts.)
- [ ] If scores will be sold to lenders, check whether that needs a credit-bureau license.
- [ ] Approval and default rates compared across age and gender groups; proxy features removed.
- [ ] Aggregates only: no message content, hashed identifiers, no "your contacts defaulted" features.
- [ ] Every decline can be explained with reason codes.
- [ ] Notebook outputs stripped before committing (`nbstripout --install`).

## Project layout

```
CreditScoring/
├── configs/default.yaml     windows, default definition, split dates, score scaling
├── data/                    never committed (personal data)
│   ├── raw/                 exports, in the format of docs/data_contract.md
│   ├── interim/             cleaned tables
│   └── processed/           one row per decision: features + label
├── docs/data_contract.md    expected tables and columns
├── models/                  trained models (not committed)
├── notebooks/               exploration
├── reports/                 validation reports (not committed)
├── src/creditscoring/
│   ├── config.py            loads configs/default.yaml
│   ├── pit.py               point-in-time feature windows (leakage guard)
│   ├── labels.py            good / bad / immature labels
│   ├── metrics.py           AUC, Gini, KS, calibration, PSI
│   └── features/            one module per source, added once the schema is known
└── tests/
```

## Getting started

Needs Python 3.10 or newer.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
pytest
```

## Open questions

1. Which repayment outcomes exist, for how many users, with how many defaults?
2. How many months of history does each source cover?
3. Which key links a subscriber to a borrower (hashed national ID, customer ID)?
4. Prepaid, postpaid, or both?
5. Which decision will the score drive (product, amount, tenor), and who lends?
6. Which country's lending and data-protection rules apply?
