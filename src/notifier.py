import os
from typing import Optional
import requests
from src.config import validate_config, Config

NOTIFIER_TIMEOUT_SECONDS = 10

def send_teams_alert(title: str, message: str, color: str = "D70000", config: Optional[Config] = None) -> bool:
    """
    Envia notificação formatada para o Microsoft Teams via Incoming Webhook.
    Princípio II: Timeout rigoroso de 10s e supressão defensiva de erros.
    """
    if config is None:
        try:
            config = validate_config()
        except SystemExit:
            return False

    payload = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "themeColor": color,
        "summary": title,
        "sections": [
            {
                "activityTitle": title,
                "text": message,
                "markdown": True
            }
        ]
    }

    try:
        response = requests.post(
            config.TEAMS_WEBHOOK_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=NOTIFIER_TIMEOUT_SECONDS
        )
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"[AVISO DEFENSIVO Teams] Falha no envio do alerta ({type(e).__name__}). Loop preservado.")
        return False
    except Exception as e:
        print(f"[AVISO DEFENSIVO Teams] Exceção genérica ({type(e).__name__}).")
        return False

def send_whatsapp_alert(site_name: str, link_name: str, status_msg: str, time_str: str, config: Optional[Config] = None) -> bool:
    """
    Envia notificação via Meta Cloud API (WhatsApp).
    Princípio II: Timeout rigoroso de 10s e supressão defensiva de erros.
    Princípio III: Sanitização de credenciais.
    """
    if config is None:
        try:
            config = validate_config()
        except SystemExit:
            return False

    url = f"https://graph.facebook.com/v17.0/{config.WA_PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {config.WA_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    # Monta payload de texto claro ou template se fornecido
    body_text = f"🚨 *ALERTA CATO NETWORKS*\n\n*Tipo:* {status_msg}\n*Localidade:* {site_name}\n*Link:* {link_name}\n*Horário:* {time_str}"
    
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": config.WA_RECIPIENT_PHONE,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": body_text
        }
    }

    try:
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=NOTIFIER_TIMEOUT_SECONDS
        )
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"[AVISO DEFENSIVO WhatsApp] Falha no envio do alerta ({type(e).__name__}). Loop preservado.")
        return False
    except Exception as e:
        print(f"[AVISO DEFENSIVO WhatsApp] Exceção genérica ({type(e).__name__}).")
        return False

def broadcast_alert(site_name: str, link_name: str, alert_type: str, time_str: str, config: Optional[Config] = None) -> None:
    """
    Dispara alertas de forma independente para Microsoft Teams e WhatsApp.
    Uma falha em um canal não afeta nem impede o envio no outro.
    """
    if "RETORNO" in alert_type:
        title = f"✅ RETORNO: {site_name} ({link_name})"
        msg = f"**Status:** RESTABELECIDO (ONLINE)\n\nO link **{link_name}** da filial **{site_name}** normalizou às **{time_str}**."
        color = "00B050"
    elif "SITE OFFLINE" in alert_type:
        title = f"🚨 ALERTA CRÍTICO: SITE OFFLINE - {site_name}"
        msg = f"**Gravidade:** MÁXIMA (TODOS OS LINKS INATIVOS)\n\nA filial **{site_name}** está completamente isolada desde às **{time_str}**."
        color = "D70000"
    else:
        title = f"⚠️ ALERTA: LINK OFFLINE - {site_name}"
        msg = f"**Gravidade:** PARCIAL (Degradação de redundância)\n\nO link **{link_name}** da filial **{site_name}** está inativo desde às **{time_str}**."
        color = "FFA500"

    send_teams_alert(title, msg, color=color, config=config)
    send_whatsapp_alert(site_name, link_name, alert_type, time_str, config=config)

def send_teams_daily_digest(report_text: str, config: Optional[Config] = None) -> bool:
    """
    Dispara o resumo matinal diário exclusivamente para o Microsoft Teams.
    """
    return send_teams_alert(
        title="📋 Boletim Matinal - Status de Links Cato Networks (08:00)",
        message=report_text,
        color="0078D7",
        config=config
    )