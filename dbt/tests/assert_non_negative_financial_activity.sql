select *
from {{ ref('mart_customer_monthly') }}
where financial_txn_count < 0
   or failed_txn_count < 0
   or avg_balance < 0

