"""Fast data-contract checks that can run before model training."""

from __future__ import annotations

import json

import pandas as pd

from src.config import OUTPUT_DIR, RAW_DIR


def main() -> dict:
    customers = pd.read_csv(RAW_DIR / "customers.csv.gz")
    activity = pd.read_csv(RAW_DIR / "monthly_activity.csv.gz")
    experiment = pd.read_csv(RAW_DIR / "retention_experiment.csv.gz")
    checks = {
        "customer_id_unique": bool(customers["customer_id"].is_unique),
        "customer_id_not_null": bool(customers["customer_id"].notna().all()),
        "customer_month_unique": bool(
            ~activity.duplicated(["customer_id", "activity_month"]).any()
        ),
        "non_negative_transactions": bool((activity["financial_txn_count"] >= 0).all()),
        "non_negative_balance": bool((activity["avg_balance"] >= 0).all()),
        "activity_has_valid_customer": bool(
            set(activity["customer_id"]).issubset(set(customers["customer_id"]))
        ),
        "experiment_has_control": bool((experiment["action"] == "controle").any()),
        "experiment_binary_outcome": bool(set(experiment["retained_60d"]).issubset({0, 1})),
    }
    report = {
        "status": "passed" if all(checks.values()) else "failed",
        "checks": checks,
        "rows": {
            "customers": int(len(customers)),
            "monthly_activity": int(len(activity)),
            "retention_experiment": int(len(experiment)),
        },
    }
    (OUTPUT_DIR / "data_quality_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    if report["status"] != "passed":
        failed = [name for name, passed in checks.items() if not passed]
        raise ValueError(f"Data contract failed: {failed}")
    return report


if __name__ == "__main__":
    print(json.dumps(main(), ensure_ascii=False, indent=2))
