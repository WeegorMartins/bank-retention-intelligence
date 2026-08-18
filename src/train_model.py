"""Train a baseline and a challenger using temporal validation."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.inspection import permutation_importance
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.config import MODEL_DIR, MODEL_FEATURES, OUTPUT_DIR, PROCESSED_DIR, RANDOM_SEED


def top_k_metrics(y_true: np.ndarray, probability: np.ndarray, capacity: float = 0.10) -> dict:
    n_target = max(1, int(len(y_true) * capacity))
    selected = np.argsort(-probability)[:n_target]
    captured = y_true[selected].sum()
    total = y_true.sum()
    precision = float(y_true[selected].mean())
    recall = float(captured / total) if total else 0.0
    lift = float(precision / y_true.mean()) if y_true.mean() else 0.0
    threshold = float(probability[selected].min())
    return {
        "capacity": capacity,
        "threshold": threshold,
        "precision_at_capacity": precision,
        "recall_at_capacity": recall,
        "lift_at_capacity": lift,
    }


def classification_metrics(y_true: np.ndarray, probability: np.ndarray, threshold: float) -> dict:
    predicted = (probability >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, predicted, labels=[0, 1]).ravel()
    return {
        "roc_auc": float(roc_auc_score(y_true, probability)),
        "pr_auc": float(average_precision_score(y_true, probability)),
        "brier_score": float(brier_score_loss(y_true, probability)),
        "precision": float(precision_score(y_true, predicted, zero_division=0)),
        "recall": float(recall_score(y_true, predicted, zero_division=0)),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
    }


def make_preprocessor(features: list[str] | None = None) -> ColumnTransformer:
    selected_features = MODEL_FEATURES if features is None else features
    return ColumnTransformer(
        [
            (
                "numeric",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scaler", StandardScaler()),
                    ]
                ),
                selected_features,
            )
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )


def make_models(features: list[str] | None = None) -> dict[str, Pipeline]:
    return {
        "baseline_logistic": Pipeline(
            [
                ("prep", make_preprocessor(features)),
                ("model", LogisticRegression(max_iter=700, class_weight="balanced", random_state=RANDOM_SEED)),
            ]
        ),
        "challenger_hist_gradient_boosting": Pipeline(
            [
                ("prep", make_preprocessor(features)),
                (
                    "model",
                    HistGradientBoostingClassifier(
                        learning_rate=0.075,
                        max_iter=180,
                        max_leaf_nodes=24,
                        min_samples_leaf=60,
                        l2_regularization=1.2,
                        random_state=RANDOM_SEED,
                    ),
                ),
            ]
        ),
    }


def make_deciles(frame: pd.DataFrame) -> pd.DataFrame:
    ordered = frame.sort_values("churn_probability", ascending=False).reset_index(drop=True)
    ordered["decile"] = pd.qcut(ordered.index, 10, labels=range(1, 11))
    overall_rate = ordered["churn_60d"].mean()
    result = ordered.groupby("decile", observed=False).agg(
        customers=("customer_id", "count"),
        predicted_risk=("churn_probability", "mean"),
        observed_churn=("churn_60d", "mean"),
        churners=("churn_60d", "sum"),
    ).reset_index()
    result["lift"] = result["observed_churn"] / overall_rate
    return result


def population_stability_index(expected: np.ndarray, actual: np.ndarray, bins: int = 10) -> float:
    edges = np.unique(np.quantile(expected, np.linspace(0, 1, bins + 1)))
    if len(edges) < 3:
        return 0.0
    edges[0] = -np.inf
    edges[-1] = np.inf
    expected_share, _ = np.histogram(expected, bins=edges)
    actual_share, _ = np.histogram(actual, bins=edges)
    expected_share = np.clip(expected_share / expected_share.sum(), 1e-6, None)
    actual_share = np.clip(actual_share / actual_share.sum(), 1e-6, None)
    return float(np.sum((actual_share - expected_share) * np.log(actual_share / expected_share)))


def select_sensitivity_feature(importance_frame: pd.DataFrame) -> str:
    """Return the strongest driver from the current model run."""
    if importance_frame.empty:
        raise ValueError("Feature importance cannot be empty.")
    return str(importance_frame.nlargest(1, "importance_mean").iloc[0]["feature"])


def main() -> dict:
    data = pd.read_csv(PROCESSED_DIR / "feature_snapshots.csv.gz", parse_dates=["snapshot_month"])
    train = data[data["snapshot_month"] <= "2026-03-01"].copy()
    validation = data[data["snapshot_month"] == "2026-04-01"].copy()
    test = data[data["snapshot_month"] == "2026-05-01"].copy()

    models = make_models()
    comparison: dict[str, dict] = {}
    for name, model in models.items():
        model.fit(train[MODEL_FEATURES], train["churn_60d"])
        valid_probability = model.predict_proba(validation[MODEL_FEATURES])[:, 1]
        operating = top_k_metrics(validation["churn_60d"].to_numpy(), valid_probability, 0.10)
        comparison[name] = {
            **classification_metrics(
                validation["churn_60d"].to_numpy(), valid_probability, operating["threshold"]
            ),
            **operating,
        }

    champion_name = max(comparison, key=lambda key: comparison[key]["pr_auc"])
    champion = models[champion_name]
    final_train = pd.concat([train, validation], ignore_index=True)
    champion.fit(final_train[MODEL_FEATURES], final_train["churn_60d"])
    validation_probability_final = champion.predict_proba(validation[MODEL_FEATURES])[:, 1]
    test_probability = champion.predict_proba(test[MODEL_FEATURES])[:, 1]
    operating_test = top_k_metrics(test["churn_60d"].to_numpy(), test_probability, 0.10)
    test_metrics = {
        **classification_metrics(
            test["churn_60d"].to_numpy(), test_probability, operating_test["threshold"]
        ),
        **operating_test,
    }

    prediction_cols = [
        "customer_id", "snapshot_month", "state", "income_band", "acquisition_channel",
        "marketing_consent", "annual_value_at_risk",
        "churn_60d", "days_since_last_activity", *MODEL_FEATURES,
    ]
    predictions = test[prediction_cols].copy()
    predictions["churn_probability"] = test_probability
    predictions["risk_band"] = pd.cut(
        predictions["churn_probability"],
        bins=[-0.001, 0.25, 0.50, 0.75, 1.001],
        labels=["baixo", "medio", "alto", "critico"],
    ).astype(str)
    predictions.to_csv(OUTPUT_DIR / "churn_predictions.csv.gz", index=False, compression="gzip")
    make_deciles(predictions).to_csv(OUTPUT_DIR / "model_deciles.csv", index=False)
    calibration = predictions.copy()
    calibration["probability_bin"] = pd.qcut(
        calibration["churn_probability"], 10, labels=False, duplicates="drop"
    ) + 1
    calibration.groupby("probability_bin", as_index=False).agg(
        customers=("customer_id", "count"),
        predicted_risk=("churn_probability", "mean"),
        observed_churn=("churn_60d", "mean"),
    ).to_csv(OUTPUT_DIR / "calibration_table.csv", index=False)

    sample = test.sample(min(6_000, len(test)), random_state=RANDOM_SEED)
    importance = permutation_importance(
        champion,
        sample[MODEL_FEATURES],
        sample["churn_60d"],
        n_repeats=4,
        scoring="average_precision",
        random_state=RANDOM_SEED,
        n_jobs=-1,
    )
    importance_frame = pd.DataFrame(
        {
            "feature": MODEL_FEATURES,
            "importance_mean": importance.importances_mean,
            "importance_std": importance.importances_std,
        }
    ).sort_values("importance_mean", ascending=False)
    importance_frame.to_csv(OUTPUT_DIR / "feature_importance.csv", index=False)
    positive_importance = importance_frame["importance_mean"].clip(lower=0)
    top_importance_share = float(
        positive_importance.iloc[0] / positive_importance.sum()
    ) if positive_importance.sum() else 0.0

    # The dominant driver can change with sample size. The robustness test must
    # always remove the feature that is actually ranked first in this run.
    sensitivity_feature = select_sensitivity_feature(importance_frame)
    sensitivity_features = [feature for feature in MODEL_FEATURES if feature != sensitivity_feature]
    sensitivity_model = make_models(sensitivity_features)[champion_name]
    sensitivity_model.fit(final_train[sensitivity_features], final_train["churn_60d"])
    sensitivity_probability = sensitivity_model.predict_proba(test[sensitivity_features])[:, 1]
    sensitivity_pr_auc = float(average_precision_score(test["churn_60d"], sensitivity_probability))

    metadata = {
        "champion_model": champion_name,
        "selection_metric": "pr_auc",
        "validation_comparison": comparison,
        "test_metrics": test_metrics,
        "score_psi_validation_to_test": population_stability_index(
            validation_probability_final, test_probability
        ),
        "sensitivity_analysis": {
            "excluded_feature": sensitivity_feature,
            "pr_auc_without_feature": sensitivity_pr_auc,
            "pr_auc_delta": float(test_metrics["pr_auc"] - sensitivity_pr_auc),
            "top_feature_positive_importance_share": top_importance_share,
        },
        "train_snapshots": ["2026-01", "2026-02", "2026-03", "2026-04"],
        "test_snapshot": "2026-05",
        "target": "60 dias sem atividade financeira qualificante",
        "protected_attributes_excluded": ["age", "state"],
    }
    (OUTPUT_DIR / "model_metrics.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    joblib.dump(champion, MODEL_DIR / "churn_champion.joblib")
    return metadata


if __name__ == "__main__":
    result = main()
    print(json.dumps(result, ensure_ascii=False, indent=2))
