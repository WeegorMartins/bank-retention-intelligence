select customer_id, activity_month, count(*) as records
from {{ ref('mart_customer_monthly') }}
group by 1, 2
having count(*) > 1

