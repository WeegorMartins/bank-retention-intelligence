-- Ação não é escolhida apenas pelo risco.
-- Valor líquido = risco × retenção incremental × valor anual − custo.
select
    customer_id,
    action,
    churn_probability,
    incremental_retention,
    annual_value_at_risk,
    action_cost,
    churn_probability * incremental_retention * annual_value_at_risk
        - action_cost as expected_net_value
from action_candidates
where eligible = 1;

