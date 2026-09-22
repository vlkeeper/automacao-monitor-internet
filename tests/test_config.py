import os
import sys
import pytest
from src.config import Config, validate_config, mask_secret

def test_mask_secret():
    """Verifica que o segredo é ofuscado e preserva apenas caracteres finais."""
    secret = "minha-chave-secreta-1234"
    masked = mask_secret(secret)
    assert len(masked) == len(secret)
    assert masked.endswith("1234")
    assert masked.startswith("****")
    assert mask_secret("curta") == "****"
    assert mask_secret("") == "****"

def test_validate_config_success(mock_env):
    """Verifica que com todas as variáveis obrigatórias, o config é carregado com sucesso."""
    config = validate_config()
    assert config.CATO_API_KEY == "mock_cato_api_key_12345"
    assert config.CATO_ACCOUNT_ID == "99999"
    assert config.TEAMS_WEBHOOK_URL == "https://outlook.office.com/webhook/test"
    assert config.WA_PHONE_ID == "1020304050"
    assert config.WA_ACCESS_TOKEN == "mock_meta_access_token_xyz"
    assert config.WA_RECIPIENT_PHONE == "5511999999999"
    assert config.FLAP_TOLERANCE_MINUTES == 3
    assert config.POLLING_INTERVAL_SECONDS == 60

def test_validate_config_fail_fast_missing_key(monkeypatch):
    """Princípio IV: Ausência de variável mandatória deve acionar sys.exit(1)."""
    monkeypatch.delenv("CATO_API_KEY", raising=False)
    monkeypatch.delenv("CATO_ACCOUNT_ID", raising=False)
    with pytest.raises(SystemExit) as exc_info:
        validate_config()
    assert exc_info.value.code == 1
