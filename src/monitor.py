from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from src.config import validate_config, Config
from src.cato_api import get_network_status
from src.state import load_state, save_state
from src.notifier import broadcast_alert, send_teams_daily_digest

def get_current_time() -> datetime:
    """Retorna a hora atual. Isolado para facilitar testes e simulação de tempo."""
    return datetime.now()

def initialize_monitoring(config: Optional[Config] = None) -> Dict[str, Any]:
    """
    Inicializa o subsistema de monitoramento na subida da aplicação (US5):
    - Carrega ou inicializa o arquivo de estado em disco.
    - Assegura integridade prévia antes do início do agendamento.
    """
    if config is None:
        config = validate_config()

    state = load_state(config.STATE_FILE_PATH)
    total_sites = len(state.get("sites", {}))
    print(f"[INFO] Estado carregado de '{config.STATE_FILE_PATH}'. Sites rastreados previamente: {total_sites}")
    return state

def check_status(config: Optional[Config] = None) -> None:
    """
    Executa um ciclo completo de monitoramento (executado a cada 60s):
    1. Consulta a telemetria da Cato Networks de forma defensiva.
    2. Carrega o estado persistido do disco.
    3. Analisa o estado de cada site e de seus respectivos links (duas etapas).
    4. Aplica a tolerância de 3 minutos para filtrar flapping transitório.
    5. Grava o estado atualizado em disco ATOMICAMENTE antes de qualquer notificação (Princípio I).
    6. Despacha alertas e mensagens de retorno para Teams e WhatsApp.
    """
    if config is None:
        try:
            config = validate_config()
        except SystemExit:
            return

    cato_data = get_network_status(config)
    if not cato_data or "data" not in cato_data:
        # Falha na API tratada defensivamente; preserva o estado atual sem alterações
        return

    state = load_state(config.STATE_FILE_PATH)
    if "sites" not in state:
        state["sites"] = {}

    now = get_current_time()
    state["last_check"] = now.isoformat()

    sites_items = cato_data.get("data", {}).get("site", {}).get("items", [])
    
    # Filas de notificações para envio após a persistência do estado
    alerts_to_dispatch: List[Dict[str, Any]] = []
    returns_to_dispatch: List[Dict[str, Any]] = []

    for site in sites_items:
        site_name = site.get("name", "Site Sem Nome")
        tunnels = site.get("tunnels", [])

        if site_name not in state["sites"]:
            state["sites"][site_name] = {"links": {}}

        site_links_state = state["sites"][site_name]["links"]
        total_links = len(tunnels)

        # Etapa 1: Mapeia o status atual dos links da filial
        current_status_map = {}
        offline_count = 0
        for tunnel in tunnels:
            t_name = tunnel.get("name", "Desconhecido")
            is_connected = (tunnel.get("status") == "CONNECTED")
            current_status_map[t_name] = is_connected
            if not is_connected:
                offline_count += 1

        is_site_completely_down = (total_links > 0 and offline_count == total_links)

        # Etapa 2: Avalia transições, janela de tolerância e retorno
        for tunnel in tunnels:
            link_name = tunnel.get("name", "Desconhecido")
            is_connected = current_status_map[link_name]

            if link_name not in site_links_state:
                site_links_state[link_name] = {
                    "status": "ONLINE",
                    "offline_since": None,
                    "alerted": False,
                    "last_alert_type": None,
                    "last_alert_timestamp": None
                }

            link_info = site_links_state[link_name]

            if not is_connected:
                # Link está offline no momento
                if link_info["status"] == "ONLINE":
                    # Minuto 0: Anota o início da queda e mantém silêncio (filtro anti-flap)
                    link_info["status"] = "OFFLINE"
                    link_info["offline_since"] = now.isoformat()
                    link_info["alerted"] = False
                    link_info["last_alert_type"] = None
                    link_info["last_alert_timestamp"] = None
                elif link_info["status"] == "OFFLINE" and not link_info["alerted"]:
                    # Minuto 1+: Verifica se atingiu a janela de 3 minutos
                    if link_info["offline_since"]:
                        offline_since_dt = datetime.fromisoformat(link_info["offline_since"])
                        tolerance_limit = timedelta(minutes=config.FLAP_TOLERANCE_MINUTES)
                        if (now - offline_since_dt) >= tolerance_limit:
                            # 3 minutos ininterruptos atingidos: agenda alerta
                            alert_type = "SITE OFFLINE" if is_site_completely_down else f"LINK OFFLINE ({link_name})"
                            link_info["alerted"] = True
                            link_info["last_alert_type"] = alert_type
                            link_info["last_alert_timestamp"] = now.isoformat()

                            alerts_to_dispatch.append({
                                "site_name": site_name,
                                "link_name": link_name,
                                "alert_type": alert_type,
                                "time_str": offline_since_dt.strftime("%H:%M")
                            })
            else:
                # Link está online no momento
                if link_info["status"] == "OFFLINE":
                    # Restabelecimento detectado
                    if link_info["alerted"]:
                        # Alerta prévio havia sido enviado: agenda notificação de retorno
                        returns_to_dispatch.append({
                            "site_name": site_name,
                            "link_name": link_name,
                            "alert_type": "RETORNO",
                            "time_str": now.strftime("%H:%M")
                        })
                    
                    # Limpa o estado da inatividade (seja retorno após alerta ou flap absorvido)
                    link_info["status"] = "ONLINE"
                    link_info["offline_since"] = None
                    link_info["alerted"] = False
                    link_info["last_alert_type"] = None
                    link_info["last_alert_timestamp"] = None

    # PRINCÍPIO I: Grava o estado atualizado em disco ANTES de despachar alertas externos
    save_state(state, config.STATE_FILE_PATH)

    # Despacha alertas acumulados
    for alert in alerts_to_dispatch:
        broadcast_alert(
            site_name=alert["site_name"],
            link_name=alert["link_name"],
            alert_type=alert["alert_type"],
            time_str=alert["time_str"],
            config=config
        )

    # Despacha confirmações de retorno acumuladas
    for ret in returns_to_dispatch:
        broadcast_alert(
            site_name=ret["site_name"],
            link_name=ret["link_name"],
            alert_type="RETORNO",
            time_str=ret["time_str"],
            config=config
        )

def send_daily_reminder(config: Optional[Config] = None) -> None:
    """
    Rotina disparada às 08:00 para envio do boletim diário consolidado para o Microsoft Teams.
    """
    if config is None:
        try:
            config = validate_config()
        except SystemExit:
            return

    state = load_state(config.STATE_FILE_PATH)
    sites = state.get("sites", {})
    now = get_current_time()

    inactive_links = []
    for site_name, site_data in sites.items():
        for link_name, link_info in site_data.get("links", {}).items():
            if link_info.get("status") == "OFFLINE" and link_info.get("offline_since"):
                since_dt = datetime.fromisoformat(link_info["offline_since"])
                # Inclui links com inatividade superior à tolerância
                if (now - since_dt) >= timedelta(minutes=config.FLAP_TOLERANCE_MINUTES):
                    duration = now - since_dt
                    days = duration.days
                    hours = duration.seconds // 3600
                    inactive_links.append(
                        f"* **{site_name}** (`{link_name}`): Inativo há **{days} dias e {hours} horas** (Desde {since_dt.strftime('%d/%m %H:%M')})"
                    )

    if inactive_links:
        report_body = (
            "Foram identificados os seguintes links com inatividade persistente:\n\n"
            + "\n".join(inactive_links)
        )
    else:
        report_body = "✅ **100% dos links e sites monitorados estão operacionais no momento.**"

    send_teams_daily_digest(report_body, config=config)