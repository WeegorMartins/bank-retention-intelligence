# Dicionário de dados

## customers.csv.gz

| Campo | Tipo | Descrição | Uso no modelo |
|---|---|---|---|
| customer_id | inteiro | Identificador sintético | Chave |
| signup_date | data | Entrada no banco | Origina tempo de relacionamento |
| state | texto | UF | Somente auditoria |
| age | inteiro | Idade sintética | Excluída |
| income | decimal | Renda sintética | Excluída diretamente |
| income_band | texto | Faixa de renda | Auditoria e recortes |
| acquisition_channel | texto | Canal de aquisição | Contexto |
| digital_affinity | decimal | Parâmetro interno da simulação | Não usado diretamente |
| has_credit_card | 0/1 | Possui cartão | Sim |
| has_personal_loan | 0/1 | Possui empréstimo | Sim |
| has_investment | 0/1 | Possui investimento | Indiretamente em produtos |
| credit_limit | decimal | Limite vigente | Sim |
| products_count | inteiro | Produtos contratados | Sim |
| monthly_contribution_margin | decimal | Margem mensal estimada | Sim, para valor |
| root_reason_synthetic | texto | Causa verdadeira inserida pelo gerador | Nunca usada no modelo |
| churn_month_synthetic | data | Mês artificial do churn | Nunca usada como variável |
| marketing_consent | 0/1 | Consentimento para contato | Regra de elegibilidade |

## monthly_activity.csv.gz

| Campo | Descrição |
|---|---|
| activity_month | Mês de referência |
| app_sessions | Acessos ao aplicativo |
| pix_in_count | Entradas por Pix |
| pix_out_count | Saídas por Pix |
| card_purchase_count | Compras no cartão |
| bill_payment_count | Pagamentos de contas |
| financial_txn_count | Total de atividades qualificantes |
| failed_txn_count | Falhas transacionais |
| salary_inflow | Indicador de entrada salarial |
| avg_balance | Saldo médio mensal |
| days_since_last_activity | Dias desde a última atividade |
| contact_pressure_30d | Contatos recebidos em 30 dias |

## support_tickets.csv.gz

| Campo | Descrição |
|---|---|
| ticket_month | Mês do atendimento |
| ticket_count | Chamados abertos |
| unresolved_count | Chamados ainda não resolvidos |
| nps | Nota sintética de recomendação |

## retention_experiment.csv.gz

| Campo | Descrição |
|---|---|
| experiment_segment | Segmento definido antes do tratamento |
| action | Braço aleatório do experimento |
| action_cost | Custo unitário |
| retained_60d | Retenção observada no horizonte |

## Definição do alvo

`churn_60d = 1` quando, ao final dos dois meses seguintes ao snapshot:

- a inatividade chega a 60 dias ou mais; e
- o cliente realizou no máximo uma transação financeira qualificante.

O alvo representa **perda de relacionamento**, não necessariamente encerramento formal da conta.

## Variáveis proibidas no treinamento

- `root_reason_synthetic`;
- `churn_month_synthetic`;
- qualquer dado posterior ao snapshot;
- idade;
- estado;
- resultado de campanha futura.

