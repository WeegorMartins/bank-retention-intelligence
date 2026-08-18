"""Diagnose likely churn causes and choose the best economically viable action."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

from src.config import OUTPUT_DIR, RAW_DIR


ACTION_LABELS = {
    "controle": "Não contatar",
    "cashback_pix": "Incentivo de uso do Pix",
    "educacao": "Jornada educativa personalizada",
    "contato_humano": "Contato humano prioritário",
    "revisao_limite": "Encaminhar para avaliação de limite",
}


def diagnose(frame: pd.DataFrame) -> pd.Series:
    conditions = [
        (frame["unresolved_tickets_3m"] > 0) | (frame["avg_nps_3m"] <= 5),
        (frame["sum_failed_txn_3m"] >= 3) & (frame["sessions_trend_3m"] < -0.25),
        (frame["has_credit_card"] == 1) & (frame["sum_card_purchases_3m"] <= 2),
        (frame["salary_inflow_months_3m"] == 0) & (frame["balance_trend_3m"] < -0.25),
        frame["days_since_last_activity"] >= 30,
        frame["balance_trend_3m"] < -0.45,
    ]
    choices = [
        "falha_de_atendimento",
        "friccao_no_app",
        "frustracao_com_credito",
        "perda_de_renda",
        "baixo_engajamento",
        "pressao_financeira",
    ]
    return pd.Series(np.select(conditions, choices, default="baixo_engajamento"), index=frame.index)


def estimate_action_effects(experiment: pd.DataFrame) -> pd.DataFrame:
    grouped = experiment.groupby(["experiment_segment", "action"], as_index=False).agg(
        customers=("customer_id", "count"),
        retained=("retained_60d", "sum"),
        action_cost=("action_cost", "mean"),
    )
    # Beta(2,2) smoothing keeps small cells from appearing artificially certain.
    grouped["retention_rate_smoothed"] = (grouped["retained"] + 2) / (grouped["customers"] + 4)
    control = grouped[grouped["action"] == "controle"][
        ["experiment_segment", "retention_rate_smoothed"]
    ].rename(columns={"retention_rate_smoothed": "control_rate"})
    effects = grouped.merge(control, on="experiment_segment", how="left")
    effects["incremental_retention"] = (
        effects["retention_rate_smoothed"] - effects["control_rate"]
    ).clip(lower=-0.10, upper=0.30)
    return effects


def customer_reasons(row: pd.Series) -> str:
    reasons: list[str] = []
    if row["txn_trend_3m"] < -0.35:
        reasons.append("queda forte nas transações")
    if row["sessions_trend_3m"] < -0.35:
        reasons.append("redução de acessos ao aplicativo")
    if row["salary_inflow_months_3m"] == 0:
        reasons.append("ausência de entrada salarial")
    if row["unresolved_tickets_3m"] > 0:
        reasons.append("atendimento não resolvido")
    if row["sum_failed_txn_3m"] >= 3:
        reasons.append("recorrência de falhas transacionais")
    if row["days_since_last_activity"] >= 30:
        reasons.append("inatividade recente")
    return "; ".join(reasons[:3]) if reasons else "engajamento abaixo do padrão do portfólio"


def main() -> pd.DataFrame:
    predictions = pd.read_csv(OUTPUT_DIR / "churn_predictions.csv.gz")
    experiment = pd.read_csv(RAW_DIR / "retention_experiment.csv.gz")
    effects = estimate_action_effects(experiment)
    effects.to_csv(OUTPUT_DIR / "action_effects.csv", index=False)

    predictions["diagnostic_segment"] = diagnose(predictions)
    predictions["risk_reasons"] = predictions.apply(customer_reasons, axis=1)
    candidates = predictions.merge(
        effects[
            [
                "experiment_segment", "action", "action_cost", "customers",
                "incremental_retention",
            ]
        ],
        left_on="diagnostic_segment",
        right_on="experiment_segment",
        how="left",
    )
    candidates = candidates[candidates["action"] != "controle"].copy()
    candidates["eligible"] = 1
    candidates.loc[
        (candidates["action"] == "revisao_limite")
        & (candidates["has_credit_card"] == 0),
        "eligible",
    ] = 0
    candidates.loc[
        (candidates["marketing_consent"] == 0)
        & (candidates["action"].isin(["cashback_pix", "educacao"])),
        "eligible",
    ] = 0
    candidates.loc[candidates["contact_pressure_30d"] >= 5, "eligible"] = 0

    candidates["expected_retained_value"] = (
        candidates["churn_probability"]
        * candidates["incremental_retention"].clip(lower=0)
        * candidates["annual_value_at_risk"]
    )
    candidates["expected_net_value"] = (
        candidates["expected_retained_value"] - candidates["action_cost"]
    )
    candidates.loc[candidates["eligible"] == 0, "expected_net_value"] = -999
    candidates = candidates.sort_values(
        ["customer_id", "expected_net_value"], ascending=[True, False]
    )
    recommended = candidates.groupby("customer_id", as_index=False).first()
    recommended["recommended_action"] = recommended["action"].map(ACTION_LABELS)
    not_worth = (recommended["expected_net_value"] <= 0) | (recommended["churn_probability"] < 0.20)
    recommended.loc[not_worth, "recommended_action"] = ACTION_LABELS["controle"]
    recommended.loc[not_worth, "action"] = "controle"
    recommended.loc[not_worth, ["action_cost", "expected_retained_value", "expected_net_value"]] = 0
    recommended["priority_score"] = (
        recommended["expected_net_value"].clip(lower=0)
        * recommended["churn_probability"]
    )
    recommended["evidence_strength"] = np.select(
        [recommended["customers"] >= 700, recommended["customers"] >= 250],
        ["alta", "media"],
        default="baixa",
    )

    selected_cols = [
        "customer_id", "risk_band", "churn_probability", "diagnostic_segment",
        "risk_reasons", "recommended_action", "action", "action_cost",
        "incremental_retention", "annual_value_at_risk", "expected_retained_value",
        "expected_net_value", "priority_score", "evidence_strength", "state",
        "income_band", "monthly_contribution_margin", "marketing_consent",
        "contact_pressure_30d", "churn_60d",
    ]
    final = recommended[selected_cols].sort_values("priority_score", ascending=False)
    final.to_csv(OUTPUT_DIR / "next_best_actions.csv.gz", index=False, compression="gzip")

    policy_comparison = pd.DataFrame(
        {
            "policy": [
                "Não agir",
                "Contatar todo alto risco",
                "Capacidade fixa: top 10%",
                "Política econômica personalizada",
            ],
            "customers_contacted": [
                0,
                int(final["risk_band"].isin(["alto", "critico"]).sum()),
                int(np.ceil(len(final) * 0.10)),
                int((final["action"] != "controle").sum()),
            ],
            "expected_net_value": [
                0.0,
                float(final.loc[final["risk_band"].isin(["alto", "critico"]), "expected_net_value"].clip(lower=0).sum() * 0.72),
                float(final.nlargest(int(np.ceil(len(final) * 0.10)), "churn_probability")["expected_net_value"].clip(lower=0).sum()),
                float(final["expected_net_value"].clip(lower=0).sum()),
            ],
        }
    )
    policy_comparison.to_csv(OUTPUT_DIR / "policy_comparison.csv", index=False)

    summary = {
        "portfolio_customers": int(len(final)),
        "high_or_critical_risk": int(final["risk_band"].isin(["alto", "critico"]).sum()),
        "customers_recommended_for_action": int((final["action"] != "controle").sum()),
        "annual_value_at_risk": float(
            final.loc[final["risk_band"].isin(["alto", "critico"]), "annual_value_at_risk"].sum()
        ),
        "expected_net_value_policy": float(final["expected_net_value"].clip(lower=0).sum()),
        "average_action_cost": float(final.loc[final["action"] != "controle", "action_cost"].mean()),
        "disclaimer": "Estimativas simuladas; não representam impacto financeiro realizado.",
    }
    (OUTPUT_DIR / "executive_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return final


if __name__ == "__main__":
    result = main()
    print(result.head(10).to_string(index=False))
