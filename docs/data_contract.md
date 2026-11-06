# Data contract

What the pipeline expects in `data/raw/`. Map your exports onto these tables. Extra columns are fine;
a missing optional column just disables the features that need it.

## General rules

- **Format:** Parquet preferred, UTF-8 CSV accepted. One folder per table and one file per month,
  e.g. `data/raw/calls/2026-01.parquet`.
- **Time:** one local time zone for every table, ISO 8601 (`2026-01-31 14:05:00`).
- **History:** at least `observation_days` (default 180) before the earliest decision, plus enough
  after the latest one for its outcome to mature. In practice, 18–24 months.
- **Privacy:** no message content, names or raw phone numbers. Hash personal identifiers with a keyed
  hash (HMAC-SHA256) *before* the data reaches this folder, and keep the key outside the project.
  Service short codes and sender names (banks, operators) aren't personal and can stay readable.

## Identifiers

| Column | Meaning |
|---|---|
| `subscriber_id` | Pseudonymous ID for one person on one SIM. Must change when a number is reassigned to a new owner. |
| `counterparty` | The other party: hashed if it's a personal number, readable if it's a short code or sender name. |
| `loan_id` | One credit decision. |

## Tables

### `subscribers`: one row per subscriber

| Column | Type | Required | Notes |
|---|---|---|---|
| `subscriber_id` | string | yes | |
| `activation_date` | date | yes | When the current owner got the SIM: gives tenure and guards against recycled numbers |
| `plan_type` | string | yes | `prepaid` or `postpaid` |
| `person_key` | string | no | Hashed national ID or customer ID for matching lender outcomes; both sides must use the same hash key |

### `calls`: one row per call

| Column | Type | Required | Notes |
|---|---|---|---|
| `subscriber_id` | string | yes | |
| `event_ts` | datetime | yes | Call start |
| `direction` | string | yes | `in` or `out` |
| `counterparty` | string | yes | |
| `duration_sec` | int | yes | 0 for missed or unanswered calls |

### `sms`: one row per message, metadata only

| Column | Type | Required | Notes |
|---|---|---|---|
| `subscriber_id` | string | yes | |
| `event_ts` | datetime | yes | |
| `direction` | string | yes | `in` or `out` |
| `counterparty` | string | yes | |
| `counterparty_kind` | string | no | `person` or `service` (banks, operators, apps) |

### `app_usage_daily`: one row per subscriber, day and app

| Column | Type | Required | Notes |
|---|---|---|---|
| `subscriber_id` | string | yes | |
| `date` | date | yes | |
| `app` | string | yes | Package name, e.g. `org.telegram.messenger`; the launcher (Home UI) is an app too |
| `category` | string | no | `social`, `messaging`, `games`, `finance`, `lending`, `betting`, `shopping`, `productivity`, `other` |
| `foreground_sec` | int | yes | Time on screen |
| `launches` | int | no | |

### `device_daily`: one row per subscriber and day

| Column | Type | Required | Notes |
|---|---|---|---|
| `subscriber_id` | string | yes | |
| `date` | date | yes | |
| `unlocks` | int | yes | |
| `screen_sec` | int | no | Total screen-on time |
| `night_screen_sec` | int | no | Screen-on time between 00:00 and 06:00 |
| `device_model` | string | no | For device price tier and age |

### `purchases`: one row per package purchase or top-up

| Column | Type | Required | Notes |
|---|---|---|---|
| `subscriber_id` | string | yes | |
| `purchase_ts` | datetime | yes | |
| `product_type` | string | yes | `data_package`, `airtime`, `bundle`, … |
| `price` | number | yes | Local currency, as charged |
| `validity_days` | int | for packages | Needed for "days without an active package" |
| `volume_mb` | number | for packages | |
| `channel` | string | no | USSD, operator app, bank app, card, … |

### `loans`: one row per credit decision (the labels)

| Column | Type | Required | Notes |
|---|---|---|---|
| `loan_id` | string | yes | |
| `subscriber_id` | string | yes | |
| `decision_date` | date | yes | Date the credit was granted |
| `amount` | number | yes | |
| `product` | string | yes | e.g. `emergency_credit`, `microloan`, `installment` |
| `due_date` | date | single payment | Final due date |
| `repaid_date` | date | single payment | Date fully repaid; empty while unpaid |

### `dpd_snapshots`: installment loans only

| Column | Type | Required | Notes |
|---|---|---|---|
| `loan_id` | string | yes | |
| `snapshot_date` | date | yes | e.g. each month end |
| `dpd` | int | yes | Days past due on that date |
