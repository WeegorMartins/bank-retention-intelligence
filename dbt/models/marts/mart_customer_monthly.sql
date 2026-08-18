with support as (
    select
        customer_id,
        ticket_month,
        sum(ticket_count) as ticket_count,
        sum(unresolved_count) as unresolved_count,
        avg(nps) as avg_nps
    from {{ ref('stg_support_tickets') }}
    group by 1, 2
)
select
    a.customer_id,
    a.activity_month,
    c.state,
    c.income_band,
    c.acquisition_channel,
    c.products_count,
    c.monthly_contribution_margin,
    a.app_sessions,
    a.financial_txn_count,
    a.failed_txn_count,
    a.avg_balance,
    a.days_since_last_activity,
    coalesce(s.ticket_count, 0) as ticket_count,
    coalesce(s.unresolved_count, 0) as unresolved_count,
    coalesce(s.avg_nps, 8) as avg_nps
from {{ ref('stg_monthly_activity') }} a
inner join {{ ref('stg_customers') }} c using (customer_id)
left join support s
    on a.customer_id = s.customer_id
    and a.activity_month = s.ticket_month

