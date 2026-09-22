# Contract: Microsoft Teams Incoming Webhook

**Endpoint**: `POST {{TEAMS_WEBHOOK_URL}}`  
**Timeout Mandatório**: `10 segundos`

## 1. Headers de Requisição

```http
Content-Type: application/json
```

## 2. Tipos de Mensagens

### 2.1 Alerta de Queda (LINK OFFLINE ou SITE OFFLINE)

```json
{
  "@type": "MessageCard",
  "@context": "http://schema.org/extensions",
  "themeColor": "D70000",
  "summary": "🚨 ALERTA: Queda de Conectividade",
  "sections": [
    {
      "activityTitle": "🚨 ALERTA: SITE OFFLINE",
      "activitySubtitle": "Filial Campinas",
      "facts": [
        { "name": "Status:", "value": "OFFLINE (Total)" },
        { "name": "Link:", "value": "Todos os links inativos" },
        { "name": "Início da Queda:", "value": "22/09/2026 10:45" },
        { "name": "Duração:", "value": ">= 3 minutos" }
      ],
      "markdown": true
    }
  ]
}
```

### 2.2 Notificação de Retorno (Normalização)

```json
{
  "@type": "MessageCard",
  "@context": "http://schema.org/extensions",
  "themeColor": "00B050",
  "summary": "✅ RETORNO: Link Restabelecido",
  "sections": [
    {
      "activityTitle": "✅ RETORNO: Conectividade Normalizada",
      "activitySubtitle": "Filial Campinas",
      "facts": [
        { "name": "Status:", "value": "ONLINE" },
        { "name": "Link:", "value": "WAN-02-Vivo" },
        { "name": "Horário do Retorno:", "value": "22/09/2026 11:15" }
      ],
      "markdown": true
    }
  ]
}
```

### 2.3 Boletim Diário (08:00)

```json
{
  "@type": "MessageCard",
  "@context": "http://schema.org/extensions",
  "themeColor": "0078D7",
  "summary": "📋 Resumo Diário de Links Inativos",
  "sections": [
    {
      "activityTitle": "📋 Boletim Matinal - Links Inativos (08:00)",
      "text": "Foram identificados os seguintes links com inatividade contínua:\n\n* **Filial Campinas (WAN-02-Vivo)**: Inativo há 1 dia e 4 horas (Desde 21/09 04:00)\n* **Filial Salvador (WAN-01-Claro)**: Inativo há 0 dias e 9 horas (Desde 21/09 23:00)",
      "markdown": true
    }
  ]
}
```

## 3. Formato Alternativo de Fallback (Simple Text Payload)

Para compatibilidade universal com webhooks simplificados do Teams:

```json
{
  "text": "🚨 **SITE OFFLINE**: A filial **Filial Campinas** está sem conectividade desde às **10:45**."
}
```
