from datetime import datetime, timedelta
import pytest
from src.monitor import check_status
from src.state import load_state, save_state

def test_us3_link_offline_partial_degradation(mocker, mock_env, sample_cato_data):
    """Filial SP tem 2 links. Se apenas 1 cair por 3 min, o alerta é LINK OFFLINE."""
    mock_broadcast = mocker.patch("src.monitor.broadcast_alert")
    state_file = mock_env["state_file"]
    
    # Filial SP: WAN-01-Claro caiu há 3 minutos; WAN-02-Vivo continua CONNECTED
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
                    },
                    "WAN-02-Vivo": {
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
    
    now = datetime(2026, 9, 22, 10, 3, 0)
    sample_cato_data["data"]["site"]["items"][0]["tunnels"][0]["status"] = "DISCONNECTED" # WAN-01
    sample_cato_data["data"]["site"]["items"][0]["tunnels"][1]["status"] = "CONNECTED"    # WAN-02
    
    mocker.patch("src.monitor.get_current_time", return_value=now)
    mocker.patch("src.monitor.get_network_status", return_value=sample_cato_data)
    
    check_status()
    
    mock_broadcast.assert_called_once()
    _, kwargs = mock_broadcast.call_args
    assert kwargs["site_name"] == "Filial SP"
    assert kwargs["link_name"] == "WAN-01-Claro"
    assert "LINK OFFLINE" in kwargs["alert_type"]
    assert "SITE OFFLINE" not in kwargs["alert_type"]

def test_us3_site_offline_total_isolation(mocker, mock_env, sample_cato_data):
    """Filial SP tem 2 links. Se AMBOS caírem por 3 min, o alerta é SITE OFFLINE."""
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
                    },
                    "WAN-02-Vivo": {
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
    
    now = datetime(2026, 9, 22, 10, 3, 0)
    # Ambos os túneis da Filial SP estão DISCONNECTED
    sample_cato_data["data"]["site"]["items"][0]["tunnels"][0]["status"] = "DISCONNECTED"
    sample_cato_data["data"]["site"]["items"][0]["tunnels"][1]["status"] = "DISCONNECTED"
    
    mocker.patch("src.monitor.get_current_time", return_value=now)
    mocker.patch("src.monitor.get_network_status", return_value=sample_cato_data)
    
    check_status()
    
    # Ambos dispararam alerta classificados como SITE OFFLINE
    assert mock_broadcast.call_count == 2
    for call in mock_broadcast.call_args_list:
        _, kwargs = call
        assert kwargs["site_name"] == "Filial SP"
        assert kwargs["alert_type"] == "SITE OFFLINE"
