import pytest
import requests
from src.notifier import (
    send_teams_alert,
    send_whatsapp_alert,
    broadcast_alert,
    send_teams_daily_digest
)

def test_send_teams_alert_success(mocker, mock_env):
    """Verifica envio bem-sucedido de alerta para Microsoft Teams com timeout de 10s."""
    mock_post = mocker.patch("requests.post")
    mock_post.return_value.status_code = 200
    
    success = send_teams_alert("🚨 SITE OFFLINE", "Filial Campinas sem conectividade")
    assert success is True
    mock_post.assert_called_once()
    _, kwargs = mock_post.call_args
    assert kwargs["timeout"] == 10
    assert "json" in kwargs

def test_send_teams_alert_defensive_on_error(mocker, mock_env):
    """Princípio II: Falha no Teams não deve propagar exceção."""
    mocker.patch("requests.post", side_effect=requests.exceptions.ConnectTimeout("Timeout Teams"))
    success = send_teams_alert("🚨 ALERTA", "Mensagem de teste")
    assert success is False

def test_send_whatsapp_alert_success(mocker, mock_env):
    """Verifica envio bem-sucedido de alerta para Meta Cloud API com timeout de 10s."""
    mock_post = mocker.patch("requests.post")
    mock_post.return_value.status_code = 200
    
    success = send_whatsapp_alert("Filial SP", "WAN-01-Claro", "LINK OFFLINE", "10:30")
    assert success is True
    mock_post.assert_called_once()
    url, kwargs = mock_post.call_args[0][0], mock_post.call_args[1]
    assert "1020304050" in url
    assert kwargs["timeout"] == 10
    assert "Authorization" in kwargs["headers"]
    assert "Bearer mock_meta_access_token_xyz" == kwargs["headers"]["Authorization"]

def test_send_whatsapp_alert_defensive_on_error(mocker, mock_env):
    """Princípio II: Falha no WhatsApp não deve propagar exceção."""
    mocker.patch("requests.post", side_effect=requests.exceptions.HTTPError("400 Bad Request"))
    success = send_whatsapp_alert("Filial SP", "WAN-01-Claro", "LINK OFFLINE", "10:30")
    assert success is False

def test_broadcast_alert_channels_independent(mocker, mock_env):
    """Verifica que erro em um canal não bloqueia o outro durante broadcast."""
    # Teams falha, mas WhatsApp funciona
    mock_teams = mocker.patch("src.notifier.send_teams_alert", return_value=False)
    mock_whatsapp = mocker.patch("src.notifier.send_whatsapp_alert", return_value=True)
    
    broadcast_alert("Filial SP", "WAN-01-Claro", "LINK OFFLINE", "10:30")
    
    mock_teams.assert_called_once()
    mock_whatsapp.assert_called_once()

def test_send_teams_daily_digest(mocker, mock_env):
    """Verifica que o resumo diário é enviado com formatação própria para o Teams."""
    mock_post = mocker.patch("requests.post")
    mock_post.return_value.status_code = 200
    
    success = send_teams_daily_digest("📋 Resumo de Links:\n- Filial SP: 2 horas fora")
    assert success is True
    mock_post.assert_called_once()
