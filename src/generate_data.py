"""Generate a realistic, fully synthetic digital-bank data set.

The generator is deterministic: the same seed recreates the same portfolio.
No real person or confidential banking record is used.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd

from src.config import FIRST_MONTH, LAST_MONTH, N_CUSTOMERS, RANDOM_SEED, RAW_DIR


@dataclass
class DataManifest:
    seed: int
    customers: int
    monthly_rows: int
    support_rows: int
    experiment_rows: int
    first_month: str
    last_month: str
    synthetic: bool = True


STATES = [
    "SP", "RJ", "MG", "BA", "PR", "RS", "PE", "CE", "PA", "SC", "GO",
    "MA", "PB", "ES", "AM", "RN", "AL", "PI", "DF", "MS", "MT", "SE",
    "RO", "TO", "AC", "AP", "RR",
]
STATE_WEIGHTS = np.array([
    0.22, 0.11, 0.10, 0.07, 0.06, 0.05, 0.05, 0.04, 0.035, 0.035, 0.03,
    0.025, 0.025, 0.022, 0.022, 0.021, 0.018, 0.018, 0.017, 0.015, 0.015,
    0.012, 0.01, 0.008, 0.004, 0.003, 0.003,
])
STATE_WEIGHTS = STATE_WEIGHTS / STATE_WEIGHTS.sum()

ROOT_REASONS = [
    "baixo_engajamento",
    "perda_de_renda",
    "friccao_no_app",
    "falha_de_atendimento",
    "frustracao_com_credito",
    "pressao_financeira",
]


def sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def generate_customers(rng: np.random.Generator, n: int) -> pd.DataFrame:
    customer_id = np.arange(1, n + 1)
    signup_dates = pd.to_datetime(
        rng.choice(pd.date_range("2019-01-01", "2025-10-01", freq="D"), n)
    )
    income = np.clip(rng.lognormal(np.log(3_200), 0.68, n), 1_200, 35_000)
    age = np.clip(np.round(rng.normal(36, 11, n)), 18, 72).astype(int)
    acquisition = rng.choice(
        ["organico", "indicacao", "midia_paga", "parceria", "loja"],
        n,
        p=[0.30, 0.23, 0.24, 0.15, 0.08],
    )
    root_reason = rng.choice(ROOT_REASONS, n, p=[0.25, 0.15, 0.14, 0.14, 0.18, 0.14])
    digital_affinity = rng.beta(3.2, 2.0, n)
    has_credit_card = rng.binomial(1, sigmoid(-0.25 + 1.1 * digital_affinity))
    has_personal_loan = rng.binomial(1, sigmoid(-2.0 + income / 12_000))
    has_investment = rng.binomial(1, sigmoid(-2.5 + income / 7_000 + digital_affinity))
    credit_limit = np.where(
        has_credit_card == 1,
        np.clip(income * rng.uniform(0.35, 1.45, n), 300, 18_000),
        0,
    )
    products_count = 1 + has_credit_card + has_personal_loan + has_investment
    base_margin = np.clip(
        4 + 7 * has_credit_card + 11 * has_personal_loan + 3 * has_investment
        + income / 1_800 + rng.normal(0, 3, n),
        2,
        80,
    )

    latent_risk = (
        -2.1
        - 0.28 * (products_count - 1)
        - 0.50 * digital_affinity
        + 0.40 * (root_reason == "perda_de_renda")
        + 0.38 * (root_reason == "falha_de_atendimento")
        + 0.25 * (acquisition == "midia_paga")
        + rng.normal(0, 0.55, n)
    )
    will_churn = rng.binomial(1, sigmoid(latent_risk))
    possible_churn_months = pd.date_range("2025-09-01", LAST_MONTH, freq="MS")
    month_weights = np.linspace(0.55, 1.45, len(possible_churn_months))
    month_weights = month_weights / month_weights.sum()
    churn_month = np.full(n, np.datetime64("NaT"), dtype="datetime64[ns]")
    churn_month[will_churn == 1] = rng.choice(
        possible_churn_months.values,
        int(will_churn.sum()),
        p=month_weights,
    )

    return pd.DataFrame(
        {
            "customer_id": customer_id,
            "signup_date": signup_dates,
            "state": rng.choice(STATES, n, p=STATE_WEIGHTS),
            "age": age,
            "income": np.round(income, 2),
            "income_band": pd.cut(
                income,
                bins=[0, 2_000, 4_000, 8_000, 15_000, np.inf],
                labels=["ate_2k", "2k_a_4k", "4k_a_8k", "8k_a_15k", "acima_15k"],
            ).astype(str),
            "acquisition_channel": acquisition,
            "digital_affinity": np.round(digital_affinity, 4),
            "has_credit_card": has_credit_card,
            "has_personal_loan": has_personal_loan,
            "has_investment": has_investment,
            "credit_limit": np.round(credit_limit, 2),
            "products_count": products_count,
            "monthly_contribution_margin": np.round(base_margin, 2),
            "root_reason_synthetic": root_reason,
            "churn_month_synthetic": pd.to_datetime(churn_month),
            "marketing_consent": rng.binomial(1, 0.83, n),
        }
    )


def generate_monthly_activity(
    rng: np.random.Generator, customers: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    months = pd.date_range(FIRST_MONTH, LAST_MONTH, freq="MS")
    frames: list[pd.DataFrame] = []
    support_frames: list[pd.DataFrame] = []
    n = len(customers)
    days_since = rng.integers(0, 12, n).astype(float)
    base_txn = np.clip(
        rng.gamma(3.0, 3.1, n)
        + 4.0 * customers["digital_affinity"].to_numpy()
        + 2.5 * customers["has_credit_card"].to_numpy(),
        1,
        35,
    )
    base_sessions = np.clip(base_txn * rng.uniform(1.2, 2.5, n), 2, 70)
    base_balance = np.clip(customers["income"].to_numpy() * rng.uniform(0.15, 1.2, n), 20, 50_000)
    churn_month = customers["churn_month_synthetic"].to_numpy(dtype="datetime64[M]")
    signup_month = customers["signup_date"].to_numpy(dtype="datetime64[M]")
    reasons = customers["root_reason_synthetic"].to_numpy()
    # Some customers show a gradual decline, while others leave abruptly.
    # Temporary dormancy creates realistic false positives: not every fall in use becomes churn.
    gradual_decline = rng.random(n) < 0.38

    for month_number, month in enumerate(months):
        month64 = np.datetime64(month, "M")
        active_account = signup_month <= month64
        months_to_churn = (churn_month - month64).astype("timedelta64[M]").astype(float)
        no_churn = np.isnat(churn_month)
        factor = np.ones(n)
        factor[(months_to_churn == 3) & ~no_churn & gradual_decline] = 0.96
        factor[(months_to_churn == 2) & ~no_churn & gradual_decline] = 0.89
        factor[(months_to_churn == 1) & ~no_churn & gradual_decline] = 0.74
        factor[(months_to_churn <= 0) & ~no_churn] = 0.0
        factor[~active_account] = 0.0
        temporary_dormancy = (rng.random(n) < 0.11) & (factor > 0)
        factor[temporary_dormancy] *= rng.uniform(0.12, 0.58, temporary_dormancy.sum())

        seasonality = 1.0 + 0.12 * np.sin((month_number + 1) * np.pi / 6)
        noise = rng.lognormal(0, 0.20, n)
        financial_txn = rng.poisson(np.clip(base_txn * factor * seasonality * noise, 0, 60))
        app_sessions = rng.poisson(np.clip(base_sessions * factor * noise, 0, 120))
        pix_in = rng.binomial(financial_txn, np.clip(0.22 + 0.15 * customers["digital_affinity"], 0.1, 0.6))
        remaining = np.maximum(financial_txn - pix_in, 0)
        pix_out = rng.binomial(remaining, 0.28)
        remaining = np.maximum(remaining - pix_out, 0)
        card_purchases = np.where(
            customers["has_credit_card"].to_numpy() == 1,
            rng.binomial(remaining, 0.68),
            0,
        )
        bill_payments = np.maximum(remaining - card_purchases, 0)

        salary_probability = np.clip(
            0.58
            - 0.42 * ((reasons == "perda_de_renda") & (factor < 0.83))
            - 0.30 * (factor == 0),
            0.01,
            0.80,
        )
        salary_inflow = rng.binomial(1, salary_probability) * active_account
        balance_factor = np.where(
            (reasons == "pressao_financeira") & (factor < 0.83),
            np.maximum(factor * 0.55, 0.05),
            np.maximum(factor, 0.08),
        )
        avg_balance = np.clip(base_balance * balance_factor * rng.lognormal(0, 0.18, n), 0, 75_000)
        avg_balance[factor == 0] = np.clip(rng.normal(3, 4, (factor == 0).sum()), 0, 20)

        friction = (
            0.02
            + 0.15 * ((reasons == "friccao_no_app") & (factor < 0.83))
            + 0.08 * ((reasons == "frustracao_com_credito") & (factor < 0.60))
        )
        failed_txn = rng.binomial(np.maximum(financial_txn + 2, 2), np.clip(friction, 0, 0.45))
        contact_pressure = rng.poisson(
            np.clip(1.1 + 1.6 * (factor < 0.60) + 0.8 * (customers["acquisition_channel"].to_numpy() == "midia_paga"), 0, 8)
        )

        has_activity = financial_txn > 0
        days_since[has_activity] = rng.integers(0, 12, has_activity.sum())
        days_since[~has_activity] = np.minimum(days_since[~has_activity] + 30, 365)
        days_since[~active_account] = np.nan

        month_df = pd.DataFrame(
            {
                "customer_id": customers["customer_id"],
                "activity_month": month,
                "app_sessions": app_sessions,
                "pix_in_count": pix_in,
                "pix_out_count": pix_out,
                "card_purchase_count": card_purchases,
                "bill_payment_count": bill_payments,
                "financial_txn_count": financial_txn,
                "failed_txn_count": failed_txn,
                "salary_inflow": salary_inflow.astype(int),
                "avg_balance": np.round(avg_balance, 2),
                "days_since_last_activity": days_since,
                "contact_pressure_30d": contact_pressure,
            }
        )
        month_df = month_df[active_account].copy()
        frames.append(month_df)

        ticket_lambda = (
            0.05
            + 0.30 * ((reasons == "falha_de_atendimento") & (factor < 0.83))
            + 0.18 * (failed_txn >= 2)
        )
        ticket_count = rng.poisson(np.clip(ticket_lambda, 0, 1.2)) * active_account
        with_ticket = ticket_count > 0
        if with_ticket.any():
            support_frames.append(
                pd.DataFrame(
                    {
                        "customer_id": customers.loc[with_ticket, "customer_id"].to_numpy(),
                        "ticket_month": month,
                        "ticket_count": ticket_count[with_ticket],
                        "unresolved_count": rng.binomial(
                            ticket_count[with_ticket],
                            np.where(reasons[with_ticket] == "falha_de_atendimento", 0.38, 0.14),
                        ),
                        "nps": np.clip(
                            np.round(
                                rng.normal(
                                    np.where(reasons[with_ticket] == "falha_de_atendimento", 4.2, 7.3),
                                    1.8,
                                    with_ticket.sum(),
                                )
                            ),
                            0,
                            10,
                        ).astype(int),
                    }
                )
            )

    activity = pd.concat(frames, ignore_index=True)
    support = pd.concat(support_frames, ignore_index=True)
    return activity, support


def generate_experiment(
    rng: np.random.Generator, customers: pd.DataFrame
) -> pd.DataFrame:
    eligible = customers.sample(frac=0.46, random_state=RANDOM_SEED).copy()
    actions = np.array(["controle", "cashback_pix", "educacao", "contato_humano", "revisao_limite"])
    eligible["action"] = rng.choice(actions, len(eligible), p=[0.25, 0.19, 0.19, 0.19, 0.18])
    eligible["experiment_month"] = rng.choice(
        pd.to_datetime(["2025-10-01", "2025-11-01", "2025-12-01"]),
        len(eligible),
    )
    base_retention = np.clip(
        0.70
        + 0.035 * eligible["products_count"].to_numpy()
        + 0.08 * eligible["digital_affinity"].to_numpy()
        + rng.normal(0, 0.035, len(eligible)),
        0.48,
        0.94,
    )
    match = {
        "baixo_engajamento": "educacao",
        "perda_de_renda": "cashback_pix",
        "friccao_no_app": "contato_humano",
        "falha_de_atendimento": "contato_humano",
        "frustracao_com_credito": "revisao_limite",
        "pressao_financeira": "educacao",
    }
    matched_action = eligible["root_reason_synthetic"].map(match).to_numpy()
    uplift = np.where(eligible["action"].to_numpy() == matched_action, 0.115, 0.018)
    uplift = np.where(eligible["action"].to_numpy() == "controle", 0.0, uplift)
    retention_probability = np.clip(base_retention + uplift, 0.05, 0.98)
    eligible["retained_60d"] = rng.binomial(1, retention_probability)
    costs = {"controle": 0.0, "cashback_pix": 12.0, "educacao": 0.45, "contato_humano": 8.5, "revisao_limite": 1.8}
    eligible["action_cost"] = eligible["action"].map(costs)
    eligible["experiment_segment"] = eligible["root_reason_synthetic"]
    return eligible[
        [
            "customer_id",
            "experiment_month",
            "experiment_segment",
            "action",
            "action_cost",
            "retained_60d",
        ]
    ].reset_index(drop=True)


def main(n_customers: int = N_CUSTOMERS, seed: int = RANDOM_SEED) -> DataManifest:
    rng = np.random.default_rng(seed)
    customers = generate_customers(rng, n_customers)
    activity, support = generate_monthly_activity(rng, customers)
    experiment = generate_experiment(rng, customers)

    customers.to_csv(RAW_DIR / "customers.csv.gz", index=False, compression="gzip")
    activity.to_csv(RAW_DIR / "monthly_activity.csv.gz", index=False, compression="gzip")
    support.to_csv(RAW_DIR / "support_tickets.csv.gz", index=False, compression="gzip")
    experiment.to_csv(RAW_DIR / "retention_experiment.csv.gz", index=False, compression="gzip")

    manifest = DataManifest(
        seed=seed,
        customers=len(customers),
        monthly_rows=len(activity),
        support_rows=len(support),
        experiment_rows=len(experiment),
        first_month=FIRST_MONTH,
        last_month=LAST_MONTH,
    )
    (RAW_DIR / "manifest.json").write_text(
        json.dumps(asdict(manifest), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--customers", type=int, default=N_CUSTOMERS)
    parser.add_argument("--seed", type=int, default=RANDOM_SEED)
    args = parser.parse_args()
    print(main(args.customers, args.seed))
