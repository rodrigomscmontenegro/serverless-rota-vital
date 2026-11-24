
# Serverless — Rota Vital

Atividade Individual 1 — Serverless
Disciplina: Infraestrutura de Software
Curso: Análise e Desenvolvimento de Sistemas
Instituição: CESAR School — 2026.2

## 1. Sobre o projeto

Este projeto implementa uma função serverless responsável pela geração de guias de transporte de requisições do Rota Vital.

A função recebe os dados de uma requisição, valida seu identificador e retorna uma guia contendo as informações do hospital e das bolsas solicitadas.

O objetivo da atividade é observar, na prática:

- Invocação de funções por evento e por HTTP.
- Cold start e reutilização do ambiente de execução.
- Comportamento de variáveis globais entre invocações.
- Limites de tempo de execução (timeout).
- Modelo de cobrança do AWS Lambda.

## 2. Caminho escolhido

Foi escolhido o **Caminho A — AWS SAM CLI local**.

Toda a execução foi realizada localmente utilizando Docker e AWS SAM CLI, sem criação de recursos na nuvem ou necessidade de uma conta AWS.

Foi utilizado Python 3.14 em vez do Python 3.12 apresentado no roteiro da atividade.

## 3. Tecnologias utilizadas

| Tecnologia | Versão |
|---|---|
| Python | 3.14.7 |
| AWS SAM CLI | 1.174.0 |
| Docker Desktop | 4.100.1 |
| Docker Engine | 29.9.3 |
| WSL | 2 |
| pytest | 9.2.0 |

Também foram utilizados Git, GitHub, Visual Studio Code, PowerShell e Git Bash.

## 4. Estrutura do projeto

```text
serverless-rota-vital/
├── events/
│   ├── event.json
│   └── pedido.json
├── evidencias/
├── hello_world/
│   ├── __init__.py
│   ├── app.py
│   └── requirements.txt
├── tests/
│   ├── integration/
│   ├── unit/
│   │   └── test_handler.py
│   └── requirements.txt
├── .gitignore
├── README.md
├── samconfig.toml
└── template.yaml
```

Principais arquivos:

- `hello_world/app.py`: implementação da função Lambda.
- `template.yaml`: configuração da função, rota HTTP e timeout.
- `events/pedido.json`: evento utilizado nas invocações locais.
- `tests/unit/test_handler.py`: testes unitários da função.
- `evidencias/`: registros dos experimentos realizados.
- `samconfig.toml`: configurações do AWS SAM CLI.

## 5. Como executar

### 5.1. Pré-requisitos

- Python 3.14.
- Docker Desktop em execução.
- AWS SAM CLI.
- Git.

### 5.2. Clonar o repositório

```bash
git clone https://github.com/rodrigomscmontenegro/serverless-rota-vital.git
cd serverless-rota-vital
```

### 5.3. Validar e construir o projeto

```bash
sam validate
sam build
```

### 5.4. Invocação por evento

Execute o comando abaixo duas vezes:

```bash
sam local invoke -e events/pedido.json
```

O evento contém os dados da requisição R-001, do hospital H-Recife e da bolsa O-NEG-0142.

Exemplo do conteúdo retornado no body da resposta:

```json
{
  "guia": "G-R-001",
  "hospital": "H-Recife",
  "bolsas": ["O-NEG-0142"],
  "invocacaoNesteAmbiente": 1
}
```

O status retornado pela função é 201.

### 5.5. Invocação por HTTP

Inicie o servidor local:

```bash
sam local start-api
```

Em outro terminal, utilizando Git Bash, execute:

```bash
curl -i -X POST http://127.0.0.1:3000/guias \
  -H "Content-Type: application/json" \
  -d '{"requisicaoId":"R-002","hospital":"H-Caruaru"}'
```

Resposta esperada:

```json
{
  "guia": "G-R-002",
  "hospital": "H-Caruaru",
  "bolsas": [],
  "invocacaoNesteAmbiente": 1
}
```

O status HTTP esperado é `201 Created`.

Repita a requisição três vezes para observar o contador.

### 5.6. Reutilização do ambiente

Encerre o servidor anterior com `Ctrl + C` e execute:

```bash
sam local start-api --warm-containers LAZY
```

Repita a requisição HTTP três vezes.

Nesse modo, o container é inicializado na primeira requisição e pode ser reutilizado nas chamadas seguintes.

### 5.7. Experimento de timeout

O projeto está configurado com timeout de 10 segundos.

Para reproduzir o experimento inicial, encerre o servidor e altere temporariamente o `template.yaml`:

```yaml
Globals:
  Function:
    Timeout: 3
```

Reconstrua o projeto e inicie o servidor:

```bash
sam build
sam local start-api --warm-containers LAZY
```

Em outro terminal, execute:

```bash
curl -i -X POST http://127.0.0.1:3000/guias \
  -H "Content-Type: application/json" \
  -d '{"requisicaoId":"R-003","demorar":true}'
```

A função tenta aguardar 5 segundos, mas é interrompida pelo limite de 3 segundos.

Depois, encerre o servidor, altere o timeout para 10 segundos e execute novamente:

```bash
sam build
sam local start-api --warm-containers LAZY
```

Repita a requisição. A função deverá concluir a execução e retornar HTTP 201.

### 5.8. Testes unitários

No PowerShell, crie e ative um ambiente virtual:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Instale o pytest:

```powershell
python -m pip install -r tests/requirements.txt
```

Execute os testes:

```powershell
python -m pytest tests/unit -v
```

Foram implementados seis testes unitários:

- Geração da guia de transporte.
- Ausência do identificador da requisição.
- Valor padrão da lista de bolsas.
- Ausência do hospital.
- Incremento do contador de invocações.
- Simulação de uma requisição demorada.

Os seis testes passaram durante o desenvolvimento.

Os testes de integração do template original não fazem parte da validação local realizada nesta atividade.

## 6. Resultados dos experimentos

### 6.1. Invocações isoladas

Foram realizadas duas invocações utilizando `sam local invoke`.

| Métrica | Primeira invocação | Segunda invocação |
|---|---:|---:|
| Init Duration | 0,03 ms | 0,03 ms |
| Duration | 56,56 ms | 510,30 ms |
| Billed Duration | 57 ms | 511 ms |
| Memória configurada | 128 MB | 128 MB |
| Contador | 1 | 1 |

Na primeira execução, foi necessário preparar a imagem do ambiente Lambda no Docker.

Apesar disso, a duração registrada pelo SAM foi maior na segunda invocação. As duas execuções utilizaram containers diferentes, sem reaproveitamento do ambiente da função.

Os tempos apresentados correspondem aos logs do SAM, e não ao tempo total de execução do comando no terminal.

### 6.2. Reutilização do ambiente de execução

| Configuração | 1ª chamada | 2ª chamada | 3ª chamada |
|---|---:|---:|---:|
| Sem warm containers | 1 | 1 | 1 |
| EAGER | 1 | 2 | 3 |
| LAZY | 1 | 2 | 3 |

Inicialmente, o arquivo `samconfig.toml` possuía a configuração EAGER para o comando `start-api`.

Essa configuração foi removida para permitir a comparação entre execuções sem reaproveitamento e com reaproveitamento explícito dos containers.

No modo LAZY, foram registrados os seguintes tempos:

| Invocação | Duration |
|---|---:|
| Primeira | 44,21 ms |
| Segunda | 1,37 ms |
| Terceira | 1,04 ms |

As chamadas seguintes apresentaram menor duração e reutilizaram o ambiente de execução.

### 6.3. Timeout

| Timeout configurado | Duração registrada | Status HTTP | Resultado |
|---|---:|---:|---|
| 3 segundos | 3.000 ms | 502 | Execução interrompida |
| 10 segundos | 5.058,63 ms | 201 | Guia gerada |

Com o timeout de 3 segundos, a função foi interrompida antes de concluir a espera de 5 segundos.

Após aumentar o limite para 10 segundos, a execução foi concluída e a guia G-R-003 foi gerada.

### 6.4. Validação HTTP com curl

Os experimentos iniciais foram realizados utilizando `Invoke-RestMethod` no PowerShell.

Posteriormente, a chamada HTTP também foi validada utilizando `curl` no Git Bash, retornando `201 Created` e a guia G-R-002.

## 7. Respostas às questões

### 1. Por que a primeira invocação demorou mais que a segunda? O que acontece na fase de Init?

Normalmente, a primeira invocação pode demorar mais porque o ambiente de execução precisa ser inicializado. Esse processo é conhecido como cold start.

Na fase de Init, o Lambda inicializa o runtime, carrega as dependências e executa o código que está fora do handler, como a inicialização das variáveis globais.

Nas duas invocações isoladas que realizei, a segunda apresentou uma duração maior que a primeira. As duas utilizaram containers diferentes, portanto não houve reaproveitamento do ambiente de execução.

Já no experimento com warm containers no modo LAZY, a primeira chamada apresentou duração de 44,21 ms, enquanto as seguintes apresentaram 1,37 ms e 1,04 ms.

Esse segundo experimento demonstrou melhor a diferença entre a primeira execução e as execuções que reutilizam um ambiente já inicializado.

### 2. O que o campo invocacaoNesteAmbiente mostrou com e sem --warm-containers? O que isso diz sobre guardar estado numa variável global da função?

Sem warm containers, o contador retornou 1 em todas as chamadas, pois cada execução utilizou um novo ambiente.

Com warm containers, o contador retornou 1, 2 e 3, demonstrando que a variável global manteve seu valor enquanto o mesmo ambiente foi reutilizado.

Porém, esse comportamento não é garantido no AWS Lambda. O ambiente pode ser encerrado ou substituído, e diferentes invocações podem utilizar ambientes distintos.

Por isso, informações importantes não devem depender de variáveis globais.

### 3. O que aconteceu com demorar = true? Qual é o tempo máximo de uma execução no Lambda, e o que fazer com um trabalho mais longo?

Ao enviar `demorar = true`, a função executou uma espera de 5 segundos.

Como o timeout inicial era de 3 segundos, a execução foi interrompida e o servidor local retornou HTTP 502.

Depois de aumentar o timeout para 10 segundos, a função conseguiu concluir a execução em aproximadamente 5 segundos e retornou HTTP 201.

O tempo máximo de execução de uma função AWS Lambda é de 900 segundos, ou 15 minutos.

Para trabalhos mais longos, é possível dividir o processamento em etapas menores, utilizar filas de mensagens e orquestrar as etapas com AWS Step Functions. Outra alternativa é utilizar serviços como AWS ECS ou AWS Batch, dependendo das características do processamento.

### 4. Quanto custa um milhão de execuções desta função com 128 MB e 100 ms?

Considerando os preços de us-east-1 apresentados na aula:

- Requisições: US$ 0,20 por milhão.
- Processamento: US$ 0,0000166667 por GB-s.
- Memória: 128 MB.
- Duração: 100 ms.
- Quantidade: 1.000.000 de execuções.

Conversão da memória:

```text
128 / 1024 = 0,125 GB
```

Conversão da duração:

```text
100 / 1000 = 0,1 segundo
```

Consumo por execução:

```text
0,125 × 0,1 = 0,0125 GB-s
```

Consumo total:

```text
0,0125 × 1.000.000 = 12.500 GB-s
```

Custo de processamento:

```text
12.500 × 0,0000166667 = US$ 0,20833375
```

Custo total:

```text
US$ 0,20833375 + US$ 0,20 = US$ 0,40833375
```

Portanto, o custo estimado é de aproximadamente **US$ 0,41 por milhão de execuções**, desconsiderando a camada gratuita e possíveis custos de outros serviços.

### 5. Em que parte do Rota Vital uma função assim faria sentido, e em qual não faria?

Uma função serverless faria sentido na geração de guias de transporte, pois essa operação acontece quando uma requisição é recebida e pode ser executada em pouco tempo.

Também poderia ser utilizada para enviar notificações ou processar eventos relacionados à movimentação das bolsas.

Por outro lado, não seria adequada para manter continuamente uma conexão de rastreamento em tempo real durante todo o transporte ou para executar um processamento único que ultrapasse o limite de 15 minutos.

Nesses casos, seria mais adequado utilizar serviços que suportem processos contínuos ou dividir o trabalho em etapas independentes.

## 8. Evidências

| Evidência | Descrição |
|---|---|
| [01](evidencias/01-primeira-invocacao.png) | Primeira invocação por evento |
| [02](evidencias/02-segunda-invocacao.png) | Segunda invocação por evento |
| [03](evidencias/03-http-configuracao-padrao.png) | Chamadas HTTP com configuração EAGER |
| [04](evidencias/04-http-sem-warm-containers.png) | Chamadas sem reutilização de containers |
| [05](evidencias/05-http-warm-lazy.png) | Chamadas com warm containers LAZY |
| [06](evidencias/06-timeout-3s-logs.png) | Erro com timeout de 3 segundos |
| [07](evidencias/07-timeout-10s-resposta.png) | Resposta com timeout de 10 segundos |
| [08](evidencias/08-timeout-10s-logs.png) | Logs da execução bem-sucedida |
| [09](evidencias/09-http-curl.png) | Validação HTTP utilizando curl |

## 9. Uso de IA

**Ferramenta:** ChatGPT (OpenAI).

**Finalidade:** auxílio na configuração do ambiente, compreensão dos conceitos de serverless, implementação e revisão dos testes unitários, interpretação dos logs, resolução de problemas durante os experimentos, organização do repositório e elaboração da documentação.

**Validação:** os comandos foram executados localmente, os resultados foram conferidos nos terminais, os testes unitários foram executados com pytest e os experimentos foram registrados por meio de capturas de tela.

Os valores apresentados neste README correspondem aos resultados observados durante os experimentos.

O uso de inteligência artificial foi realizado como ferramenta de apoio ao desenvolvimento e à aprendizagem, conforme a orientação da atividade e a política PO-CESAR-021.

## Referências

- [Documentação do AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/what-is-sam.html)
- [Ciclo de vida do ambiente de execução do Lambda](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html)
- [Limites do AWS Lambda](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html)
- [Preços do AWS Lambda](https://aws.amazon.com/lambda/pricing/)
- Material da Aula 007 — Serverless, CESAR School.
