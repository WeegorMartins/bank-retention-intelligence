# Guia completo, clique a clique

## Pulso — Diagnóstico de Churn e Próxima Melhor Ação

Este guia parte do zero. Você não precisa instalar Python no seu computador. Todo o desenvolvimento pode ser feito pelo navegador usando GitHub Codespaces, e a aplicação pode ser publicada no Streamlit Community Cloud.

## Resultado final

Ao terminar, você terá:

- repositório público no GitHub;
- base bancária sintética e reproduzível;
- produto de dados mensal em SQL/dbt;
- modelo de risco de churn;
- diagnóstico individual de causas;
- experimento de retenção com grupo de controle;
- recomendação de ação baseada em valor incremental;
- aplicação pública com seis áreas;
- testes automáticos;
- documentação para recrutadores e equipes técnicas.

---

# Fase 1 — Entender o problema antes do código

## 1.1 O banco fictício

O banco chama-se **Pulso Bank** apenas dentro do projeto. Ele oferece:

- conta digital;
- Pix;
- cartão;
- pagamento de contas;
- empréstimo pessoal;
- investimentos;
- atendimento digital.

Não use o nome, logotipo ou identidade visual da Neon, PicPay ou de qualquer instituição real. O projeto é inspirado no tipo de problema de uma fintech, não em dados ou sistemas dessas empresas.

## 1.2 O que é churn neste projeto

Churn não será “cliente que fechou a conta”. Em banco digital, uma conta pode continuar aberta e deixar de ser a conta principal.

Definição operacional:

> Cliente que chega a 60 dias sem atividade financeira qualificante e realiza no máximo uma transação durante o horizonte observado.

Atividades qualificantes:

- Pix;
- compra no cartão;
- pagamento de conta;
- outra movimentação financeira.

Não contam isoladamente:

- abrir o aplicativo;
- receber comunicação;
- visualizar uma oferta.

## 1.3 Data de observação e horizonte

- Snapshot principal: maio de 2026.
- Dados usados como variáveis: março, abril e maio de 2026.
- Horizonte do alvo: junho e julho de 2026.

Nunca use junho ou julho para criar as variáveis do snapshot de maio. Isso seria vazamento de informação futura.

## 1.4 Decisão a ser apoiada

O produto não responderá apenas “quem pode sair?”. Ele responderá:

1. Qual o risco?
2. Quais sinais sustentam esse risco?
3. Qual o valor anual em risco?
4. Qual ação funcionou melhor em experimento para clientes semelhantes?
5. O retorno esperado paga o custo?
6. O cliente pode e deve ser contatado?

---

# Fase 2 — Criar as contas gratuitas

## 2.1 GitHub

1. Abra `https://github.com`.
2. Clique em **Sign up** se ainda não possuir conta.
3. Informe e-mail, senha e nome de usuário.
4. Confirme o e-mail.
5. Entre na conta.

Contas pessoais possuem uma franquia mensal gratuita de Codespaces. A franquia pode mudar, por isso confirme na documentação oficial antes de iniciar uma execução muito longa:

`https://docs.github.com/billing/managing-billing-for-github-codespaces/about-billing-for-github-codespaces`

## 2.2 Streamlit Community Cloud

Não é necessário criar agora, mas você usará ao final.

1. Abra `https://share.streamlit.io`.
2. Clique em **Continue with GitHub**.
3. Autorize a conexão.

Documentação oficial:

`https://docs.streamlit.io/deploy/streamlit-community-cloud`

---

# Fase 3 — Criar o repositório

## 3.1 Criar no GitHub

1. No canto superior direito do GitHub, clique no símbolo **+**.
2. Clique em **New repository**.
3. Em **Repository name**, escreva:

```text
bank-retention-intelligence
```

4. Em **Description**, cole:

```text
Diagnóstico de churn e recomendação de próxima melhor ação para um banco digital fictício.
```

5. Marque **Public**.
6. Não adicione README, `.gitignore` ou licença nessa tela, pois o pacote já possui esses arquivos.
7. Clique em **Create repository**.

## 3.2 Abrir o Codespaces

1. Dentro do repositório, clique no botão verde **Code**.
2. Abra a aba **Codespaces**.
3. Clique em **Create codespace on main**.
4. Aguarde abrir uma tela semelhante ao Visual Studio Code.
5. Se aparecer uma tela de boas-vindas, feche-a.

## 3.3 Enviar os arquivos deste projeto

Você receberá um arquivo ZIP com todo o projeto.

1. Baixe o ZIP.
2. No seu computador, não altere o conteúdo.
3. No Codespaces, arraste o ZIP para o painel esquerdo de arquivos.
4. Aguarde o envio terminar.
5. No menu superior, clique em **Terminal**.
6. Clique em **New Terminal**.
7. Execute, trocando o nome se necessário:

```bash
unzip bank-retention-intelligence.zip -d /tmp/pulso-project
```

8. Copie os arquivos para o repositório:

```bash
cp -r /tmp/pulso-project/bank-retention-intelligence/. .
```

9. No painel esquerdo, localize o ZIP enviado.
10. Clique com o botão direito nele e escolha **Delete**.

Confirme que aparecem as pastas `src`, `dbt`, `docs`, `sql`, `tests` e o arquivo `app.py`.

---

# Fase 4 — Preparar o ambiente Python

## 4.1 Criar ambiente virtual

No terminal do Codespaces:

```bash
python -m venv .venv
```

Ative:

```bash
source .venv/bin/activate
```

O início da linha do terminal deve passar a mostrar `(.venv)`.

## 4.2 Instalar ferramentas

```bash
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
```

Espere até o terminal voltar a aceitar comandos. Não feche a página durante a instalação.

## 4.3 Confirmar instalação

```bash
python --version
streamlit --version
dbt --version
```

---

# Fase 5 — Executar primeiro com uma base pequena

Não comece com 50 mil clientes. Primeiro valide o fluxo com 5 mil:

```bash
python -m src.run_pipeline --customers 5000
```

O terminal executará cinco etapas:

1. geração dos dados;
2. validação dos contratos;
3. construção dos snapshots;
4. treinamento e avaliação;
5. diagnóstico e recomendação.

Ao final, procure a mensagem:

```text
Pipeline concluído.
```

## 5.1 Conferir os arquivos

No painel esquerdo:

1. Abra `data/raw`.
2. Confirme os arquivos de clientes, atividade, atendimento e experimento.
3. Abra `outputs`.
4. Confirme previsões, recomendações, métricas, importância, decis e resumo executivo.
5. Abra `models`.
6. Confirme `churn_champion.joblib`.

## 5.2 Validar a qualidade

```bash
python -m src.validate_data
```

O campo `status` deve ser `passed`.

## 5.3 Rodar testes unitários

```bash
pytest -q
```

O resultado esperado é que os testes sejam aprovados.

---

# Fase 6 — Entender o código, arquivo por arquivo

## 6.1 `src/config.py`

Centraliza:

- caminhos;
- semente aleatória;
- quantidade padrão de clientes;
- meses;
- snapshots;
- lista oficial de variáveis.

Abra o arquivo clicando em `src` e depois em `config.py`.

A lista `MODEL_FEATURES` é um contrato: somente essas variáveis entram no modelo. Idade, estado e causa sintética não aparecem nela.

## 6.2 `src/generate_data.py`

Cria quatro fontes.

### Cadastro

Possui produtos, tempo de relacionamento, margem, consentimento e atributos de auditoria.

### Comportamento mensal

Simula acessos, transações, Pix, cartão, contas, saldo, salário, falhas e pressão de contato.

### Atendimento

Simula chamados, pendências e NPS.

### Experimento

Distribui aleatoriamente clientes entre:

- controle;
- incentivo de Pix;
- educação;
- contato humano;
- avaliação de limite.

O gerador inclui clientes que saem repentinamente e clientes que ficam temporariamente inativos, mas voltam. Isso impede um desempenho artificialmente perfeito.

Execute somente essa etapa assim:

```bash
python -m src.generate_data --customers 5000
```

## 6.3 `src/validate_data.py`

Testa:

- chave única;
- ausência de identificador vazio;
- uma linha por cliente e mês;
- valores não negativos;
- integridade entre tabelas;
- existência de grupo de controle;
- alvo experimental binário.

Se um contrato falhar, o pipeline deve parar. Isso é proposital.

## 6.4 `src/build_features.py`

Para cada snapshot:

1. lê somente os três meses anteriores;
2. agrega comportamento;
3. calcula tendências;
4. une atendimento;
5. observa os dois meses futuros apenas para formar o alvo;
6. salva uma linha por cliente e snapshot.

Variáveis importantes:

- tendência de transações;
- tendência de acessos;
- tendência de saldo;
- meses com entrada salarial;
- falhas transacionais;
- chamados não resolvidos;
- dias desde a última atividade;
- quantidade de produtos;
- valor anual em risco.

Execute isoladamente:

```bash
python -m src.build_features
```

## 6.5 `src/train_model.py`

O arquivo treina:

- regressão logística como referência;
- gradiente impulsionado por histogramas como desafiante.

Separação temporal:

- janeiro a março: treino inicial;
- abril: validação e seleção;
- maio: teste final;
- junho e julho: horizonte do alvo de maio.

Métrica principal: PR-AUC, adequada quando o evento é minoritário.

Também calcula:

- ROC-AUC;
- Brier;
- precisão;
- recall;
- lift;
- recall no top 10%;
- decis;
- calibração;
- PSI do escore;
- importância por permutação.

Por que top 10%? Porque uma operação real não consegue falar com todos. O modelo precisa ser avaliado dentro de uma capacidade operacional.

Execute:

```bash
python -m src.train_model
```

## 6.6 `src/recommend_actions.py`

Este é o principal diferencial do projeto.

Primeiro, o código cria uma hipótese de causa:

- atendimento não resolvido;
- fricção no aplicativo;
- frustração com crédito;
- perda de entrada salarial;
- baixo engajamento;
- pressão financeira.

Depois, mede a retenção de cada ação contra o controle dentro do segmento. A estimativa utiliza suavização para evitar conclusões exageradas em grupos pequenos.

Finalmente, calcula:

```text
risco × retenção incremental × valor anual − custo
```

Restrições:

- sem consentimento, algumas comunicações são bloqueadas;
- alta pressão de contato bloqueia nova abordagem;
- avaliação de limite exige cartão existente;
- valor negativo resulta em não contatar;
- baixo risco pode resultar em não contatar.

Importante: encaminhar para avaliação de limite não significa aprovar aumento. Risco de crédito deve ser avaliado por política independente.

Execute:

```bash
python -m src.recommend_actions
```

## 6.7 `app.py`

Transforma os resultados em seis áreas:

1. visão executiva;
2. diagnóstico;
3. desempenho;
4. próxima melhor ação;
5. cliente 360;
6. governança.

O aplicativo não treina o modelo. Ele lê resultados já validados. Essa separação reduz tempo de abertura e diferencia produção de exploração.

---

# Fase 7 — Abrir a aplicação

No terminal:

```bash
streamlit run app.py --server.port 8501
```

O Codespaces mostrará uma mensagem sobre a porta 8501.

1. Clique em **Open in Browser**.
2. Se não aparecer, abra a aba **Ports** na parte inferior.
3. Localize a porta `8501`.
4. Clique no ícone de globo ou em **Open in Browser**.

Percorra todas as páginas e confira se os gráficos aparecem.

Para interromper, volte ao terminal e pressione:

```text
Ctrl + C
```

---

# Fase 8 — Executar a camada SQL/dbt

Depois de gerar os dados, execute:

```bash
dbt build --project-dir dbt --profiles-dir dbt
```

O comando deve:

- criar as visões de clientes, atividade e atendimento;
- criar a tabela analítica mensal;
- testar chaves e valores;
- validar integridade entre clientes e atividades;
- executar testes singulares.

## 8.1 Gerar documentação

```bash
dbt docs generate --project-dir dbt --profiles-dir dbt
dbt docs serve --project-dir dbt --profiles-dir dbt --port 8080
```

1. Abra a aba **Ports**.
2. Localize `8080`.
3. Clique em **Open in Browser**.
4. Explore a documentação e a linhagem.

Interrompa com `Ctrl + C`.

---

# Fase 9 — Executar a versão completa

Agora gere 50 mil clientes:

```bash
python -m src.run_pipeline --customers 50000
```

Não use o computador para outro processamento pesado enquanto a execução estiver ocorrendo. Ao terminar:

```bash
streamlit run app.py --server.port 8501
```

Registre os resultados reais gerados pela sua execução no arquivo:

```text
docs/MEMORANDO_EXECUTIVO.md
```

Não copie números exemplificativos de outro lugar.

---

# Fase 10 — Versionar no GitHub

## 10.1 Conferir alterações

```bash
git status
```

Os dados brutos e o modelo completo são ignorados. Os resultados compactos necessários para a demonstração podem ser versionados.

## 10.2 Adicionar

```bash
git add .
```

## 10.3 Criar o primeiro commit

```bash
git commit -m "feat: cria produto analitico de retencao bancaria"
```

## 10.4 Enviar

```bash
git push origin main
```

Volte à página do repositório e atualize. O README deve aparecer formatado.

## 10.5 Fixar tópicos

1. Na página do repositório, localize **About**.
2. Clique no ícone de engrenagem.
3. Adicione:

```text
churn
product-analytics
banking
python
sql
dbt
streamlit
machine-learning
experimentation
next-best-action
```

4. Salve.

---

# Fase 11 — Publicar gratuitamente no Streamlit

Antes de publicar, confirme que estes arquivos aparecem no GitHub:

- `app.py`;
- `requirements.txt`;
- `outputs/churn_predictions.csv.gz`;
- `outputs/next_best_actions.csv.gz`;
- `outputs/model_metrics.json`;
- `outputs/executive_summary.json`;
- `data/raw/manifest.json`.

Depois:

1. Abra `https://share.streamlit.io`.
2. Entre com GitHub.
3. Clique em **Create app**.
4. Escolha seu repositório `bank-retention-intelligence`.
5. Em **Branch**, selecione `main`.
6. Em **Main file path**, informe `app.py`.
7. Escolha um endereço como `pulso-retention-intelligence`.
8. Clique em **Deploy**.
9. Aguarde a instalação.
10. Abra o endereço público.

Se a aplicação informar que faltam resultados, volte ao GitHub e verifique se os arquivos compactos da pasta `outputs` foram enviados.

---

# Fase 12 — O que mostrar ao recrutador

Não comece a apresentação pela acurácia. Use esta ordem:

1. perda de relacionamento em banco digital;
2. definição operacional do churn;
3. corte temporal e prevenção de vazamento;
4. diagnóstico das causas;
5. experimento com grupo de controle;
6. valor incremental líquido;
7. regras de consentimento e elegibilidade;
8. capacidade operacional;
9. monitoramento e limitações;
10. demonstração pública.

Frase central:

> O modelo não decide quem deve receber uma oferta. Ele estima risco. A política de decisão combina risco, causa provável, efeito incremental, valor, custo e elegibilidade.

---

# Fase 13 — Erros comuns

## `ModuleNotFoundError`

Ative o ambiente e instale novamente:

```bash
source .venv/bin/activate
pip install -r requirements-dev.txt
```

## `streamlit: command not found`

```bash
source .venv/bin/activate
python -m streamlit run app.py
```

## A aplicação diz que os resultados não existem

```bash
python -m src.run_pipeline --customers 5000
```

## O dbt não encontra os CSVs

Confirme que o terminal está na raiz do repositório:

```bash
pwd
ls data/raw
```

Depois rode novamente:

```bash
dbt build --project-dir dbt --profiles-dir dbt
```

## O GitHub não enviou os arquivos

```bash
git status
git add .
git commit -m "fix: atualiza artefatos da demonstracao"
git push origin main
```

## O Codespaces parou

1. Abra o repositório no GitHub.
2. Clique em **Code**.
3. Abra **Codespaces**.
4. Clique no codespace existente.
5. Reative o ambiente virtual.

```bash
source .venv/bin/activate
```

---

# Checklist final

- [ ] O README abre corretamente.
- [ ] A base está identificada como sintética.
- [ ] O pipeline completo funciona.
- [ ] Os testes de dados passam.
- [ ] Os testes unitários passam.
- [ ] O dbt build passa.
- [ ] O corte temporal está documentado.
- [ ] Idade e estado não entram no modelo.
- [ ] O grupo de controle existe.
- [ ] O valor considera custo.
- [ ] Consentimento e saturação são respeitados.
- [ ] A aplicação abre publicamente.
- [ ] O post não apresenta impacto simulado como resultado real.

