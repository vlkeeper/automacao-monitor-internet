from datetime import datetime, timedelta
import pytest
from src.monitor import send_daily_reminder
from src.state import save_state

def test_us4_daily_reminder_with_inactive_links(mocker, mock_env):
    """Resumo diário às 08:00: calcula dias/horas e envia EXCLUSIVAMENTE para o Teams."""
    mock_teams_digest = mocker.patch("src.monitor.send_teams_daily_digest")
    mock_whatsapp = mocker.patch("src.notifier.send_whatsapp_alert")
    state_file = mock_env["state_file"]
    
    # 08:00 do dia 22/09/2026
    now = datetime(2026, 9, 22, 8, 0, 0)
    mocker.patch("src.monitor.get_current_time", return_value=now)
    
    # Link 1 caiu há 26 horas (1 dia e 2 horas)
    caiu_link1 = now - timedelta(days=1, hours=2)
    # Link 2 caiu há 5 horas (0 dias e 5 horas)
    caiu_link2 = now - timedelta(hours=5)
    
    save_state({
        "last_check": now.isoformat(),
        "sites": {
            "Filial SP": {
                "links": {
                    "WAN-01-Claro": {
                        "status": "OFFLINE",
                        "offline_since": caiu_link1.isoformat(),
                        "alerted": True,
                        "last_alert_type": "LINK OFFLINE",
                        "last_alert_timestamp": caiu_link1.isoformat()
                    }
                }
            },
            "Filial RJ": {
                "links": {
                    "WAN-01-Oi": {
                        "status": "OFFLINE",
                        "offline_since": caiu_link2.isoformat(),
                        "alerted": True,
                        "last_alert_type": "LINK OFFLINE",
                        "last_alert_timestamp": caiu_link2.isoformat()
                    }
                }
            }
        }
    }, state_file)
    
    send_daily_reminder()
    
    # Valida envio exclusivo para o Teams
    mock_teams_digest.assert_called_once()
    report_text = mock_teams_digest.call_args[0][0]
    
    assert "Filial SP" in report_text
    assert "1 dias e 2 horas" in report_text or "1 dia" in report_text
    assert "Filial RJ" in report_text
    assert "0 dias e 5 horas" in report_text
    
    # Garante que NENHUM alerta foi disparado para o WhatsApp (US4 e US05)
    mock_whatsapp.assert_not_called()

def test_us4_daily_reminder_all_online_positive_check(mocker, mock_env):
    """Resumo diário às 08:00 com 100% de links operacionais: envia status positivo."""
    mock_teams_digest = mocker.patch("src.monitor.send_teams_daily_digest")
    state_file = mock_env["state_file"]
    
    now = datetime(2026, 9, 22, 8, 0, 0)
    mocker.patch("src.monitor.get_current_time", return_value=now)
    
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
    
    send_daily_reminder()
    
    mock_teams_digest.assert_called_once()
    report_text = mock_teams_digest.call_args[0][0]
    assert "100%" in report_text or "operacionais" in report_text
