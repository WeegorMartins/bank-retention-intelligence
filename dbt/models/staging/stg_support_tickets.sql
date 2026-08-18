select
    cast(customer_id as bigint) as customer_id,
    cast(ticket_month as date) as ticket_month,
    cast(ticket_count as integer) as ticket_count,
    cast(unresolved_count as integer) as unresolved_count,
    cast(nps as integer) as nps
from read_csv_auto('data/raw/support_tickets.csv.gz', header = true)
