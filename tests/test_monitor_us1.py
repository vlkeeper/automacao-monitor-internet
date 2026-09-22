from datetime import datetime, timedelta, timezone
import pytest
from src.monitor import check_status
from src.state import load_state, save_state

def test_us1_initial_offline_no_alert(mocker, mock_env, sample_cato_data):
    """Minuto 0: Link cai. Anota no estado, salva atomicamente e permanece em silêncio."""
    # Modifica retorno para que um link apareça DISCONNECTED
    sample_cato_data["data"]["site"]["items"][0]["tunnels"][0]["status"] = "DISCONNECTED"
    mocker.patch("src.monitor.get_network_status", return_value=sample_cato_data)
    mock_broadcast = mocker.patch("src.monitor.broadcast_alert")
    
    now = datetime(2026, 9, 22, 10, 0, 0)
    mocker.patch("src.monitor.get_current_time", return_value=now)
    
    check_status()
    
    # Valida que nenhum alerta foi enviado
    mock_broadcast.assert_not_called()
    
    # Valida que o estado foi anotado e persistido
    state = load_state()
    link_info = state["sites"]["Filial SP"]["links"]["WAN-01-Claro"]
    assert link_info["status"] == "OFFLINE"
    assert link_info["alerted"] is False
    assert link_info["offline_since"] == now.isoformat()

def test_us1_flap_filtered_out_under_3_minutes(mocker, mock_env, sample_cato_data):
    """Flap: Cai às 10:00 e volta às 10:02 (< 3 min). Deve absorver sem nenhum alerta."""
    mock_broadcast = mocker.patch("src.monitor.broadcast_alert")
    state_file = mock_env["state_file"]
    
    # Estado inicial: caiu às 10:00
    caiu_as = datetime(2026, 9, 22, 10, 0, 0)
    save_state({
        "last_check": caiu_as.isoformat(),
        "sites": {
            "Filial SP": {
                "links": {
                    "WAN-01-Claro": {
                        "status": "OFFLINE",
                        "offline_since": caiu_as.isoformat(),
                        "alerted": False,
                        "last_alert_type": None,
                        "last_alert_timestamp": None
                    }
                }
            }
        }
    }, state_file)
    
    # Às 10:02 o link aparece CONNECTED de volta
    now = datetime(2026, 9, 22, 10, 2, 0)
    mocker.patch("src.monitor.get_current_time", return_value=now)
    mocker.patch("src.monitor.get_network_status", return_value=sample_cato_data)
    
    check_status()
    
    # Nenhum alerta disparado (nem queda, nem retorno)
    mock_broadcast.assert_not_called()
    
    # Estado voltou a ficar ONLINE
    state = load_state(state_file)
    link_info = state["sites"]["Filial SP"]["links"]["WAN-01-Claro"]
    assert link_info["status"] == "ONLINE"
    assert link_info["offline_since"] is None
    assert link_info["alerted"] is False

def test_us1_alert_triggered_at_3_minutes_continuous(mocker, mock_env, sample_cato_data):
    """Minuto 3 ininterrupto: Dispara alerta e salva estado antes do envio."""
    mock_broadcast = mocker.patch("src.monitor.broadcast_alert")
    state_file = mock_env["state_file"]
    
    caiu_as = datetime(2026, 9, 22, 10, 0, 0)
    save_state({
        "last_check": caiu_as.isoformat(),
        "sites": {
            "Filial SP": {
                "links": {
                    "WAN-01-Claro": {
                        "status": "OFFLINE",
                        "offline_since": caiu_as.isoformat(),
                        "alerted": False,
                        "last_alert_type": None,
                        "last_alert_timestamp": None
                    }
                }
            }
        }
    }, state_file)
    
    # Às 10:03 (3 minutos cravados), continua DISCONNECTED
    now = datetime(2026, 9, 22, 10, 3, 0)
    sample_cato_data["data"]["site"]["items"][0]["tunnels"][0]["status"] = "DISCONNECTED"
    mocker.patch("src.monitor.get_current_time", return_value=now)
    mocker.patch("src.monitor.get_network_status", return_value=sample_cato_data)
    
    check_status()
    
    # Alerta disparado
    mock_broadcast.assert_called_once()
    _, kwargs = mock_broadcast.call_args
    assert kwargs["site_name"] == "Filial SP"
    assert kwargs["link_name"] == "WAN-01-Claro"
    assert "OFFLINE" in kwargs["alert_type"]
    
    # Estado persistido com alerted=True
    state = load_state(state_file)
    link_info = state["sites"]["Filial SP"]["links"]["WAN-01-Claro"]
    assert link_info["alerted"] is True

def test_us1_no_duplicate_alert_after_alerted(mocker, mock_env, sample_cato_data):
    """Minuto 4: Continua offline, mas alerted já é True -> NÃO duplica alerta."""
    mock_broadcast = mocker.patch("src.monitor.broadcast_alert")
    state_file = mock_env["state_file"]
    
    caiu_as = datetime(2026, 9, 22, 10, 0, 0)
    save_state({
        "last_check": caiu_as.isoformat(),
        "sites": {
            "Filial SP": {
                "links": {
                    "WAN-01-Claro": {
                        "status": "OFFLINE",
                        "offline_since": caiu_as.isoformat(),
                        "alerted": True,
                        "last_alert_type": "LINK OFFLINE",
                        "last_alert_timestamp": "2026-09-22T10:03:00"
                    }
                }
            }
        }
    }, state_file)
    
    # Às 10:04 continua DISCONNECTED
    now = datetime(2026, 9, 22, 10, 4, 0)
    sample_cato_data["data"]["site"]["items"][0]["tunnels"][0]["status"] = "DISCONNECTED"
    mocker.patch("src.monitor.get_current_time", return_value=now)
    mocker.patch("src.monitor.get_network_status", return_value=sample_cato_data)
    
    check_status()
    
    # Não deve reenviar alerta
    mock_broadcast.assert_not_called()
