from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
MODEL_DIR = ROOT / "models"
OUTPUT_DIR = ROOT / "outputs"

RANDOM_SEED = 42
N_CUSTOMERS = 50_000
FIRST_MONTH = "2024-08-01"
LAST_MONTH = "2026-07-01"
SNAPSHOT_MONTHS = [
    "2026-01-01",
    "2026-02-01",
    "2026-03-01",
    "2026-04-01",
    "2026-05-01",
]

MODEL_FEATURES = [
    "tenure_months",
    "products_count",
    "has_credit_card",
    "has_personal_loan",
    "credit_limit",
    "avg_balance_3m",
    "avg_app_sessions_3m",
    "sum_pix_in_3m",
    "sum_pix_out_3m",
    "sum_card_purchases_3m",
    "sum_bill_payments_3m",
    "sum_financial_txn_3m",
    "sum_failed_txn_3m",
    "salary_inflow_months_3m",
    "support_tickets_3m",
    "unresolved_tickets_3m",
    "avg_nps_3m",
    "txn_trend_3m",
    "sessions_trend_3m",
    "balance_trend_3m",
    "contact_pressure_30d",
    "monthly_contribution_margin",
]

for directory in [RAW_DIR, PROCESSED_DIR, MODEL_DIR, OUTPUT_DIR]:
    directory.mkdir(parents=True, exist_ok=True)
