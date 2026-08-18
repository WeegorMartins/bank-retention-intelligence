from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "outputs"
RAW = ROOT / "data" / "raw"

CAUSE_LABELS = {
    "baixo_engajamento": "Baixo engajamento",
    "falha_de_atendimento": "Falha de atendimento",
    "pressao_financeira": "Pressão financeira",
    "frustracao_com_credito": "Frustração com crédito",
    "perda_de_renda": "Perda de renda",
    "friccao_no_app": "Fricção no aplicativo",
}

RISK_LABELS = {"baixo": "Baixo", "medio": "Médio", "alto": "Alto", "critico": "Crítico"}
EVIDENCE_LABELS = {"baixa": "Baixa", "media": "Média", "alta": "Alta"}
MODEL_LABELS = {
    "baseline_logistic": "Regressão logística",
    "challenger_hist_gradient_boosting": "Gradient boosting",
}
FEATURE_LABELS = {
    "tenure_months": "Tempo de relacionamento",
    "products_count": "Quantidade de produtos",
    "has_credit_card": "Possui cartão de crédito",
    "has_personal_loan": "Possui empréstimo pessoal",
    "credit_limit": "Limite de crédito",
    "avg_balance_3m": "Saldo médio em 3 meses",
    "avg_app_sessions_3m": "Acessos médios ao app em 3 meses",
    "sum_pix_in_3m": "Pix recebidos em 3 meses",
    "sum_pix_out_3m": "Pix enviados em 3 meses",
    "sum_card_purchases_3m": "Compras no cartão em 3 meses",
    "sum_bill_payments_3m": "Contas pagas em 3 meses",
    "sum_financial_txn_3m": "Transações financeiras em 3 meses",
    "sum_failed_txn_3m": "Transações com falha em 3 meses",
    "salary_inflow_months_3m": "Meses com entrada salarial",
    "support_tickets_3m": "Chamados em 3 meses",
    "unresolved_tickets_3m": "Chamados não resolvidos",
    "avg_nps_3m": "NPS médio em 3 meses",
    "txn_trend_3m": "Tendência de transações",
    "sessions_trend_3m": "Tendência de acessos ao app",
    "balance_trend_3m": "Tendência de saldo",
    "contact_pressure_30d": "Pressão de contato em 30 dias",
    "monthly_contribution_margin": "Margem de contribuição mensal",
}

st.set_page_config(
    page_title="Pulso | Inteligência de Retenção",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .stApp {background-color:#07111f; color:#edf3f8;}
    [data-testid="stSidebar"] {background-color:#0b1728;}
    .metric-card {background:linear-gradient(145deg,#11243a,#0b1a2c); border:1px solid #203a55;
      border-radius:16px; padding:18px 20px; min-height:126px; box-shadow:0 8px 26px rgba(0,0,0,.20);}
    .metric-title {color:#93a9bc; font-size:.82rem; letter-spacing:.04em; text-transform:uppercase;}
    .metric-value {color:#f4f8fb; font-size:2rem; font-weight:750; margin-top:8px;}
    .metric-note {color:#8fa5b8; font-size:.78rem; margin-top:5px;}
    .signal {display:inline-block; border-radius:999px; padding:4px 10px; background:#123c43; color:#6fe5cf; font-size:.76rem;}
    h1,h2,h3 {color:#f5f8fb !important;}
    div[data-testid="stDataFrame"] {border:1px solid #203a55; border-radius:12px; overflow:hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_data():
    actions = pd.read_csv(OUTPUT / "next_best_actions.csv.gz")
    predictions = pd.read_csv(OUTPUT / "churn_predictions.csv.gz")
    importance = pd.read_csv(OUTPUT / "feature_importance.csv")
    deciles = pd.read_csv(OUTPUT / "model_deciles.csv")
    effects = pd.read_csv(OUTPUT / "action_effects.csv")
    summary = json.loads((OUTPUT / "executive_summary.json").read_text(encoding="utf-8"))
    metrics = json.loads((OUTPUT / "model_metrics.json").read_text(encoding="utf-8"))
    manifest = json.loads((RAW / "manifest.json").read_text(encoding="utf-8"))
    return actions, predictions, importance, deciles, effects, summary, metrics, manifest


def brl(value: float) -> str:
    if abs(value) >= 1_000_000:
        return f"R$ {value / 1_000_000:,.1f} mi".replace(",", "X").replace(".", ",").replace("X", ".")
    if abs(value) >= 1_000:
        return f"R$ {value / 1_000:,.0f} mil".replace(",", ".")
    return f"R$ {value:,.0f}".replace(",", ".")


def card(title: str, value: str, note: str):
    st.markdown(
        f'<div class="metric-card"><div class="metric-title">{title}</div>'
        f'<div class="metric-value">{value}</div><div class="metric-note">{note}</div></div>',
        unsafe_allow_html=True,
    )


required = [
    OUTPUT / "next_best_actions.csv.gz",
    OUTPUT / "model_metrics.json",
    RAW / "manifest.json",
]
if not all(path.exists() and path.stat().st_size > 0 for path in required):
    st.title("Pulso | Inteligência de Retenção")
    st.error("Os resultados ainda não foram gerados.")
    st.code("python -m src.run_pipeline --customers 50000", language="bash")
    st.stop()

actions, predictions, importance, deciles, effects, summary, metrics, manifest = load_data()

st.sidebar.markdown("## ◉ Pulso")
st.sidebar.caption("Diagnóstico e próxima melhor ação")
page = st.sidebar.radio(
    "Navegação",
    [
        "Visão executiva",
        "Diagnóstico",
        "Desempenho do modelo",
        "Próxima melhor ação",
        "Cliente 360",
        "Governança e monitoramento",
    ],
)
st.sidebar.markdown("---")
st.sidebar.markdown('<span class="signal">Dados 100% sintéticos</span>', unsafe_allow_html=True)
st.sidebar.caption("Snapshot de decisão: maio/2026 · horizonte: 60 dias")

plot_template = "plotly_dark"
color_sequence = ["#55dcc5", "#ffb454", "#ff6b7a", "#68a4ff", "#a98bff"]

if page == "Visão executiva":
    st.title("Visão executiva de retenção")
    st.caption("Quem está em risco, por que pode sair e onde a intervenção cria valor incremental.")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        card("Clientes avaliados", f'{summary["portfolio_customers"]:,}'.replace(",", "."), "Base elegível no snapshot")
    with c2:
        card("Risco alto ou crítico", f'{summary["high_or_critical_risk"]:,}'.replace(",", "."), "Probabilidade individual")
    with c3:
        card("Valor anual em risco", brl(summary["annual_value_at_risk"]), "Não é perda realizada")
    with c4:
        card("Valor líquido esperado", brl(summary["expected_net_value_policy"]), "Política simulada de ações")

    st.markdown("### O que exige decisão")
    left, right = st.columns([1.15, 1])
    with left:
        cause = (
            actions[actions["risk_band"].isin(["alto", "critico"])]
            .groupby("diagnostic_segment", as_index=False)
            .agg(clientes=("customer_id", "count"), valor_em_risco=("annual_value_at_risk", "sum"))
            .sort_values("valor_em_risco")
        )
        cause["causa_exibicao"] = cause["diagnostic_segment"].map(CAUSE_LABELS)
        fig = px.bar(
            cause,
            x="valor_em_risco",
            y="causa_exibicao",
            orientation="h",
            color="valor_em_risco",
            color_continuous_scale=["#19344d", "#55dcc5"],
            template=plot_template,
            labels={"valor_em_risco": "Valor anual em risco", "causa_exibicao": "Causa provável"},
            title="Valor em risco por causa provável",
        )
        fig.update_layout(coloraxis_showscale=False, height=410)
        st.plotly_chart(fig, width="stretch")
    with right:
        action_value = (
            actions.groupby("recommended_action", as_index=False)
            .agg(clientes=("customer_id", "count"), valor_liquido=("expected_net_value", "sum"))
            .sort_values("valor_liquido", ascending=False)
        )
        fig = px.scatter(
            action_value,
            x="clientes",
            y="valor_liquido",
            size="valor_liquido",
            color="recommended_action",
            color_discrete_sequence=color_sequence,
            template=plot_template,
            labels={"clientes": "Clientes", "valor_liquido": "Valor líquido esperado"},
            title="Escala e retorno das ações recomendadas",
        )
        fig.update_layout(
            height=410,
            legend_title_text="Ação",
            legend=dict(orientation="h", yanchor="top", y=-0.18, xanchor="left", x=0),
        )
        st.plotly_chart(fig, width="stretch")

    top = actions[actions["action"] != "controle"].nlargest(10, "priority_score").copy()
    st.markdown("### Dez decisões prioritárias")
    top_display = top[
            ["customer_id", "risk_band", "churn_probability", "diagnostic_segment",
             "recommended_action", "expected_net_value", "evidence_strength"]
        ].copy()
    top_display["risk_band"] = top_display["risk_band"].map(RISK_LABELS)
    top_display["diagnostic_segment"] = top_display["diagnostic_segment"].map(CAUSE_LABELS)
    top_display["evidence_strength"] = top_display["evidence_strength"].map(EVIDENCE_LABELS)
    top_display = top_display.rename(columns={
        "customer_id": "Cliente",
        "risk_band": "Faixa de risco",
        "churn_probability": "Risco",
        "diagnostic_segment": "Causa provável",
        "recommended_action": "Ação recomendada",
        "expected_net_value": "Valor líquido esperado",
        "evidence_strength": "Força da evidência",
    })
    st.dataframe(
        top_display,
        hide_index=True,
        width="stretch",
        column_config={
            "Risco": st.column_config.ProgressColumn("Risco", min_value=0, max_value=1, format="percent"),
            "Valor líquido esperado": st.column_config.NumberColumn("Valor líquido esperado", format="R$ %.2f"),
        },
    )
    st.caption(
        "Força da evidência indica o tamanho da amostra experimental da ação. "
        "Evidência baixa exige piloto controlado antes de qualquer escala."
    )

elif page == "Diagnóstico":
    st.title("Diagnóstico de churn")
    st.caption("Separação entre probabilidade, causa provável e valor financeiro em risco.")
    risk_filter = st.multiselect(
        "Faixa de risco",
        ["baixo", "medio", "alto", "critico"],
        default=["alto", "critico"],
        format_func=lambda value: RISK_LABELS[value],
    )
    filtered = actions[actions["risk_band"].isin(risk_filter)].copy()
    filtered["causa_exibicao"] = filtered["diagnostic_segment"].map(CAUSE_LABELS)
    c1, c2 = st.columns(2)
    with c1:
        matrix = filtered.groupby(["causa_exibicao", "risk_band"], as_index=False).size()
        matrix["faixa_exibicao"] = matrix["risk_band"].map(RISK_LABELS)
        fig = px.bar(
            matrix,
            x="causa_exibicao",
            y="size",
            color="faixa_exibicao",
            barmode="stack",
            color_discrete_map={"Baixo": "#68a4ff", "Médio": "#ffb454", "Alto": "#ff8c66", "Crítico": "#ff4d6d"},
            template=plot_template,
            labels={"size": "Clientes", "causa_exibicao": "Causa provável", "faixa_exibicao": "Faixa de risco"},
            title="Risco por causa provável",
        )
        st.plotly_chart(fig, width="stretch")
    with c2:
        fig = px.scatter(
            filtered,
            x="churn_probability",
            y="annual_value_at_risk",
            color="causa_exibicao",
            size="monthly_contribution_margin",
            opacity=0.55,
            template=plot_template,
            color_discrete_sequence=color_sequence,
            labels={"churn_probability": "Probabilidade de churn", "annual_value_at_risk": "Valor anual em risco"},
            title="Risco versus valor financeiro",
        )
        fig.update_layout(
            legend_title_text="Causa provável",
            legend=dict(orientation="h", yanchor="top", y=-0.22, xanchor="left", x=0),
        )
        st.plotly_chart(fig, width="stretch")

    st.markdown("### Leitura das causas")
    st.info(
        "A causa é uma hipótese diagnóstica baseada em comportamento observado. "
        "Ela deve orientar um teste, não ser tratada como verdade individual incontestável."
    )
    cause_table = filtered.groupby("causa_exibicao", as_index=False).agg(
        clientes=("customer_id", "count"),
        risco_medio=("churn_probability", "mean"),
        valor_em_risco=("annual_value_at_risk", "sum"),
        valor_liquido_estimado=("expected_net_value", "sum"),
    ).sort_values("valor_em_risco", ascending=False)
    cause_table = cause_table.rename(columns={
        "causa_exibicao": "Causa provável",
        "clientes": "Clientes",
        "risco_medio": "Risco médio",
        "valor_em_risco": "Valor em risco",
        "valor_liquido_estimado": "Valor líquido estimado",
    })
    st.dataframe(
        cause_table,
        hide_index=True,
        width="stretch",
        column_config={
            "Risco médio": st.column_config.NumberColumn("Risco médio", format="percent"),
            "Valor em risco": st.column_config.NumberColumn("Valor em risco", format="R$ %.2f"),
            "Valor líquido estimado": st.column_config.NumberColumn("Valor líquido estimado", format="R$ %.2f"),
        },
    )

elif page == "Desempenho do modelo":
    st.title("Desempenho e limite operacional")
    tm = metrics["test_metrics"]
    c1, c2, c3, c4 = st.columns(4)
    with c1: card("ROC-AUC", f'{tm["roc_auc"]:.3f}', "Discriminação global")
    with c2: card("PR-AUC", f'{tm["pr_auc"]:.3f}', "Métrica principal")
    with c3: card("Recall no top 10%", f'{tm["recall_at_capacity"]:.1%}', "Capacidade operacional fixa")
    with c4: card("Lift no top 10%", f'{tm["lift_at_capacity"]:.1f}x', "Comparado à seleção aleatória")

    left, right = st.columns(2)
    with left:
        fig = px.bar(
            deciles,
            x="decile",
            y="observed_churn",
            color="lift",
            color_continuous_scale=["#19344d", "#55dcc5"],
            template=plot_template,
            labels={"decile": "Decil de risco (1 = maior)", "observed_churn": "Churn observado"},
            title="Concentração de churn por decil",
        )
        fig.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig, width="stretch")
    with right:
        top_importance = importance.nlargest(12, "importance_mean").sort_values("importance_mean").copy()
        top_importance["variavel_exibicao"] = (
            top_importance["feature"].map(FEATURE_LABELS).fillna(top_importance["feature"])
        )
        fig = px.bar(
            top_importance,
            x="importance_mean",
            y="variavel_exibicao",
            orientation="h",
            color="importance_mean",
            color_continuous_scale=["#19344d", "#68a4ff"],
            template=plot_template,
            labels={"importance_mean": "Queda na PR-AUC", "variavel_exibicao": "Variável"},
            title="Importância por permutação",
        )
        fig.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig, width="stretch")

    sensitivity = metrics.get("sensitivity_analysis")
    if sensitivity:
        excluded_label = FEATURE_LABELS.get(
            sensitivity["excluded_feature"], sensitivity["excluded_feature"]
        )
        delta = float(sensitivity["pr_auc_delta"])
        variation_text = (
            f"queda de {delta:.3f}"
            if delta >= 0
            else f"ganho marginal de {abs(delta):.3f}"
        )
        st.info(
            f'**Teste de robustez:** {excluded_label} concentra '
            f'{sensitivity["top_feature_positive_importance_share"]:.1%} da importância positiva. '
            f'Ao retirar essa variável e treinar novamente, a PR-AUC fica em '
            f'{sensitivity["pr_auc_without_feature"]:.3f} '
            f'({variation_text}). A estabilidade indica que o modelo não depende '
            f'exclusivamente desse sinal.'
        )

    st.warning(
        "O modelo foi avaliado em corte temporal posterior. Estado e idade não entram no modelo; "
        "estado é mantido somente para auditoria de estabilidade e disparidades."
    )

elif page == "Próxima melhor ação":
    st.title("Próxima melhor ação")
    st.caption("Risco × retenção incremental × valor do cliente − custo da intervenção.")
    st.info(
        "A recomendação é uma hipótese de intervenção. Linhas com evidência baixa devem "
        "entrar primeiro em piloto com grupo de controle, e não em implantação ampla."
    )
    c1, c2, c3 = st.columns(3)
    risk = c1.multiselect(
        "Risco",
        ["baixo", "medio", "alto", "critico"],
        default=["alto", "critico"],
        format_func=lambda value: RISK_LABELS[value],
    )
    causes = sorted(actions["diagnostic_segment"].unique())
    cause = c2.multiselect(
        "Causa",
        causes,
        default=causes,
        format_func=lambda value: CAUSE_LABELS.get(value, value),
    )
    min_value = c3.number_input("Valor líquido mínimo", min_value=0.0, value=10.0, step=10.0)
    table = actions[
        actions["risk_band"].isin(risk)
        & actions["diagnostic_segment"].isin(cause)
        & (actions["expected_net_value"] >= min_value)
    ].copy()
    action_display = table[
            ["customer_id", "churn_probability", "risk_reasons", "recommended_action",
             "incremental_retention", "action_cost", "expected_net_value", "evidence_strength"]
        ].head(1000).copy()
    action_display["incremental_retention"] = action_display["incremental_retention"] * 100
    action_display["evidence_strength"] = action_display["evidence_strength"].map(EVIDENCE_LABELS)
    action_display = action_display.rename(columns={
        "customer_id": "Cliente",
        "churn_probability": "Risco",
        "risk_reasons": "Principais sinais",
        "recommended_action": "Ação recomendada",
        "incremental_retention": "Retenção incremental",
        "action_cost": "Custo",
        "expected_net_value": "Valor líquido",
        "evidence_strength": "Força da evidência",
    })
    st.dataframe(
        action_display,
        hide_index=True,
        width="stretch",
        column_config={
            "Risco": st.column_config.ProgressColumn("Risco", min_value=0, max_value=1, format="percent"),
            "Retenção incremental": st.column_config.NumberColumn("Retenção incremental", format="%.1f%%"),
            "Custo": st.column_config.NumberColumn("Custo", format="R$ %.2f"),
            "Valor líquido": st.column_config.NumberColumn("Valor líquido", format="R$ %.2f"),
        },
    )
    st.download_button(
        "Baixar fila priorizada",
        data=table.to_csv(index=False).encode("utf-8"),
        file_name="fila_retencao_priorizada.csv",
        mime="text/csv",
    )

elif page == "Cliente 360":
    st.title("Cliente 360")
    customer_id = st.selectbox("Cliente", actions["customer_id"].head(2000).tolist())
    row = actions[actions["customer_id"] == customer_id].iloc[0]
    c1, c2, c3, c4 = st.columns(4)
    with c1: card("Risco", f'{row["churn_probability"]:.1%}', RISK_LABELS.get(str(row["risk_band"]), str(row["risk_band"])))
    with c2: card("Causa provável", CAUSE_LABELS.get(str(row["diagnostic_segment"]), str(row["diagnostic_segment"])), "Hipótese diagnóstica")
    with c3: card("Ação", str(row["recommended_action"]), f'Evidência {EVIDENCE_LABELS.get(str(row["evidence_strength"]), str(row["evidence_strength"]))}')
    with c4: card("Valor líquido", brl(float(row["expected_net_value"])), "Estimativa individual")
    st.markdown("### Principais sinais")
    st.write(row["risk_reasons"])
    gauge = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=float(row["churn_probability"] * 100),
            number={"suffix": "%"},
            title={"text": "Probabilidade de churn em 60 dias"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "#55dcc5"},
                "steps": [
                    {"range": [0, 25], "color": "#173451"},
                    {"range": [25, 50], "color": "#5d512d"},
                    {"range": [50, 75], "color": "#6b3d32"},
                    {"range": [75, 100], "color": "#6e2639"},
                ],
            },
        )
    )
    gauge.update_layout(template=plot_template, height=340)
    st.plotly_chart(gauge, width="stretch")
    st.caption("A recomendação respeita consentimento, pressão de contato, elegibilidade e retorno econômico.")

else:
    st.title("Governança e monitoramento")
    c1, c2, c3 = st.columns(3)
    with c1: card("Linhas mensais", f'{manifest["monthly_rows"]:,}'.replace(",", "."), "Manifesto reproduzível")
    with c2: card("Modelo campeão", MODEL_LABELS.get(metrics["champion_model"], metrics["champion_model"]), "Escolhido por PR-AUC")
    with c3: card("Atributos excluídos", "Idade e estado", "Não usados na decisão")

    st.markdown("### Auditoria por estado")
    audit = predictions.groupby("state", as_index=False).agg(
        clientes=("customer_id", "count"),
        risco_medio=("churn_probability", "mean"),
        churn_observado=("churn_60d", "mean"),
    )
    fig = px.scatter(
        audit,
        x="risco_medio",
        y="churn_observado",
        size="clientes",
        text="state",
        template=plot_template,
        color_discrete_sequence=["#55dcc5"],
        labels={"risco_medio": "Risco médio previsto", "churn_observado": "Churn observado"},
        title="Previsto versus observado por UF (somente monitoramento)",
    )
    fig.update_traces(textposition="top center")
    st.plotly_chart(fig, width="stretch")

    st.markdown("### Controles do projeto")
    st.markdown(
        """
        - Corte temporal para evitar vazamento de informação futura.
        - Consentimento e pressão de contato aplicados antes da recomendação.
        - Grupos de controle e retenção incremental para avaliar ações.
        - Custos deduzidos do valor esperado; alto risco não implica contato automático.
        - Dados sintéticos identificados em todas as entregas.
        - Recomendações são hipóteses para experimentação, não decisões irreversíveis.
        """
    )
