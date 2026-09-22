import os
import sys
from dataclasses import dataclass
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env caso exista
load_dotenv()

def mask_secret(secret: str) -> str:
    """Ofusca um segredo para exibição segura em logs (Princípio III)."""
    if not secret:
        return "****"
    if len(secret) <= 6:
        return "****"
    return "*" * (len(secret) - 4) + secret[-4:]

@dataclass
class Config:
    """Estrutura tipada de configurações da aplicação."""
    CATO_API_KEY: str
    CATO_ACCOUNT_ID: str
    TEAMS_WEBHOOK_URL: str
    WA_PHONE_ID: str
    WA_ACCESS_TOKEN: str
    WA_RECIPIENT_PHONE: str
    WA_TEMPLATE_NAME: str = "cato_link_alert"
    STATE_FILE_PATH: str = "estado_links.json"
    POLLING_INTERVAL_SECONDS: int = 60
    FLAP_TOLERANCE_MINUTES: int = 3
    DAILY_DIGEST_TIME: str = "08:00"
    TIMEZONE: str = "America/Sao_Paulo"

def validate_config() -> Config:
    """
    Valida a presença de todas as variáveis obrigatórias (Princípio IV: Fail-Fast).
    Se qualquer variável obrigatória estiver ausente, encerra a execução com código 1.
    """
    required_vars = [
        "CATO_API_KEY",
        "CATO_ACCOUNT_ID",
        "TEAMS_WEBHOOK_URL",
        "WA_PHONE_ID",
        "WA_ACCESS_TOKEN",
        "WA_RECIPIENT_PHONE",
    ]

    missing = [var for var in required_vars if not os.getenv(var)]

    if missing:
        print(f"[ERRO CRÍTICO FAIL-FAST] Variáveis obrigatórias ausentes no ambiente: {', '.join(missing)}")
        sys.exit(1)

    try:
        polling_interval = int(os.getenv("POLLING_INTERVAL_SECONDS", "60"))
    except ValueError:
        polling_interval = 60

    try:
        flap_tolerance = int(os.getenv("FLAP_TOLERANCE_MINUTES", "3"))
    except ValueError:
        flap_tolerance = 3

    return Config(
        CATO_API_KEY=os.getenv("CATO_API_KEY", ""),
        CATO_ACCOUNT_ID=os.getenv("CATO_ACCOUNT_ID", ""),
        TEAMS_WEBHOOK_URL=os.getenv("TEAMS_WEBHOOK_URL", ""),
        WA_PHONE_ID=os.getenv("WA_PHONE_ID", ""),
        WA_ACCESS_TOKEN=os.getenv("WA_ACCESS_TOKEN", ""),
        WA_RECIPIENT_PHONE=os.getenv("WA_RECIPIENT_PHONE", ""),
        WA_TEMPLATE_NAME=os.getenv("WA_TEMPLATE_NAME", "cato_link_alert"),
        STATE_FILE_PATH=os.getenv("STATE_FILE_PATH", "estado_links.json"),
        POLLING_INTERVAL_SECONDS=polling_interval,
        FLAP_TOLERANCE_MINUTES=flap_tolerance,
        DAILY_DIGEST_TIME=os.getenv("DAILY_DIGEST_TIME", "08:00"),
        TIMEZONE=os.getenv("TIMEZONE", "America/Sao_Paulo"),
    )

# Instância padrão para conveniência e compatibilidade retroativa
def get_config() -> Config:
    return validate_config()