# Implementation Plan: Monitoramento de Sockets Cato Networks

**Branch**: `001-cato-socket-monitoring` | **Date**: 2026-09-22 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from [specs/001-cato-socket-monitoring/spec.md](spec.md) e proposta de arquitetura modular em Python.

---

## Summary

Implementação de um serviço daemon resiliente em Python para monitorar continuamente (ciclos de 60 segundos) a conectividade dos sockets e links LAN/WAN da Cato Networks. O sistema filtra oscilações rápidas (flaps) aplicando uma janela de tolerância estrita de 3 minutos contínuos antes de alertar a equipe de TI via Microsoft Teams e WhatsApp (Meta Cloud API). A solução diferencia degradação parcial (`LINK OFFLINE`) de queda total (`SITE OFFLINE`), envia confirmações instantâneas de retorno (`RETORNO`) e despacha um resumo matinal diário às 08:00 exclusivo no Teams com o tempo acumulado de inatividade. O estado é persistido de forma atômica em disco para garantir tolerância a falhas e reinicializações de contêiner.

---

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: `requests==2.31.0`, `schedule==1.2.1`, `python-dotenv==1.0.0`  
**Storage**: Arquivo JSON persistente (`estado_links.json`) gravado de forma atômica via arquivo temporário (`.tmp`) e `os.replace`  
**Testing**: `pytest`, `pytest-mock`  
**Target Platform**: Contêiner Docker (`python:3.11-slim`) em Linux / Execução local Windows  
**Project Type**: Background Daemon / CLI Service  
**Performance Goals**: Ciclo de polling de 60 segundos com execução total em < 15 segundos; alertas despachados em até 10 segundos após detecção  
**Constraints**: Uso de memória < 100MB; timeouts obrigatórios de 10s (notificações) e 15s (Cato API); tolerância a falhas de rede sem interrupção do loop; isolamento total de segredos  
**Scale/Scope**: Monitoramento de dezenas a centenas de links e filiais (sites) da organização  

---

## Constitution Check

*GATE: Avaliado inicialmente e re-checado após o design técnico das Fases 0 e 1.*

| Princípio Constitucional | Requisito do Projeto | Status de Conformidade | Evidência no Design |
|---------------------------|----------------------|------------------------|---------------------|
| **I. Resiliência de Estado (NON-NEGOTIABLE)** | Gravação atômica em disco antes de ações externas; sobrevivência a reinicializações | **PASS** | `src/state.py` grava via `.tmp` e `os.replace`; `src/monitor.py` executa `save_state()` obrigatoriamente antes de invocar notificação externa. |
| **II. Operações de Rede Defensivas** | Timeouts rígidos (10-15s), captura local de exceções, supressão segura de erros sem abortar o daemon | **PASS** | `cato_api.py` (timeout 15s), `notifier.py` (timeout 10s); blocos `try/except` isolados capturam `RequestException` e impedem quebra do loop principal. |
| **III. Isolamento Estrito de Segredos** | Credenciais exclusivamente em variáveis de ambiente; mascaramento em logs | **PASS** | `src/config.py` carrega `.env`; funções de log suprimem chaves de API, webhooks e tokens de autenticação. |
| **IV. Configuração Fail-Fast** | Validação mandatória no startup; saída imediata com código não-zero se ausente/inválido | **PASS** | `Config.validate_config()` valida todas as variáveis obrigatórias e executa `sys.exit(1)` antes do início do daemon. |
| **V. Carga Cognitiva e Fadiga de Alerta** | Filtro anti-flap (>= 3 min), distinção clara de impacto (`LINK OFFLINE` vs `SITE OFFLINE`), aviso de retorno | **PASS** | Lógica em duas etapas no `src/monitor.py`: absorve oscilações < 3 min, diferencia link individual de queda total do site e emite retorno imediato. |

---

## Project Structure

### Documentation (this feature)

```text
specs/001-cato-socket-monitoring/
├── plan.md              # Este arquivo (Plano de Implementação)
├── spec.md              # Especificação de Requisitos e Critérios de Sucesso
├── research.md          # Fase 0: Decisões de Arquitetura e Padrões Técnicos
├── data-model.md        # Fase 1: Modelos de Dados e Máquina de Estados
├── quickstart.md        # Fase 1: Guia de Validação e Execução
├── contracts/           # Fase 1: Contratos de Integração
│   ├── cato-graphql-api.md   # Contrato Cato Networks GraphQL
│   ├── teams-webhook.md      # Contrato Microsoft Teams Incoming Webhook
│   ├── whatsapp-cloud-api.md # Contrato Meta WhatsApp Cloud API
│   └── state-storage.json    # Esquema JSON de Persistência em Disco
└── checklists/
    └── requirements.md  # Validação de Qualidade da Especificação
```

### Source Code (repository root)

```text
src/
├── __init__.py
├── config.py            # Validação Fail-Fast e leitura de variáveis de ambiente
├── state.py             # Persistência atômica (.tmp + os.replace) e carga do JSON
├── cato_api.py          # Cliente GraphQL Cato Networks com timeout defensivo de 15s
├── notifier.py          # Adaptadores Teams Webhook e WhatsApp Meta Cloud API com timeout de 10s
└── monitor.py           # Orquestração do ciclo de 1 min, cálculo de tolerância e boletim diário

tests/
├── __init__.py
├── conftest.py          # Fixtures de mock para ambiente, APIs e estado
├── test_config.py       # Teste de fail-fast para variáveis ausentes/inválidas
├── test_state.py        # Teste de escrita atômica e recuperação após reinício
├── test_cato_api.py     # Teste defensivo contra falhas de rede e timeouts
├── test_notifier.py     # Teste de despacho para Teams e WhatsApp
└── test_monitor.py      # Teste do filtro anti-flap (3 min), SITE/LINK OFFLINE e retorno

main.py                  # Entrypoint: registro dos agendamentos no schedule e loop infinito defensivo
requirements.txt         # Dependências do projeto (requests, schedule, python-dotenv, pytest)
Dockerfile               # Conteinerização em python:3.11-slim com volume persistente /app/data
.env.example             # Modelo documentado de variáveis de ambiente sem segredos
```

**Structure Decision**: Padrão modular baseado em responsabilidade única (SRP), desacoplando totalmente a coleta de telemetria (`cato_api`), a persistência atômica (`state`), as notificações (`notifier`), a orquestração do domínio (`monitor`) e o bootstrap (`config` e `main`).

---

## Complexity Tracking

> Nenhuma violação aos princípios constitucionais. O projeto atende integralmente às regras de resiliência, fail-fast, segurança e operações defensivas sem acréscimo de complexidade desnecessária.

| Princípio / Diretriz | Solução Adotada | Justificativa de Simplicidade |
|----------------------|-----------------|--------------------------------|
| Persistência de Estado | Arquivo JSON local com escrita atômica (`os.replace`) | Dispensa infraestrutura de banco de dados externa para um daemon local uniprocesso |
| Agendamento | Biblioteca `schedule` em loop do daemon | Elimina necessidade de dependências complexas como Celery/Redis ou cron externo |
| Integração Multi-Canal | Funções desacopladas com fallbacks isolados | Garante que falha em um canal (ex: WhatsApp) não impeça a notificação no Teams |
