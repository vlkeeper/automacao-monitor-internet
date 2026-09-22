# Quickstart: Validação e Execução do Monitor Cato Networks

**Feature**: [spec.md](spec.md) | **Branch**: `001-cato-socket-monitoring` | **Date**: 2026-09-22

Este guia fornece o passo a passo para configuração do ambiente, execução local, execução via Docker e validação dos cenários fim a fim da automação.

---

## 1. Pré-requisitos

- **Python**: Versão 3.10 ou superior
- **Docker**: (Opcional para execução em contêiner)
- **Acessos / Credenciais**:
  - Cato Networks API Key e Account ID
  - Webhook URL do Microsoft Teams
  - Credenciais da Meta Cloud API (WhatsApp Phone Number ID, Access Token e número de destino)

---

## 2. Configuração do Ambiente Local

### 2.1 Criar ambiente virtual e instalar dependências

```bash
python -m venv venv
# No Windows PowerShell:
.\venv\Scripts\Activate.ps1
# No Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 2.2 Configurar variáveis de ambiente (`.env`)

Crie ou edite o arquivo `.env` na raiz do projeto com base nas chaves documentadas em [research.md](research.md):

```dotenv
# Credenciais Cato Networks
CATO_API_KEY=sua_chave_cato_aqui
CATO_ACCOUNT_ID=seu_account_id_aqui

# Canal Microsoft Teams
TEAMS_WEBHOOK_URL=https://outlook.office.com/webhook/seu_webhook_aqui

# Canal Meta WhatsApp Cloud API
WA_PHONE_ID=seu_phone_number_id_aqui
WA_ACCESS_TOKEN=seu_access_token_aqui
WA_RECIPIENT_PHONE=5511999999999
WA_TEMPLATE_NAME=alerta_queda_cato

# Configurações de Estado e Comportamento (Opcionais)
STATE_FILE_PATH=estado_links.json
POLLING_INTERVAL_SECONDS=60
FLAP_TOLERANCE_MINUTES=3
DAILY_DIGEST_TIME=08:00
TIMEZONE=America/Sao_Paulo
```

---

## 3. Execução dos Testes Automatizados

Execute a suíte de testes unitários que valida as garantias da Constituição:

```bash
pytest -v
```

Cenários cobertos pela suíte:
- `test_fail_fast_missing_env`: Garante que a aplicação aborta com código 1 caso falte credencial obrigatória.
- `test_atomic_state_persistence`: Garante escrita atômica via `.tmp` e `os.replace` e integridade em reinicializações.
- `test_flap_tolerance_filter`: Simula oscilação com menos de 3 minutos e valida que nenhum alerta é disparado.
- `test_link_vs_site_offline_detection`: Valida a distinção precisa entre `LINK OFFLINE` e `SITE OFFLINE`.
- `test_restoration_alert`: Valida despacho de alerta de retorno e limpeza de estado após normalização.
- `test_daily_digest_teams_only`: Valida o formato e envio exclusivo para o Teams às 08:00 com cálculo de dias/horas.
- `test_defensive_network_operations`: Simula timeout e erro 500 na Cato API e nos Notifiers, validando que o loop continua ativo.

---

## 4. Execução Manual / Daemon Local

Inicie o processo do daemon:

```bash
python main.py
```

Saída esperada no console:
```text
Iniciando Monitoramento Cato Networks...
[INFO] Configurações validadas com sucesso.
[INFO] Agendamento ativo: verificação a cada 60s | resumo diário às 08:00.
```

---

## 5. Execução em Contêiner Docker

### 5.1 Construir a imagem Docker

```bash
docker build -t cato-monitor:latest .
```

### 5.2 Executar com volume persistente para o estado

```bash
docker run -d \
  --name cato-monitor-app \
  --restart unless-stopped \
  --env-file .env \
  -v ${PWD}/data:/app/data \
  -e STATE_FILE_PATH=/app/data/estado_links.json \
  cato-monitor:latest
```

### 5.3 Verificar logs em tempo real

```bash
docker logs -f cato-monitor-app
```

---

## 6. Cenários de Validação Fim a Fim (Manual / Mock)

### Cenário A: Validação do Filtro Anti-Flap
1. Simule uma resposta da Cato onde o link `"WAN-01"` aparece `DISCONNECTED` às `10:00`.
2. O sistema registra `"status": "OFFLINE"`, `"alerted": false` no estado. Nenhum alerta em Teams/WhatsApp.
3. Às `10:02` (2 minutos decorridos), simule o link voltando para `CONNECTED`.
4. O sistema limpa o estado. Nenhum alerta de queda e nenhum alerta de retorno é disparado. **(Sucesso)**.

### Cenário B: Validação de Queda Real (>= 3 minutos)
1. Às `10:00`, link `"WAN-01"` cai.
2. Às `10:01` e `10:02`, o link continua inativo. Nenhum alerta emitido.
3. Às `10:03` (3 minutos ininterruptos completados), o sistema:
   - Salva atomicamente no disco `"alerted": true`.
   - Despacha o alerta de `"LINK OFFLINE"` para o canal do Teams e WhatsApp. **(Sucesso)**.

### Cenário C: Validação de Retorno
1. Com o link `"WAN-01"` em estado de alerta (`"alerted": true`), simule a volta para `CONNECTED` às `10:15`.
2. O sistema:
   - Salva o estado restaurado no disco.
   - Despacha imediatamente a mensagem de `"RETORNO"` para o Teams e WhatsApp. **(Sucesso)**.

### Cenário D: Validação de Reinicialização de Contêiner
1. Com um link inativo há 2 minutos, encerre o contêiner (`docker restart cato-monitor-app`).
2. Aguarde 1 minuto.
3. O sistema retoma o timestamp do arquivo persistido `/app/data/estado_links.json` e despacha o alerta de queda pontualmente ao completar 3 minutos, sem reiniciar a contagem. **(Sucesso)**.
