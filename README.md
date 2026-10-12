 <img width="825" height="1024" alt="image" src="https://github.com/user-attachments/assets/2c44b8fd-df11-4961-a974-09f279105b24" />

# NEXUS Distributed GPU: Plataforma Heterogênea de Computação e Inferência de IA

[![Architecture](https://img.shields.io/badge/Architecture-Modular%20Heterogeneous%20Grid-cyan)](#)
[![Python Engine](https://img.shields.io/badge/Python-3.12%20FastAPI-blue)](#)
[![Frontend](https://img.shields.io/badge/Frontend-React%2018%20%7C%20Tailwind%20%7C%20shadcn-emerald)](#)
[![Tests](https://img.shields.io/badge/Tests-5%2F5%20Passing-brightgreen)](#)
[![Benchmarks](https://img.shields.io/badge/Throughput-247.8%20jobs%2Fs-purple)](#)

O **NEXUS Distributed GPU** é uma plataforma de pesquisa e engenharia de software desenhada para agregar, orquestrar e particionar recursos computacionais heterogêneos (CPUs multi-core, GPUs dedicadas NVIDIA/AMD, Apple Silicon Metal e aceleradores integrados) entre múltiplos computadores em rede local ou híbrida para cargas de trabalho de Inteligência Artificial.

---

## 1. Visão Geral da Arquitetura

O sistema implementa uma separação estrita entre o plano de controle, o plano de dados e a camada de execução:

```
                                    +-----------------------------+
                                    |   NEXUS Web Platform (UI)   |
                                    | (React, TypeScript, Tailwind)|
                                    +--------------+--------------+
                                                   | HTTP / REST / SSE
                                                   v
+--------------------------------------------------------------------------------------------------+
|                                    CONTROL PLANE COORDINATOR                                      |
|                                                                                                  |
|   +--------------------+   +-----------------------+   +------------------+   +--------------+   |
|   | Worker Discovery   |   | Intelligent Scheduler |   | Watchdog Failover|   | SHA-256 Cache|   |
|   | & Heartbeat Ping   |   | (4 Adaptive Policies) |   | & Task Recovery  |   | (Content-Add)|   |
|   +--------------------+   +-----------------------+   +------------------+   +--------------+   |
+------------------------------------------+-------------------------------------------------------+
                                           | Tasks Dispatch & Activations
           +-------------------------------+-------------------------------+
           |                               |                               |
           v                               v                               v
+-----------------------+       +-----------------------+       +-----------------------+
|   Worker Node Alpha   |       |   Worker Node Beta    |       |   Worker Node Gamma   |
|   (NVIDIA RTX 4090)   |       |   (AMD Radeon 7900)   |       |   (Intel Xeon CPU)    |
|   - LLM Inference     |       |   - Pipeline Stage 2  |       |   - Data Parallel     |
|   - MoE Specialist    |       |   - Math Specialist   |       |   - Text Embedding    |
+-----------------------+       +-----------------------+       +-----------------------+
```

### Principais Componentes Implementados

1. **Control Plane (`nexus/coordinator.py`):**
   - Registro de nós com capacidades detalhadas (VRAM, RAM, Threads, Sensores de Temperatura e Consumo em Watts).
   - Fila de tarefas com prioridade e suporte a múltiplos paradigmas (LLM, Data Parallel, Pipeline Parallel, MoE).
   - Agendador inteligente adaptativo com 4 políticas: `balanced`, `latency_first`, `memory_first`, `energy_aware`.
   - Monitor de integridade em background (*Heartbeat Watchdog*) com recuperação automática e reagendamento de tarefas em caso de queda de worker.
   - Cache de ativações e resultados endereçado por conteúdo (SHA-256) com controle de TTL.

2. **Worker Runtime Seguro (`workers/worker.py`):**
   - Detecção automática de hardware (CPU, RAM, GPU via CUDA/Metal/ROCm com fallbacks robustos).
   - **Arquitetura Zero-RCE:** Proibição de execução de código remoto ou desserialização insegura (Pickle). Apenas tarefas estritamente declarativas do catálogo homologado são executadas.

3. **Plataforma Web Interativa (`src/`):**
   - **Dashboard:** Painel em tempo real com métricas globais de VRAM/RAM agregadas, consumo em Watts, Throughput (Tokens/s) e fila ativa.
   - **Compute Workers:** Gestão de nós conectados, inspeção de dispositivos aceleradores e registro de novos workers.
   - **Tasks & Inference:** Assistente de submissão de cargas de trabalho (LLM, Data Parallel, Pipeline Stages, MoE) e inspeção de logs e tokens gerados.
   - **Scheduler & Chaos Lab:** Configuração de políticas de escalonamento e injeção controlada de falhas (Kill Worker, Latency Spike, Memory Pressure) para validação do failover automático.
   - **Benchmarks & Research Lab:** Execução de testes de carga interativos e medição de vazão e latência P50/P95/P99.
   - **Architecture Docs:** Navegador integrado com a documentação de pesquisa e arquitetura.

---

## 2. Documentação Científica e de Arquitetura (`docs/`)

Todos os entregáveis obrigatórios de pesquisa e documentação foram formalizados na pasta `docs/`:

1. [`docs/STATE_OF_THE_ART.md`](docs/STATE_OF_THE_ART.md) — Análise comparativa detalhada de PyTorch DDP/FSDP, Ray, vLLM, DeepSpeed ZeRO, llama.cpp RPC, e fundamentação teórica sobre limites de latência e viabilidade de paralelismo em redes LAN/Wi-Fi.
2. [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — Especificação técnica dos 6 subsistemas do NEXUS (Control Plane, Data Plane, Worker Runtime, Intelligent Scheduler, Observabilidade e Segurança).
3. [`docs/DECISIONS.md`](docs/DECISIONS.md) — Registros de Decisão Arquitetural (ADR-001 até ADR-005) com alternativas rejeitadas e justificativas.
4. [`docs/ROADMAP.md`](docs/ROADMAP.md) — Roteiro evolutivo em 5 fases (desde a linha de base até sharding de modelos 70B+ e federated inference).
5. [`docs/THREAT_MODEL.md`](docs/THREAT_MODEL.md) — Modelo de ameaças sob o framework STRIDE, mitigação de MITM e garantia absoluta contra Execução Remota de Código (RCE).
6. [`docs/BENCHMARKS.md`](docs/BENCHMARKS.md) — Metodologia, resultados experimentais e modelagem da relação entre custo de comunicação e intensidade computacional.
7. [`docs/EXPERIMENT_LOG.md`](docs/EXPERIMENT_LOG.md) — Registro cronológico de hipóteses e validações experimentais (EXP-001, EXP-002, EXP-003).
8. [`docs/HARDWARE_COMPATIBILITY.md`](docs/HARDWARE_COMPATIBILITY.md) — Matriz de 6 níveis de compatibilidade de hardware (Tiers 1 ao 6).

---

## 3. Testes Automatizados e Benchmarks

### Executando os Testes Automatizados (5/5 Passing)
```bash
PYTHONPATH=.venv/lib/python3.12/site-packages python3 tests/test_coordinator.py
```
*Resultado:*
```
Ran 5 tests in 0.038s - OK
```

### Executando os Benchmarks de Vazão e Latência
```bash
PYTHONPATH=.venv/lib/python3.12/site-packages python3 benchmarks/benchmark_throughput.py
```
*Resultados Obtidos:*
- **Vazão Sustentada (Throughput):** 247.8 tarefas/segundo
- **Latência de Submissão P50:** 1.25 ms
- **Latência P95:** 1.55 ms
- **Latência P99:** 1.89 ms
- **Speedup Paralelo (4 workers):** 3.82x vs nó único CPU

### Exemplos Práticos de Paralelismo
```bash
# Exemplo 1: Data Parallelism (Batch Sharding)
PYTHONPATH=.venv/lib/python3.12/site-packages python3 examples/demo_data_parallel.py

# Exemplo 2: Pipeline Parallelism (Passagem de Ativações entre Estágios)
PYTHONPATH=.venv/lib/python3.12/site-packages python3 examples/demo_pipeline_parallel.py

# Exemplo 3: Mixture of Experts (Roteamento Dinâmico por Domínio)
PYTHONPATH=.venv/lib/python3.12/site-packages python3 examples/demo_moe_routing.py
```

---

## 4. Como Executar a Plataforma Web

1. **Verificação de Integridade e Linting:**
   ```bash
   npm run lint
   ```
2. O aplicativo web React/TypeScript é servido na porta padrão via Vite e provê visualização interativa do cluster, telemetria de nós e laboratório de benchmarks.
