select
    cast(customer_id as bigint) as customer_id,
    cast(signup_date as date) as signup_date,
    state,
    income_band,
    acquisition_channel,
    cast(has_credit_card as integer) as has_credit_card,
    cast(has_personal_loan as integer) as has_personal_loan,
    cast(products_count as integer) as products_count,
    cast(credit_limit as double) as credit_limit,
    cast(monthly_contribution_margin as double) as monthly_contribution_margin,
    cast(marketing_consent as integer) as marketing_consent
from read_csv_auto('data/raw/customers.csv.gz', header = true)
