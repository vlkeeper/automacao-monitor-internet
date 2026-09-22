from datetime import datetime, timedelta
import pytest
from src.monitor import check_status
from src.state import load_state, save_state

def test_us2_return_alert_when_alerted_link_recovers(mocker, mock_env, sample_cato_data):
    """Link previamente alertado volta a ficar CONNECTED: dispara RETORNO e reseta estado."""
    mock_broadcast = mocker.patch("src.monitor.broadcast_alert")
    state_file = mock_env["state_file"]
    
    # Estado inicial: link estava OFFLINE e já havia sido alertado (alerted=True)
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
    
    # Às 10:15, o link volta a ficar CONNECTED
    now = datetime(2026, 9, 22, 10, 15, 0)
    mocker.patch("src.monitor.get_current_time", return_value=now)
    mocker.patch("src.monitor.get_network_status", return_value=sample_cato_data)
    
    check_status()
    
    # Valida que o alerta de RETORNO foi despachado
    mock_broadcast.assert_called_once()
    _, kwargs = mock_broadcast.call_args
    assert kwargs["site_name"] == "Filial SP"
    assert kwargs["link_name"] == "WAN-01-Claro"
    assert kwargs["alert_type"] == "RETORNO"
    assert kwargs["time_str"] == "10:15"
    
    # Valida que o estado foi resetado
    state = load_state(state_file)
    link_info = state["sites"]["Filial SP"]["links"]["WAN-01-Claro"]
    assert link_info["status"] == "ONLINE"
    assert link_info["offline_since"] is None
    assert link_info["alerted"] is False

def test_us2_no_return_alert_on_subsequent_online_cycle(mocker, mock_env, sample_cato_data):
    """No ciclo seguinte à recuperação, se continuar ONLINE, não dispara novo RETORNO."""
    mock_broadcast = mocker.patch("src.monitor.broadcast_alert")
    state_file = mock_env["state_file"]
    
    # Estado já está ONLINE
    now = datetime(2026, 9, 22, 10, 16, 0)
    save_state({
        "last_check": now.isoformat(),
        "sites": {
            "Filial SP": {
                "links": {
                    "WAN-01-Claro": {
                        "status": "ONLINE",
                        "offline_since": None,
                        "alerted": False,
                        "last_alert_type": None,
                        "last_alert_timestamp": None
                    }
                }
            }
        }
    }, state_file)
    
    mocker.patch("src.monitor.get_current_time", return_value=now)
    mocker.patch("src.monitor.get_network_status", return_value=sample_cato_data)
    
    check_status()
    
    mock_broadcast.assert_not_called()
