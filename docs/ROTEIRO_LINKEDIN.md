# Roteiro de publicação no LinkedIn

## Título do primeiro post

**Um cliente não precisa encerrar a conta para dar churn em um banco digital.**

## Texto-base

Em serviços financeiros, uma conta pode permanecer aberta enquanto deixa de receber salário, fazer Pix, pagar contas ou movimentar o cartão.

Por isso, construí o Pulso: um produto analítico para diagnosticar perda de relacionamento em 60 dias e recomendar a próxima melhor ação.

O desafio não era apenas prever quem poderia sair.

O produto precisava responder:

- quais sinais sustentam o risco;
- qual valor financeiro está exposto;
- qual ação apresentou retenção incremental para clientes semelhantes;
- se o benefício esperado paga o custo;
- se o cliente possui consentimento e não está saturado de contatos.

Usei uma base 100% sintética e reproduzível, com conta, Pix, cartão, saldo, aplicativo, atendimento, falhas transacionais e campanhas.

A solução contém:

- snapshots temporais sem vazamento de dados futuros;
- SQL, Python e dbt;
- baseline e modelo desafiante;
- avaliação por PR-AUC, lift e recall com capacidade fixa;
- experimento com grupo de controle;
- diagnóstico de causas;
- política de próxima melhor ação;
- aplicação interativa;
- testes, governança e monitoramento.

Na simulação com 50 mil clientes, o modelo alcançou PR-AUC de 0,898 e concentrou 87,1% dos churns nos 10% priorizados. A política identificou R$ 481,7 mil de valor anual em risco e estimou R$ 26,4 mil de valor líquido — sempre tratados como resultados simulados, não como impacto realizado.

O principal aprendizado foi simples:

> risco de churn não é recomendação de contato.

A decisão correta depende de risco, efeito incremental, valor, custo, consentimento e elegibilidade.

Aplicação: https://pulso-retencao-inteligente.streamlit.app/

Repositório e documentação: https://github.com/WeegorMartins/bank-retention-intelligence

## Carrossel de dez páginas

1. Um cliente não precisa fechar a conta para dar churn.
2. Como defini perda de relacionamento em 60 dias.
3. Quais dados o banco fictício possui.
4. Como evitei vazamento temporal.
5. Onde o modelo concentra os churners.
6. Como transformei previsão em diagnóstico.
7. Por que usei grupo de controle.
8. Como calculei a ação de maior valor.
9. Consentimento, saturação e governança.
10. Demonstração e documentação.

## Sequência de cinco posts

### Post 1 — Problema e definição

Explique churn de relacionamento versus conta encerrada.

### Post 2 — Engenharia analítica

Mostre snapshots, linhagem, testes e corte temporal.

### Post 3 — Modelo

Mostre PR-AUC, lift e capacidade fixa, sem transformar AUC em protagonista.

### Post 4 — Decisão

Explique valor incremental líquido e por que alto risco pode resultar em não contatar.

### Post 5 — Governança

Mostre atributos excluídos, consentimento, saturação e monitoramento.

## O que não escrever

- “Meu modelo gerou milhões para o banco.”
- “A inteligência artificial descobriu a causa real de cada cliente.”
- “O modelo possui 99% de acurácia.”
- “Aumentar limite reduz churn.”
- “A solução está pronta para produção real.”

Use “estimativa simulada”, “hipótese diagnóstica”, “efeito observado no experimento sintético” e “protótipo de produto analítico”.
