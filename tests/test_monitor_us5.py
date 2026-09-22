from datetime import datetime, timedelta
import pytest
from src.monitor import check_status
from src.state import save_state, load_state

def test_us5_in_flight_tolerance_preserved_across_restart(mocker, mock_env, sample_cato_data):
    """Link inativo há 2 min antes do restart; retoma execução e alerta aos 3 min acumulados."""
    mock_broadcast = mocker.patch("src.monitor.broadcast_alert")
    state_file = mock_env["state_file"]
    
    # 10:00 - Queda do link
    caiu_as = datetime(2026, 9, 22, 10, 0, 0)
    save_state({
        "last_check": datetime(2026, 9, 22, 10, 2, 0).isoformat(),
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
    
    # Simula reinicialização do daemon às 10:03 (3 minutos acumulados)
    now = datetime(2026, 9, 22, 10, 3, 0)
    sample_cato_data["data"]["site"]["items"][0]["tunnels"][0]["status"] = "DISCONNECTED"
    mocker.patch("src.monitor.get_current_time", return_value=now)
    mocker.patch("src.monitor.get_network_status", return_value=sample_cato_data)
    
    # Executa primeiro ciclo pós-restart
    check_status()
    
    # O alerta deve ser disparado pontualmente pois acumulou 3 min
    mock_broadcast.assert_called_once()
    _, kwargs = mock_broadcast.call_args
    assert kwargs["site_name"] == "Filial SP"
    assert kwargs["link_name"] == "WAN-01-Claro"
    
    # Estado é atualizado com alerted=True
    state = load_state(state_file)
    assert state["sites"]["Filial SP"]["links"]["WAN-01-Claro"]["alerted"] is True

def test_us5_alerted_state_preserved_no_duplicates_on_restart(mocker, mock_env, sample_cato_data):
    """Link já alertado antes do restart: pós-restart continua offline e NÃO reenvia alerta."""
    mock_broadcast = mocker.patch("src.monitor.broadcast_alert")
    state_file = mock_env["state_file"]
    
    caiu_as = datetime(2026, 9, 22, 9, 0, 0)
    save_state({
        "last_check": datetime(2026, 9, 22, 9, 30, 0).isoformat(),
        "sites": {
            "Filial SP": {
                "links": {
                    "WAN-01-Claro": {
                        "status": "OFFLINE",
                        "offline_since": caiu_as.isoformat(),
                        "alerted": True,
                        "last_alert_type": "LINK OFFLINE",
                        "last_alert_timestamp": "2026-09-22T09:03:00"
                    }
                }
            }
        }
    }, state_file)
    
    # Reinício às 10:00 com link ainda offline
    now = datetime(2026, 9, 22, 10, 0, 0)
    sample_cato_data["data"]["site"]["items"][0]["tunnels"][0]["status"] = "DISCONNECTED"
    mocker.patch("src.monitor.get_current_time", return_value=now)
    mocker.patch("src.monitor.get_network_status", return_value=sample_cato_data)
    
    check_status()
    
    # Não deve duplicar envio
    mock_broadcast.assert_not_called()
