import time
import sys
import schedule
from src.config import validate_config
from src.monitor import check_status, send_daily_reminder, initialize_monitoring

def main() -> None:
    print("==================================================")
    print("🚀 Iniciando Monitoramento Cato Networks (Daemon)")
    print("==================================================")

    # 1. Validação Fail-Fast das Configurações (Princípio IV)
    config = validate_config()
    print("[INFO] Configurações de ambiente validadas com sucesso.")

    # 2. Inicialização e recuperação de estado persistido (Princípio I / US5)
    initialize_monitoring(config)

    # 3. Executa a primeira checagem imediata no boot
    print("[INFO] Executando ciclo inicial de monitoramento...")
    try:
        check_status(config)
    except Exception as e:
        print(f"[AVISO] Falha não-bloqueante no ciclo inicial: {type(e).__name__}")

    # 4. Agendamento dos ciclos periódicos
    schedule.every(config.POLLING_INTERVAL_SECONDS).seconds.do(check_status, config=config)
    schedule.every().day.at(config.DAILY_DIGEST_TIME).do(send_daily_reminder, config=config)
    print(f"[INFO] Agendamento ativo: Varredura a cada {config.POLLING_INTERVAL_SECONDS}s | Resumo diário às {config.DAILY_DIGEST_TIME}.")

    # 5. Loop infinito resiliente do Daemon
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except KeyboardInterrupt:
            print("\n[INFO] Monitoramento encerrado pelo operador via SIGINT/Ctrl+C.")
            break
        except Exception as e:
            # Princípio II: Protege o loop principal de exceções inesperadas
            print(f"[ERRO DEFENSIVO] Exceção capturada no loop do daemon: {type(e).__name__}. Retomando em 5 segundos...")
            time.sleep(5)

if __name__ == "__main__":
    main()