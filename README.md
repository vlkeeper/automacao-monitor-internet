# Monitoramento de Sockets Cato Networks

Automação resiliente em Python para monitoramento proativo de sockets e links LAN/WAN da Cato Networks. O sistema filtra oscilações rápidas (flaps), alerta a equipe de TI via Microsoft Teams e WhatsApp de forma inteligente, diferenciando problemas parciais de quedas totais, e despacha relatórios diários de backlog de manutenção.

---

## 🚀 Funcionalidades Principais

- **Varredura Contínua (Polling a cada 60s):** Consulta a telemetria da Cato Networks a cada 1 minuto de forma defensiva e não-bloqueante.
- **Filtro Anti-Flap (Tolerância de 3 Minutos):** Quedas inferiores a 3 minutos ininterruptos são absorvidas silenciosamente sem gerar falsos alertas.
- **Diferenciação Inteligente de Impacto:**
  - `LINK OFFLINE`: Identifica degradação parcial em sites com redundância de links.
  - `SITE OFFLINE`: Identifica a perda total de conectividade da localidade (todos os links inativos).
- **Notificação Imediata de Retorno (`RETORNO`):** Alerta instantâneo no Teams e WhatsApp quando um link ou site normaliza.
- **Boletim Diário Matinal (08:00):** Resumo consolidado enviado exclusivamente ao Microsoft Teams com a listagem dos links inativos e o tempo acumulado em dias e horas.
- **Resiliência e Persistência Atômica:** O estado é gravado de forma atômica no arquivo `estado_links.json` antes de qualquer ação externa, garantindo tolerância a reinicializações e falhas do contêiner.

---

## 🛠️ Arquitetura e Estrutura do Projeto

```text
├── src/
│   ├── config.py        # Validação Fail-Fast e leitura de variáveis de ambiente
│   ├── state.py         # Persistência atômica (.tmp + os.replace)
│   ├── cato_api.py      # Cliente Cato Networks GraphQL com timeout defensivo de 15s
│   ├── notifier.py      # Despacho Teams Webhook e Meta WhatsApp com timeout de 10s
│   └── monitor.py       # Orquestração do ciclo, tolerância 3 min e boletim 08:00
├── tests/               # Suíte completa de testes automatizados (pytest)
├── main.py              # Entrypoint do daemon em loop infinito
├── requirements.txt     # Dependências (requests, schedule, python-dotenv, pytest)
├── Dockerfile           # Imagem enxuta python:3.11-slim com volume persistente /app/data
├── .env.example         # Template documentado de variáveis de ambiente
└── .dockerignore        # Isolamento do contexto de build do Docker
```

---

## ⚙️ Configuração das Variáveis de Ambiente

Copie o arquivo `.env.example` para `.env` e configure as credenciais:

```bash
cp .env.example .env
```

| Variável | Obrigatória | Padrão | Descrição |
|----------|-------------|--------|-----------|
| `CATO_API_KEY` | **Sim** | - | Chave de API da Cato Networks |
| `CATO_ACCOUNT_ID` | **Sim** | - | Identificador numérico da conta Cato |
| `TEAMS_WEBHOOK_URL` | **Sim** | - | URL do Incoming Webhook do Microsoft Teams |
| `WA_PHONE_ID` | **Sim** | - | Phone Number ID na Meta Cloud API |
| `WA_ACCESS_TOKEN` | **Sim** | - | Token de Acesso do Sistema Meta |
| `WA_RECIPIENT_PHONE` | **Sim** | - | Telefone de destino do WhatsApp (`5511999999999`) |
| `STATE_FILE_PATH` | Não | `estado_links.json` | Caminho do arquivo JSON de estado persistente |
| `POLLING_INTERVAL_SECONDS` | Não | `60` | Intervalo entre varreduras em segundos |
| `FLAP_TOLERANCE_MINUTES` | Não | `3` | Janela de tolerância contínua para alerta |
| `DAILY_DIGEST_TIME` | Não | `08:00` | Horário de envio do boletim diário |
| `TIMEZONE` | Não | `America/Sao_Paulo` | Fuso horário local |

> **Segurança (Princípio III):** Nenhuma credencial deve ser commitada no Git. O arquivo `.env` está explicitamente ignorado no `.gitignore`.

---

## 🧪 Execução dos Testes Automatizados

Para executar todos os testes unitários e de integração:

```bash
pytest -v
```

---

## 💻 Execução Local

```bash
# 1. Ativar ambiente virtual
# No Windows PowerShell:
.\venv\Scripts\Activate.ps1
# No Linux:
source venv/bin/activate

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Iniciar o daemon
python main.py
```

---

## 🐳 Execução via Docker (Produção)

### Construção da imagem

```bash
docker build -t cato-monitor:latest .
```

### Execução com montagem de volume persistente

Para garantir que o estado sobreviva a reinicializações do contêiner (Princípio I da Constituição):

```bash
docker run -d \
  --name cato-monitor-app \
  --restart unless-stopped \
  --env-file .env \
  -v ${PWD}/data:/app/data \
  -e STATE_FILE_PATH=/app/data/estado_links.json \
  cato-monitor:latest
```

### Visualização dos logs

```bash
docker logs -f cato-monitor-app
```