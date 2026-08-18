-- Diagnóstico gerencial: risco, valor e concentração por segmento.
select
    diagnostic_segment,
    risk_band,
    count(*) as customers,
    avg(churn_probability) as average_churn_probability,
    sum(annual_value_at_risk) as annual_value_at_risk,
    sum(expected_net_value) as expected_net_value
from next_best_actions
group by 1, 2
order by annual_value_at_risk desc;

