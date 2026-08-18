"""Create leakage-safe feature snapshots and the 60-day churn target."""

from __future__ import annotations

import pandas as pd
import numpy as np

from src.config import PROCESSED_DIR, RAW_DIR, SNAPSHOT_MONTHS


def _safe_ratio_change(current: pd.Series, reference: pd.Series) -> pd.Series:
    return ((current - reference) / reference.replace(0, np.nan)).clip(-2, 2).fillna(0)


def build_snapshot(
    snapshot_month: str,
    customers: pd.DataFrame,
    activity: pd.DataFrame,
    support: pd.DataFrame,
) -> pd.DataFrame:
    snapshot = pd.Timestamp(snapshot_month)
    history_start = snapshot - pd.DateOffset(months=2)
    future_end = snapshot + pd.DateOffset(months=2)

    hist = activity[
        activity["activity_month"].between(history_start, snapshot, inclusive="both")
    ].copy()
    current = activity[activity["activity_month"] == snapshot].copy()
    prev = activity[
        activity["activity_month"].between(history_start, snapshot - pd.DateOffset(months=1))
    ].copy()
    future = activity[
        activity["activity_month"].between(
            snapshot + pd.DateOffset(months=1), future_end, inclusive="both"
        )
    ].copy()

    aggregate = hist.groupby("customer_id", as_index=False).agg(
        avg_balance_3m=("avg_balance", "mean"),
        avg_app_sessions_3m=("app_sessions", "mean"),
        sum_pix_in_3m=("pix_in_count", "sum"),
        sum_pix_out_3m=("pix_out_count", "sum"),
        sum_card_purchases_3m=("card_purchase_count", "sum"),
        sum_bill_payments_3m=("bill_payment_count", "sum"),
        sum_financial_txn_3m=("financial_txn_count", "sum"),
        sum_failed_txn_3m=("failed_txn_count", "sum"),
        salary_inflow_months_3m=("salary_inflow", "sum"),
        contact_pressure_30d=("contact_pressure_30d", "max"),
    )
    current_cols = current[
        [
            "customer_id",
            "financial_txn_count",
            "app_sessions",
            "avg_balance",
            "days_since_last_activity",
        ]
    ].rename(
        columns={
            "financial_txn_count": "current_financial_txn",
            "app_sessions": "current_app_sessions",
            "avg_balance": "current_balance",
        }
    )
    prev_agg = prev.groupby("customer_id", as_index=False).agg(
        prev_avg_financial_txn=("financial_txn_count", "mean"),
        prev_avg_app_sessions=("app_sessions", "mean"),
        prev_avg_balance=("avg_balance", "mean"),
    )
    future_target = future.groupby("customer_id", as_index=False).agg(
        future_max_inactivity=("days_since_last_activity", "max"),
        future_total_txn=("financial_txn_count", "sum"),
    )
    future_target["churn_60d"] = (
        (future_target["future_max_inactivity"] >= 60)
        & (future_target["future_total_txn"] <= 1)
    ).astype(int)

    support_hist = support[
        support["ticket_month"].between(history_start, snapshot, inclusive="both")
    ]
    support_agg = support_hist.groupby("customer_id", as_index=False).agg(
        support_tickets_3m=("ticket_count", "sum"),
        unresolved_tickets_3m=("unresolved_count", "sum"),
        avg_nps_3m=("nps", "mean"),
    )

    frame = (
        customers.merge(aggregate, on="customer_id", how="inner")
        .merge(current_cols, on="customer_id", how="inner")
        .merge(prev_agg, on="customer_id", how="left")
        .merge(future_target[["customer_id", "churn_60d"]], on="customer_id", how="inner")
        .merge(support_agg, on="customer_id", how="left")
    )
    frame["support_tickets_3m"] = frame["support_tickets_3m"].fillna(0)
    frame["unresolved_tickets_3m"] = frame["unresolved_tickets_3m"].fillna(0)
    frame["avg_nps_3m"] = frame["avg_nps_3m"].fillna(8.0)
    frame["txn_trend_3m"] = _safe_ratio_change(
        frame["current_financial_txn"], frame["prev_avg_financial_txn"]
    )
    frame["sessions_trend_3m"] = _safe_ratio_change(
        frame["current_app_sessions"], frame["prev_avg_app_sessions"]
    )
    frame["balance_trend_3m"] = _safe_ratio_change(
        frame["current_balance"], frame["prev_avg_balance"]
    )
    frame["tenure_months"] = (
        (snapshot.year - frame["signup_date"].dt.year) * 12
        + snapshot.month
        - frame["signup_date"].dt.month
    ).clip(lower=1)
    frame["snapshot_month"] = snapshot
    frame["annual_value_at_risk"] = frame["monthly_contribution_margin"] * 12
    return frame


def main() -> pd.DataFrame:
    customers = pd.read_csv(
        RAW_DIR / "customers.csv.gz",
        parse_dates=["signup_date", "churn_month_synthetic"],
    )
    activity = pd.read_csv(RAW_DIR / "monthly_activity.csv.gz", parse_dates=["activity_month"])
    support = pd.read_csv(RAW_DIR / "support_tickets.csv.gz", parse_dates=["ticket_month"])
    frames = [build_snapshot(month, customers, activity, support) for month in SNAPSHOT_MONTHS]
    features = pd.concat(frames, ignore_index=True)
    features.to_csv(PROCESSED_DIR / "feature_snapshots.csv.gz", index=False, compression="gzip")
    return features


if __name__ == "__main__":
    result = main()
    print(f"Feature snapshots: {len(result):,} rows | churn rate: {result.churn_60d.mean():.2%}")

