import json
import os
from typing import Optional

DEFAULT_STATE_FILE = "estado_links.json"

def _get_target_path(file_path: Optional[str] = None) -> str:
    if file_path:
        return file_path
    return os.getenv("STATE_FILE_PATH", DEFAULT_STATE_FILE)

def load_state(file_path: Optional[str] = None) -> dict:
    """
    Carrega o estado atual dos links a partir do arquivo JSON persistido.
    Retorna uma estrutura padrão vazia caso o arquivo não exista ou esteja corrompido.
    """
    path = _get_target_path(file_path)
    default_state = {"last_check": None, "sites": {}}

    if not os.path.exists(path):
        return default_state

    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
            if not isinstance(data, dict):
                return default_state
            if "sites" not in data:
                data["sites"] = {}
            return data
    except (json.JSONDecodeError, OSError) as e:
        print(f"[AVISO ESTADO] Falha ao ler arquivo de estado '{path}'. Utilizando estado limpo. Detalhe: {e}")
        return default_state

def save_state(state: dict, file_path: Optional[str] = None) -> None:
    """
    Salva o estado atualizado em disco de forma estritamente atômica (Princípio I da Constituição).
    1. Garante a existência do diretório pai.
    2. Grava os dados completos em um arquivo temporário (.tmp).
    3. Força flush/fsync no disco.
    4. Executa a substituição atômica via os.replace.
    """
    path = _get_target_path(file_path)
    parent_dir = os.path.dirname(path)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)

    temp_file = f"{path}.tmp"
    with open(temp_file, "w", encoding="utf-8") as file:
        json.dump(state, file, indent=2, ensure_ascii=False)
        file.flush()
        os.fsync(file.fileno())

    os.replace(temp_file, path)