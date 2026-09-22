import requests
import pytest
from src.cato_api import get_network_status, CATO_GRAPHQL_URL

def test_get_network_status_success(mocker, mock_env, sample_cato_data):
    """Verifica retorno bem-sucedido dos dados estruturados da Cato."""
    mock_response = mocker.MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = sample_cato_data
    mock_response.raise_for_status.return_value = None
    
    mock_post = mocker.patch("requests.post", return_value=mock_response)
    
    result = get_network_status()
    assert result is not None
    assert "data" in result
    items = result["data"]["site"]["items"]
    assert len(items) == 2
    assert items[0]["name"] == "Filial SP"
    
    # Valida parâmetros da chamada defensiva (Princípio II)
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert args[0] == CATO_GRAPHQL_URL
    assert kwargs["timeout"] == 15
    assert "x-api-key" in kwargs["headers"]

def test_get_network_status_timeout_defensive(mocker, mock_env):
    """Princípio II: Timeout deve ser capturado localmente e retornar dicionário vazio sem quebrar o loop."""
    mocker.patch("requests.post", side_effect=requests.exceptions.Timeout("Connection timed out after 15s"))
    result = get_network_status()
    assert result == {}

def test_get_network_status_http_error_defensive(mocker, mock_env):
    """Princípio II: Erro 500 ou 429 deve ser tratado e retornar dicionário vazio."""
    mock_response = mocker.MagicMock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("500 Server Error")
    mocker.patch("requests.post", return_value=mock_response)
    result = get_network_status()
    assert result == {}
