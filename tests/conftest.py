import os
import pytest
from datetime import datetime, timezone

@pytest.fixture
def mock_env(monkeypatch, tmp_path):
    """Configura um ambiente completo e válido para testes."""
    state_file = str(tmp_path / "test_estado_links.json")
    monkeypatch.setenv("CATO_API_KEY", "mock_cato_api_key_12345")
    monkeypatch.setenv("CATO_ACCOUNT_ID", "99999")
    monkeypatch.setenv("TEAMS_WEBHOOK_URL", "https://outlook.office.com/webhook/test")
    monkeypatch.setenv("WA_PHONE_ID", "1020304050")
    monkeypatch.setenv("WA_ACCESS_TOKEN", "mock_meta_access_token_xyz")
    monkeypatch.setenv("WA_RECIPIENT_PHONE", "5511999999999")
    monkeypatch.setenv("STATE_FILE_PATH", state_file)
    monkeypatch.setenv("FLAP_TOLERANCE_MINUTES", "3")
    monkeypatch.setenv("POLLING_INTERVAL_SECONDS", "60")
    monkeypatch.setenv("DAILY_DIGEST_TIME", "08:00")
    monkeypatch.setenv("TIMEZONE", "America/Sao_Paulo")
    return {
        "state_file": state_file,
        "api_key": "mock_cato_api_key_12345",
        "account_id": "99999"
    }

@pytest.fixture
def sample_cato_data():
    """Mock da estrutura de dados retornada pela Cato Networks."""
    return {
        "data": {
            "site": {
                "items": [
                    {
                        "id": "101",
                        "name": "Filial SP",
                        "connectionState": "Connected",
                        "tunnels": [
                            {"id": "tun-01", "name": "WAN-01-Claro", "status": "CONNECTED"},
                            {"id": "tun-02", "name": "WAN-02-Vivo", "status": "CONNECTED"}
                        ]
                    },
                    {
                        "id": "102",
                        "name": "Filial RJ",
                        "connectionState": "Connected",
                        "tunnels": [
                            {"id": "tun-03", "name": "WAN-01-Oi", "status": "CONNECTED"}
                        ]
                    }
                ]
            }
        }
    }
