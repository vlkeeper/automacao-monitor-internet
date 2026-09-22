import os
from typing import Optional, Dict, Any
import requests
from src.config import validate_config, mask_secret, Config

CATO_GRAPHQL_URL = "https://api.catonetworks.com/api/v1/graphql2"
CATO_TIMEOUT_SECONDS = 15

def get_network_status(config: Optional[Config] = None) -> Dict[str, Any]:
    """
    Consulta a topologia e o status de conectividade dos sites e links na Cato Networks.
    Princípio II da Constituição (Operações de Rede Defensivas):
    - Timeout estrito de 15 segundos.
    - Captura local e supressão de exceções de rede (Timeout, ConnectionError, HTTPError).
    - Logs sanitizados sem expor chaves de API (Princípio III).
    - Retorna dict vazio em caso de falha, mantendo o daemon em execução contínua.
    """
    if config is None:
        try:
            config = validate_config()
        except SystemExit:
            return {}

    headers = {
        "x-api-key": config.CATO_API_KEY,
        "Content-Type": "application/json"
    }

    query = """
    query GetSiteTopology($accountId: ID!) {
        site(accountId: $accountId) {
            items {
                id
                name
                connectionState
                tunnels {
                    id
                    name
                    status
                }
            }
        }
    }
    """

    payload = {
        "query": query,
        "variables": {
            "accountId": str(config.CATO_ACCOUNT_ID)
        }
    }

    try:
        response = requests.post(
            CATO_GRAPHQL_URL,
            json=payload,
            headers=headers,
            timeout=CATO_TIMEOUT_SECONDS
        )
        response.raise_for_status()
        data = response.json()

        if "errors" in data:
            print(f"[AVISO Cato API] Resposta retornou erros GraphQL. O loop continuará com segurança.")
            return {}

        return data
    except requests.exceptions.Timeout:
        print(f"[AVISO DEFENSIVO Cato API] Timeout de {CATO_TIMEOUT_SECONDS}s excedido ao consultar Cato Networks. Próximo ciclo tentará novamente.")
        return {}
    except requests.exceptions.RequestException as e:
        # Sanitiza a mensagem de erro para não expor headers ou URLs sensíveis
        print(f"[AVISO DEFENSIVO Cato API] Falha na comunicação HTTP: {type(e).__name__}. Ciclo preservado.")
        return {}
    except Exception as e:
        print(f"[AVISO DEFENSIVO Cato API] Exceção inesperada capturada defensivamente: {type(e).__name__}")
        return {}