"""Run the full reproducible project pipeline."""

from __future__ import annotations

import argparse
import json

from src import build_features, generate_data, recommend_actions, train_model, validate_data


def main(customers: int) -> None:
    print("[1/5] Gerando dados sintéticos...")
    manifest = generate_data.main(n_customers=customers)
    print(json.dumps(manifest.__dict__, ensure_ascii=False, indent=2))
    print("[2/5] Validando contratos de dados...")
    print(json.dumps(validate_data.main(), ensure_ascii=False, indent=2))
    print("[3/5] Construindo snapshots sem vazamento temporal...")
    features = build_features.main()
    print(f"{len(features):,} snapshots criados")
    print("[4/5] Treinando e avaliando modelos...")
    metrics = train_model.main()
    print(json.dumps(metrics["test_metrics"], ensure_ascii=False, indent=2))
    print("[5/5] Criando diagnóstico e recomendações...")
    actions = recommend_actions.main()
    print(f"{len(actions):,} clientes avaliados. Pipeline concluído.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--customers", type=int, default=50_000)
    args = parser.parse_args()
    main(args.customers)
