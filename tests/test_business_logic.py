import pandas as pd

from src.config import MODEL_FEATURES
from src.recommend_actions import diagnose
from src.train_model import select_sensitivity_feature, top_k_metrics


def test_top_k_metrics_capture_high_risk():
    y = pd.Series([0, 0, 0, 1, 1]).to_numpy()
    p = pd.Series([0.1, 0.2, 0.3, 0.8, 0.9]).to_numpy()
    result = top_k_metrics(y, p, capacity=0.40)
    assert result["recall_at_capacity"] == 1.0
    assert result["lift_at_capacity"] > 1.0


def test_diagnosis_prioritizes_unresolved_service():
    frame = pd.DataFrame(
        {
            "unresolved_tickets_3m": [1],
            "avg_nps_3m": [3],
            "sum_failed_txn_3m": [4],
            "sessions_trend_3m": [-0.8],
            "has_credit_card": [1],
            "sum_card_purchases_3m": [0],
            "salary_inflow_months_3m": [0],
            "balance_trend_3m": [-0.8],
            "days_since_last_activity": [70],
        }
    )
    assert diagnose(frame).iloc[0] == "falha_de_atendimento"


def test_current_inactivity_is_not_used_as_model_feature():
    """The operational diagnostic must not become a shortcut for the future target."""
    assert "days_since_last_activity" not in MODEL_FEATURES


def test_sensitivity_uses_the_actual_top_feature():
    importance = pd.DataFrame(
        {"feature": ["saldo", "acessos"], "importance_mean": [0.08, 0.27]}
    )
    assert select_sensitivity_feature(importance) == "acessos"
