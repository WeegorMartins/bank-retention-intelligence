# Como apresentar o projeto em entrevista

## Discurso de 90 segundos

“Eu construí um produto analítico de retenção para um banco digital fictício. O primeiro cuidado foi definir churn como perda de relacionamento, e não somente conta encerrada: 60 dias sem atividade financeira qualificante.

Criei snapshots temporais para impedir vazamento de informação, treinei uma regressão logística como referência e um modelo de gradiente como desafiante. Avaliei não apenas ROC-AUC, mas PR-AUC, lift e recall dentro de uma capacidade operacional de 10% da carteira.

O modelo estima risco, mas não define a abordagem. Em uma camada separada, diagnostiquei sinais prováveis, estimei retenção incremental a partir de um experimento com grupo de controle e calculei valor líquido considerando margem e custo.

A recomendação também respeita consentimento, saturação de contato e elegibilidade. Por isso, um cliente de alto risco pode receber a decisão de não contatar.

Por fim, disponibilizei o resultado em uma aplicação com visão executiva, fila operacional, cliente 360, qualidade, estabilidade e auditoria. Todos os dados são sintéticos e os impactos são estimativas, não resultados reais.”

## Perguntas técnicas prováveis

### Por que não usar acurácia?

Porque o churn é minoritário. Um modelo que prevê todo mundo como não churn pode ter acurácia alta e nenhuma utilidade. PR-AUC e métricas dentro da capacidade operacional são mais informativas.

### Por que criar uma regressão logística?

Ela funciona como referência transparente. O modelo mais complexo precisa demonstrar ganho real sobre uma alternativa simples.

### Por que separar diagnóstico de previsão?

Uma variável pode ajudar a prever sem representar uma causa. O diagnóstico é uma hipótese de ação que precisa ser validada experimentalmente.

### Como evitou vazamento?

As variáveis usam somente o snapshot e os dois meses anteriores. Os meses futuros são usados exclusivamente para construir o alvo.

### Por que o limiar não é 0,5?

O limiar depende da capacidade e do custo. A política principal seleciona dentro de uma capacidade de 10% e depois considera valor econômico.

### Como escolheu a ação?

Comparei cada braço do experimento com o controle no mesmo segmento, estimei retenção incremental suavizada e calculei o valor líquido esperado.

### Como lidaria com causalidade em produção?

Manteria aleatorização, grupo de controle, estratificação pré-tratamento, métricas de margem e guardrails de reclamação e descadastro.

### O que monitoraria?

Qualidade e atualização dos dados, PSI do escore, calibração, PR-AUC atrasada, lift, taxa de contato, reclamações, descadastro, retenção e margem incremental.

### Por que idade e estado não entram no modelo?

Para reduzir risco de tratamento inadequado e porque o objetivo é decidir com base em relacionamento e comportamento. Estado permanece apenas para auditoria de disparidades.

### Qual a maior limitação?

Os dados e experimentos são sintéticos. O projeto demonstra método e arquitetura, não prova impacto em uma carteira real.

## Perguntas de negócio

### Se o orçamento cair pela metade, o que fazer?

Reordenar pela razão entre valor líquido esperado e custo, aplicar limite por canal e preservar grupo de controle.

### Você contataria todos os clientes críticos?

Não. Alguns não têm consentimento, estão saturados, não possuem ação com efeito positivo ou têm valor esperado menor que o custo.

### Aumentar limite é ação de retenção?

Somente “encaminhar para avaliação” pode ser recomendado. A aprovação depende de política de crédito e capacidade de pagamento independentes.

### Como provar impacto?

Pela diferença incremental contra controle em retenção e margem, descontando custo e acompanhando efeitos adversos.

## Demonstração de cinco minutos

1. Abra a visão executiva e explique a decisão.
2. Mostre causas e valor em risco.
3. Mostre lift no top 10% e importância.
4. Abra a fila de ações e mostre um cliente.
5. Termine em governança, limitações e próximo experimento.

