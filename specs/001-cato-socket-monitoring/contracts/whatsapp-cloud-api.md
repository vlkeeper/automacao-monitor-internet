# Contract: Meta WhatsApp Cloud API

**Endpoint**: `POST https://graph.facebook.com/v17.0/{{WA_PHONE_ID}}/messages`  
**Timeout Mandatório**: `10 segundos`

## 1. Headers de Requisição

```http
Authorization: Bearer {{WA_ACCESS_TOKEN}}
Content-Type: application/json
```

## 2. Formato 1: Mensagem de Texto Padrão (Ambiente Direto/Desenvolvimento)

```json
{
  "messaging_product": "whatsapp",
  "recipient_type": "individual",
  "to": "{{WA_RECIPIENT_PHONE}}",
  "type": "text",
  "text": {
    "preview_url": false,
    "body": "🚨 *ALERTA CATO NETWORKS*\n\n*Tipo:* SITE OFFLINE\n*Localidade:* Filial Campinas\n*Link:* Todos os links\n*Início:* 22/09/2026 10:45\n*Duração:* >= 3 minutos"
  }
}
```

## 3. Formato 2: Template Aprovado (Ambiente de Produção Meta)

Para contas que exigem templates pré-aprovados fora da janela de 24h:

```json
{
  "messaging_product": "whatsapp",
  "recipient_type": "individual",
  "to": "{{WA_RECIPIENT_PHONE}}",
  "type": "template",
  "template": {
    "name": "{{WA_TEMPLATE_NAME}}",
    "language": {
      "code": "pt_BR"
    },
    "components": [
      {
        "type": "body",
        "parameters": [
          { "type": "text", "text": "Filial Campinas" },
          { "type": "text", "text": "SITE OFFLINE" },
          { "type": "text", "text": "10:45" }
        ]
      }
    ]
  }
}
```

## 4. Regras de Resiliência
- Erros de autenticação (token expirado), rate-limit (429) ou timeout de rede são capturados em bloco try/except isolado.
- Uma falha no WhatsApp **NÃO** deve impedir o envio para o Teams nem abortar o loop principal de monitoramento.
- Tokens e credenciais nunca são impressos nos logs.
