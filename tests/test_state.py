import os
import json
import pytest
from src.state import load_state, save_state

def test_load_state_non_existent(tmp_path):
    """Carregamento de arquivo inexistente deve retornar estrutura vazia padrão."""
    fake_path = str(tmp_path / "nao_existe.json")
    state = load_state(fake_path)
    assert isinstance(state, dict)
    assert state.get("sites") == {}

def test_save_and_load_state_atomic(tmp_path):
    """Princípio I: Gravação atômica via .tmp e os.replace preservando os dados com fidelidade."""
    state_file = str(tmp_path / "subdir" / "estado.json")
    sample_data = {
        "last_check": "2026-09-22T11:00:00-03:00",
        "sites": {
            "Filial SP": {
                "links": {
                    "WAN-01": {
                        "status": "OFFLINE",
                        "offline_since": "2026-09-22T10:57:00-03:00",
                        "alerted": True,
                        "last_alert_type": "LINK OFFLINE",
                        "last_alert_timestamp": "2026-09-22T11:00:00-03:00"
                    }
                }
            }
        }
    }
    
    save_state(sample_data, state_file)
    
    assert os.path.exists(state_file)
    # Garante que o arquivo temporário foi consumido pelo os.replace
    assert not os.path.exists(f"{state_file}.tmp")
    
    loaded = load_state(state_file)
    assert loaded == sample_data
    assert loaded["sites"]["Filial SP"]["links"]["WAN-01"]["alerted"] is True

def test_load_state_corrupted_json(tmp_path):
    """Arquivo corrompido deve ser tratado sem abortar a aplicação."""
    corrupted_file = str(tmp_path / "corrupted.json")
    with open(corrupted_file, "w") as f:
        f.write("{ invalid json content ...")
        
    state = load_state(corrupted_file)
    assert isinstance(state, dict)
    assert state.get("sites") == {}
