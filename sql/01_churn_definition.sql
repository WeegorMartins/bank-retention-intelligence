-- Definição operacional: churn em 60 dias.
-- Um cliente é churner quando chega ao final do horizonte com pelo menos
-- 60 dias sem atividade financeira qualificante e no máximo uma transação.
with future_window as (
    select
        customer_id,
        max(days_since_last_activity) as max_days_inactive,
        sum(financial_txn_count) as qualifying_transactions
    from monthly_activity
    where activity_month between date '2026-06-01' and date '2026-07-01'
    group by customer_id
)
select
    customer_id,
    case
        when max_days_inactive >= 60 and qualifying_transactions <= 1 then 1
        else 0
    end as churn_60d
from future_window;

