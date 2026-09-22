# Contract: Cato Networks GraphQL API

**Endpoint**: `POST https://api.catonetworks.com/api/v1/graphql2`  
**Timeout Mandatório**: `15 segundos` (Princípio II da Constituição)

## 1. Headers de Requisição

```http
Content-Type: application/json
x-api-key: {{CATO_API_KEY}}
```

## 2. Payload da Query GraphQL

A consulta recupera a lista de sites e os túneis/sockets associados à conta informada:

```json
{
  "query": "query GetSiteTopology($accountId: ID!) { site(accountId: $accountId) { items { id name connectionState tunnels { id name status } } } }",
  "variables": {
    "accountId": "{{CATO_ACCOUNT_ID}}"
  }
}
```

## 3. Contrato de Resposta Sucesso (200 OK)

```json
{
  "data": {
    "site": {
      "items": [
        {
          "id": "1001",
          "name": "Filial Campinas",
          "connectionState": "Connected",
          "tunnels": [
            {
              "id": "tun-01",
              "name": "WAN-01-Claro",
              "status": "CONNECTED"
            },
            {
              "id": "tun-02",
              "name": "WAN-02-Vivo",
              "status": "DISCONNECTED"
            }
          ]
        }
      ]
    }
  }
}
```

## 4. Regras de Resiliência
- Se status HTTP != 200, resposta contiver campo `"errors"` ou ocorrer timeout/erro de conexão:
  - O cliente captura a exceção localmente.
  - Loga aviso de erro sanitizado sem expor a chave `x-api-key`.
  - Retorna `{}` ou `None` para que o ciclo atual seja abortado com segurança sem alterar os estados prévios.
