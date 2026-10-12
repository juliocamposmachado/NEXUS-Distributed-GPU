<img width="825" height="1024" alt="image" src="https://github.com/user-attachments/assets/2c44b8fd-df11-4961-a974-09f279105b24" />


# NEXUS Distributed GPU

**Uma arquitetura experimental para processamento distribuído de inteligência artificial.**

O NEXUS Distributed GPU é um projeto experimental em Python que explora como distribuir tarefas computacionais entre diferentes workers, coordenar sua execução e reunir os resultados em um único sistema.

A visão do projeto é evoluir de um coordenador local para uma rede de processamento de IA capaz de utilizar recursos computacionais autorizados de múltiplas máquinas.

> **Estado do projeto:** protótipo inicial em desenvolvimento. A fila de tarefas e a comunicação entre coordenador e workers estão em fase experimental. A execução real de modelos em GPU e o paralelismo interno de modelos neurais ainda precisam ser implementados e validados.

## Visão

Criar uma infraestrutura na qual o usuário envie uma solicitação e o sistema encaminhe o trabalho aos recursos computacionais apropriados, sem exigir que o computador do usuário execute localmente todo o processamento pesado.

A arquitetura poderá evoluir para incluir:

- Coordenação de tarefas distribuídas.
- Workers executando tarefas especializadas.
- Detecção de recursos computacionais.
- Integração com modelos locais de inteligência artificial.
- Processamento de imagens e documentos.
- Monitoramento de recursos e consumo energético.
- Tolerância a falhas e recuperação de tarefas.
- Distribuição de modelos entre aceleradores compatíveis.

## Arquitetura inicial

```text
                 USUÁRIO / CLIENTE
                         |
                         v
                COORDENADOR NEXUS
                         |
                  FILA DE TAREFAS
                         |
             +-----------+-----------+
             |           |           |
             v           v           v
          WORKER 1    WORKER 2    WORKER N
             |           |           |
             +-----------+-----------+
                         |
                         v
                 RESULTADOS FINAIS
```

### Componentes

- **Coordenador:** recebe tarefas, mantém seus estados e disponibiliza trabalho aos workers.
- **Fila de tarefas:** organiza as solicitações pendentes.
- **Workers:** executam tarefas compatíveis e devolvem os resultados.
- **API HTTP:** permite registrar workers, enviar tarefas e consultar resultados.
- **Camada de recursos:** será expandida para considerar CPU, memória, GPUs e disponibilidade.
- **Camada de IA:** futura integração com modelos de linguagem, geração de imagens e outros mecanismos de inferência.

## Tecnologias

- Python 3.10 ou superior.
- FastAPI.
- Uvicorn.
- HTTPX.
- Pydantic.
- Git e GitHub.

## Requisitos

- Linux, incluindo Zorin OS.
- Python 3.10 ou superior.
- `python3-venv` disponível no sistema.
- Conexão com a internet para instalar dependências.

Uma GPU não é necessária para executar o protótipo inicial.

## Instalação

Clone o repositório:

```bash
git clone https://github.com/juliocamposmachado/NEXUS-Distributed-GPU.git
cd NEXUS-Distributed-GPU
```

Crie e ative o ambiente virtual:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Instale as dependências:

```bash
python -m pip install -r requirements.txt
```

## Executar o coordenador

```bash
python -m uvicorn nexus.coordinator:app \
  --host 127.0.0.1 \
  --port 8787
```

A API ficará disponível localmente em:

- Saúde: `http://127.0.0.1:8787/health`
- Documentação: `http://127.0.0.1:8787/docs`
- Workers: `http://127.0.0.1:8787/workers`
- Tarefas: `http://127.0.0.1:8787/tasks`

## Executar um worker

Em outro terminal:

```bash
cd NEXUS-Distributed-GPU
source .venv/bin/activate

python workers/worker.py --name worker-local-1
```

O worker registra seus recursos disponíveis e aguarda tarefas compatíveis.

## Enviar uma tarefa de teste

Com o coordenador e o worker em execução:

```bash
curl -X POST http://127.0.0.1:8787/tasks \
  -H 'Content-Type: application/json' \
  -d '{"kind":"demo","payload":{"text":"Olá, NEXUS Distributed GPU"}}'
```

A resposta contém o identificador da tarefa.

Consulte o estado e o resultado:

```bash
curl http://127.0.0.1:8787/tasks
```

A tarefa poderá aparecer como `queued`, `running`, `completed` ou `failed`.

## Roadmap

### Fase 1 — Coordenação
- [x] Estrutura inicial em Python.
- [x] API HTTP para tarefas e workers.
- [x] Fila de tarefas em memória.
- [x] Worker demonstrativo.
- [ ] Testes automatizados completos.
- [ ] Persistência de tarefas em SQLite.

### Fase 2 — Recursos computacionais
- [ ] Monitoramento de CPU e RAM.
- [ ] Detecção e monitoramento de GPUs.
- [ ] Medição de temperatura e consumo quando suportados.
- [ ] Agendamento por capacidade e disponibilidade.
- [ ] Heartbeats robustos e recuperação de workers indisponíveis.

### Fase 3 — Inteligência artificial
- [ ] Integração com modelos locais.
- [ ] Execução real de inferência em GPU.
- [ ] Processamento distribuído de tarefas de IA.
- [ ] Integração experimental com geração de imagens.
- [ ] Avaliação de desempenho e qualidade.

### Fase 4 — Rede distribuída
- [ ] Autenticação e autorização dos nós.
- [ ] Comunicação segura com TLS.
- [ ] Execução em máquinas remotas autorizadas.
- [ ] Recuperação de tarefas e tolerância a falhas.
- [ ] Observabilidade e métricas de eficiência.

### Fase 5 — Modelos distribuídos
- [ ] Pesquisa de paralelismo de modelos.
- [ ] Comunicação entre aceleradores compatíveis.
- [ ] Avaliação de latência e tráfego de rede.
- [ ] Comparação de desempenho e consumo energético.

## Princípios do projeto

1. Distribuir trabalho de maneira eficiente.
2. Reduzir a dependência do processamento local do usuário.
3. Aproveitar recursos computacionais disponíveis de forma autorizada.
4. Medir o desempenho antes de afirmar ganhos de velocidade ou eficiência energética.
5. Preservar a integridade e a confidencialidade dos dados.
6. Evoluir progressivamente, com testes reproduzíveis.

## Segurança

Esta versão é experimental e não está pronta para exposição pública na internet.

O coordenador inicial mantém o estado em memória e não implementa autenticação, TLS ou persistência. Use-o apenas em ambiente local e com dados não confidenciais.

Antes de habilitar comunicação remota, será necessário implementar autenticação dos workers, autorização por tarefa, validação de dados, limites de recursos, proteção contra abuso e comunicação criptografada.

Não execute código arbitrário recebido de máquinas remotas. Não envie informações sensíveis para workers que não sejam confiáveis.

## Contribuições

Contribuições, testes, sugestões de arquitetura e experimentos reproduzíveis são bem-vindos.

## Licença

A licença ainda será definida. Até que uma licença seja adicionada ao repositório, não presuma que o código esteja liberado para reutilização, redistribuição ou uso comercial.

---

**NEXUS Distributed GPU — explorando uma nova arquitetura para processamento distribuído de inteligência artificial.**
