select
    cast(customer_id as bigint) as customer_id,
    cast(activity_month as date) as activity_month,
    cast(app_sessions as integer) as app_sessions,
    cast(pix_in_count as integer) as pix_in_count,
    cast(pix_out_count as integer) as pix_out_count,
    cast(card_purchase_count as integer) as card_purchase_count,
    cast(bill_payment_count as integer) as bill_payment_count,
    cast(financial_txn_count as integer) as financial_txn_count,
    cast(failed_txn_count as integer) as failed_txn_count,
    cast(salary_inflow as integer) as salary_inflow,
    cast(avg_balance as double) as avg_balance,
    cast(days_since_last_activity as integer) as days_since_last_activity,
    cast(contact_pressure_30d as integer) as contact_pressure_30d
from read_csv_auto('data/raw/monthly_activity.csv.gz', header = true)
