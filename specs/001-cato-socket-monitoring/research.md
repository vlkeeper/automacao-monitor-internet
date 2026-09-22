# Research & Architecture Decisions: Monitoramento Cato Networks

**Feature**: [spec.md](spec.md) | **Branch**: `001-cato-socket-monitoring` | **Date**: 2026-09-22

Este documento consolida as decisões técnicas e padrões arquiteturais adotados para a implementação do monitoramento de sockets e links da Cato Networks, em conformidade estrita com a [Constituição do Projeto](../../.specify/memory/constitution.md).

---

## 1. Configuração e Fail-Fast (`src/config.py`)

### Decisão
Utilizar uma classe estruturada `Config` (dataclass) alimentada por `python-dotenv` e variáveis de ambiente, com método explícito `validate_config()` invocado no início do `main()`.

### Racional
- **Aderência ao Princípio IV (Configuração Fail-Fast)**: Se qualquer variável mandatória (`CATO_API_KEY`, `CATO_ACCOUNT_ID`, `TEAMS_WEBHOOK_URL`, `WA_PHONE_ID`, `WA_ACCESS_TOKEN`, `WA_RECIPIENT_PHONE`) estiver ausente ou vazia, a aplicação exibe mensagem de erro claro (sem vazar credenciais) e encerra imediatamente com `sys.exit(1)`.
- **Testabilidade**: Evita efeitos colaterais de encerramento imediato durante a importação de módulos em suítes de teste unitário (`pytest`), permitindo injetar configurações simuladas em tempo de teste.

### Variáveis Obrigatórias vs Opcionais
- **Obrigatórias**:
  - `CATO_API_KEY`: Token de autenticação da API Cato Networks.
  - `CATO_ACCOUNT_ID`: Identificador da conta na Cato Networks.
  - `TEAMS_WEBHOOK_URL`: URL do webhook corporativo do Microsoft Teams.
  - `WA_PHONE_ID`: Identificador do número de envio na Meta Cloud API.
  - `WA_ACCESS_TOKEN`: Bearer token de autenticação na Meta Cloud API.
  - `WA_RECIPIENT_PHONE`: Número de telefone do destinatário/plantão WhatsApp (formato internacional E.164, ex.: `5511999999999`).
- **Opcionais (com defaults seguros)**:
  - `STATE_FILE_PATH`: Caminho do arquivo JSON de estado (default: `data/estado_links.json` ou `estado_links.json`).
  - `POLLING_INTERVAL_SECONDS`: Intervalo de checagem em segundos (default: `60`).
  - `FLAP_TOLERANCE_MINUTES`: Minutos ininterruptos de inatividade para alerta (default: `3`).
  - `DAILY_DIGEST_TIME`: Horário do boletim matinal (default: `"08:00"`).
  - `TIMEZONE`: Fuso horário do sistema/agendador (default: `"America/Sao_Paulo"`).
  - `WA_TEMPLATE_NAME`: Nome do template aprovado na Meta Cloud API (se aplicável, ou envio de payload de mensagem padrão).

### Alternativas Consideradas
- *Acesso direto via `os.getenv` no corpo dos módulos*: Rejeitado por espalhar validações, dificultar testes e violar o princípio de validação centralizada na inicialização.

---

## 2. Resiliência e Atomicidade de Estado (`src/state.py`)

### Decisão
Implementar persistência de estado em arquivo JSON local utilizando padrão de escrita atômica com arquivo temporário (`.tmp`) e substituição via `os.replace`.

### Racional
- **Aderência ao Princípio I (Resiliência de Estado - NON-NEGOTIABLE)**: Em caso de terminação abrupta (SIGKILL do contêiner, crash de host ou falta de energia), a operação `os.replace` é garantida como atômica no nível do sistema de arquivos POSIX/NTFS, prevenindo JSON truncado ou corrompido.
- **Ordem de Operações Inegociável**: O estado DEVE ser persistido em disco ANTES do despacho de qualquer alerta externo. Isso impede que o sistema despache uma notificação para Teams/WhatsApp e, ao sofrer crash imediato, esqueça que já enviou o alerta e passe a reenviar alertas em loop infinito ao reiniciar.

### Estrutura do Estado
O arquivo `estado_links.json` armazena a estrutura hierárquica e cronológica dos sites e links:
```json
{
  "last_check": "2026-09-22T11:00:00-03:00",
  "sites": {
    "Filial SP": {
      "links": {
        "WAN-01": {
          "status": "OFFLINE",
          "offline_since": "2026-09-22T10:57:00-03:00",
          "alerted": true,
          "last_alert_type": "LINK OFFLINE",
          "last_alert_timestamp": "2026-09-22T11:00:00-03:00"
        }
      }
    }
  }
}
```

### Alternativas Consideradas
- *Banco SQLite*: Avaliado, mas considerado sobrecarga desnecessária para o volume de dados (dezenas a poucas centenas de links) e exigiria migrations e concorrência que não existem no daemon mono-processo.
- *Persistência em memória RAM*: Rejeitada terminantemente pela Constituição.

---

## 3. Algoritmo de Avaliação de Impacto e Tolerância (`src/monitor.py`)

### Decisão
Processamento em duas etapas (two-pass processing) por ciclo de 60 segundos:
1. **Etapa 1 - Agregação de Status Atual**: Mapeia todos os links retornados pela Cato para cada site e determina o total de links configurados e a quantidade de links atualmente offline.
2. **Etapa 2 - Avaliação Temporal e Notificação**:
   - Se um link ficou offline pela primeira vez: anota `offline_since = now`, `alerted = False`.
   - Se o link continua offline e ainda não foi alertado (`not alerted`):
     - Calcula `delta_tempo = now - offline_since`.
     - Se `delta_tempo >= 3 minutos`:
       - Determina se o site inteiro está offline (`total_links == offline_links_do_site`) ou se é queda parcial.
       - Marca `alerted = True`, define `last_alert_type = "SITE OFFLINE"` ou `"LINK OFFLINE"`.
       - **PERSISTE O ESTADO EM DISCO** (`save_state`).
       - Despacha notificações para Teams e WhatsApp.
   - Se um link que estava em alerta (`alerted == True`) restabeleceu conectividade:
     - Marca no estado o restabelecimento.
     - **PERSISTE O ESTADO EM DISCO**.
     - Despacha notificação de `RETORNO` para Teams e WhatsApp.
     - Limpa o registro de inatividade do link.
   - Se o link restabeleceu conectividade ANTES de completar 3 minutos (`alerted == False`):
     - Reseta silenciosamente `offline_since = None` e `status = "ONLINE"`.
     - Nenhum alerta de queda nem de retorno é enviado (filtro anti-flap concluído).

### Racional
- Garante o cumprimento de US01, US02, US03, US04 e Princípio V.
- Elimina a falha sutil do código anterior onde a detecção de "SITE OFFLINE" avaliava `total_links == offline_links` durante a iteração individual antes de processar todos os links do site.

---

## 4. Integração GraphQL Cato Networks (`src/cato_api.py`)

### Decisão
Utilizar endpoint padrão Cato GraphQL (`https://api.catonetworks.com/api/v1/graphql2`) com cabeçalho `x-api-key`, payload estruturado e timeout de 15 segundos.

### Racional
- **Aderência ao Princípio II (Operações de Rede Defensivas)**: Requisição com timeout estrito de 15 segundos. Exceções de rede (`requests.exceptions.RequestException`, `Timeout`, `ConnectionError`) são capturadas localmente, registradas em log com mascaramento e retornam `None` ou estrutura vazia, permitindo que o daemon continue o loop sem falha catastrófica.

### Sanitização
- Logs nunca exibem a chave `x-api-key` ou tokens.
- O identificador de conta e URLs são mascarados caso ocorra log de depuração.

---

## 5. Despacho Multi-Canal e Resumo Diário (`src/notifier.py`)

### Decisão
Isolar as funções de envio em adaptadores dedicados com timeout de 10 segundos:
- `send_teams_alert(title, text, color)`: Envia payload padronizado via Webhook HTTP POST (compatível com Office 365 Connector / Adaptive Cards / Simple MessageCard).
- `send_whatsapp_alert(site_name, link_name, status_msg, timestamp)`: Envia requisição POST para a Meta Cloud API (`v17.0` ou mais recente) para o número configurado.
- `broadcast_incident(site_name, link_name, alert_type, timestamp)`: Orquestra o envio simultâneo para Teams e WhatsApp com proteção try/except independente em cada canal.
- `send_daily_digest(inactive_items)`: Disparado exclusivamente às 08:00 para o Microsoft Teams com a listagem formatada dos links inativos há mais de 3 minutos, com o cálculo exato de dias e horas acumuladas. Se não houver quedas, envia mensagem verde informando normalidade de 100% dos links.

---

## 6. Agendador e Ciclo Daemon (`main.py`)

### Decisão
Daemon contínuo utilizando `schedule` para orquestrar:
- `schedule.every(1).minutes.do(job_check_status)`
- `schedule.every().day.at("08:00").do(job_daily_reminder)`
- Loop `while True` com `schedule.run_pending()` e tratamento global defensivo de exceções para proteger a continuidade do contêiner.

---

## 7. Conteinerização e Volume de Estado (`Dockerfile`)

### Decisão
Imagem base `python:3.11-slim`:
- Usuário não-root (`appuser`) para segurança de contêiner.
- Diretório de trabalho `/app`.
- Criação de pasta `/app/data` para montagem de volume persistente do Docker (`-v ./data:/app/data`).
- `CMD ["python", "main.py"]` com `PYTHONUNBUFFERED=1` para flush imediato de logs.

---

## 8. Estratégia de Testes (`tests/`)

### Decisão
Utilizar `pytest` e `pytest-mock` para validar os portões inegociáveis da Constituição:
1. `tests/test_config.py`: Validação fail-fast na ausência de variáveis.
2. `tests/test_state.py`: Validação de atomicidade de escrita e recuperação após falha simulada.
3. `tests/test_monitor.py`: Validação da tolerância de 3 minutos (flapping), diferenciação `LINK OFFLINE` vs `SITE OFFLINE`, restabelecimento e envio de boletim diário.
4. `tests/test_cato_api.py`: Validação defensiva de timeouts e captura de exceções HTTP sem quebra do fluxo.
