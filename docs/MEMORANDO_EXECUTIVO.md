# Memorando executivo — Política de retenção Pulso

**Cenário:** banco digital fictício, dados 100% sintéticos  
**Snapshot de decisão:** maio de 2026  
**Horizonte de risco:** 60 dias

## Decisão solicitada

Autorizar um piloto controlado de retenção para clientes priorizados pelo valor líquido esperado, preservando grupo de controle, consentimento, limites de contato e regras independentes de crédito.

## Diagnóstico executivo

| Indicador | Resultado simulado |
|---|---:|
| Portfólio avaliado | 50.000 clientes |
| Risco alto ou crítico | 3.334 clientes |
| Valor anual em risco | R$ 481,7 mil |
| Clientes com ação economicamente elegível | 1.907 |
| Valor líquido esperado da política | R$ 26,4 mil |

As três maiores concentrações de valor em risco são:

1. **frustração com crédito:** aproximadamente R$ 221,2 mil;
2. **baixo engajamento:** aproximadamente R$ 152,7 mil;
3. **falha de atendimento:** aproximadamente R$ 56,2 mil.

Esses segmentos são hipóteses diagnósticas baseadas em comportamento observado. Não devem ser interpretados como causa individual comprovada.

## Evidência do modelo

- PR-AUC no teste temporal: **0,898**;
- ROC-AUC no teste temporal: **0,944**;
- recall dentro dos 10% priorizados: **87,1%**;
- lift dentro dos 10% priorizados: **8,7x**;
- avaliação fora da amostra em período posterior;
- idade e estado excluídos do modelo de decisão.

O ganho operacional está na concentração de clientes que efetivamente perdem relacionamento dentro de uma capacidade limitada, e não apenas em uma métrica global de classificação.

## Recomendação

Iniciar um piloto com capacidade limitada e filas ordenadas por valor líquido esperado. A política deve:

1. selecionar clientes por risco e valor;
2. escolher a ação com maior retenção incremental estimada;
3. descontar o custo da intervenção;
4. bloquear contatos sem consentimento ou com saturação recente;
5. encaminhar recomendações de crédito somente para avaliação independente;
6. reservar grupo de controle para medir retenção e margem incrementais.

Linhas com evidência baixa não devem entrar em implantação ampla. Primeiro devem passar por experimento controlado.

## Métricas do piloto

### Resultado principal

- retenção incremental em 60 dias;
- margem incremental líquida do custo;
- valor líquido por cliente elegível.

### Proteções

- reclamações e descadastros;
- frequência de contato;
- inadimplência e deterioração de risco, quando houver avaliação de crédito;
- disparidades de resultado entre grupos monitorados;
- estabilidade do escore e qualidade dos dados.

## Hipóteses que ainda precisam de validação

1. O efeito observado no experimento sintético permanece estável em novo período.
2. A margem mensal representa adequadamente o valor econômico retido.
3. O contato não aumenta reclamação, descadastro ou outros efeitos adversos.
4. A segmentação diagnóstica é operacionalmente acionável.
5. O ganho incremental permanece positivo após custos reais de canal e operação.

## Riscos de decisão

- falsos positivos e contato desnecessário;
- saturação e piora da experiência;
- mudança de comportamento da carteira;
- confusão entre correlação diagnóstica e causalidade;
- uso indevido da recomendação de “avaliar limite” como decisão de crédito;
- implantação ampla antes de evidência experimental suficiente.

## Próximo passo proposto

Executar experimento controlado, estratificado por causa provável e força da evidência, com leitura em 60 dias. A decisão de escala deve ocorrer somente se houver ganho incremental de retenção e margem, sem violação dos indicadores de proteção.

> Todos os números deste memorando vêm de uma simulação reproduzível. Eles demonstram método de decisão e não representam resultado financeiro realizado.
