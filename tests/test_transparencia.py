"""
Testes para o conector da API do Portal da Transparência.

Este módulo contém testes unitários para o conector da API do Portal da Transparência,
verificando a funcionalidade dos métodos de consulta e processamento de dados.
"""

import unittest
import pandas as pd
import os
import sys
from unittest.mock import patch, MagicMock

# Adicionar diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar módulo a ser testado
from src.api.transparencia import PortalTransparenciaAPI


class TestPortalTransparenciaAPI(unittest.TestCase):
    """Testes para a classe PortalTransparenciaAPI."""
    
    def setUp(self):
        """Configuração inicial para os testes."""
        # Criar instância do conector com token de teste
        self.api = PortalTransparenciaAPI(token="token_teste")
    
    @patch('src.api.transparencia.requests.get')
    def test_listar_endpoints_disponiveis(self, mock_get):
        """Testa o método listar_endpoints_disponiveis."""
        # Verificar se retorna a lista de endpoints
        endpoints = self.api.listar_endpoints_disponiveis()
        self.assertIsInstance(endpoints, list)
        self.assertGreater(len(endpoints), 0)
    
    @patch('src.api.transparencia.requests.get')
    def test_fazer_requisicao(self, mock_get):
        """Testa o método _fazer_requisicao."""
        # Configurar mock
        mock_response = MagicMock()
        mock_response.json.return_value = [{"id": 1, "nome": "Teste"}]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Fazer requisição
        resultado = self.api._fazer_requisicao("/endpoint-teste", {"param": "valor"})
        
        # Verificar resultado
        self.assertIsInstance(resultado, list)
        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]["id"], 1)
        
        # Verificar se a requisição foi feita corretamente
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertEqual(kwargs["headers"]["chave-api-dados"], "token_teste")
        self.assertEqual(kwargs["params"], {"param": "valor"})
    
    @patch('src.api.transparencia.requests.get')
    def test_consultar_bolsa_familia_por_municipio(self, mock_get):
        """Testa o método consultar_bolsa_familia_por_municipio."""
        # Configurar mock
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"id": 1, "municipio": "Teste", "valor": 1000.0},
            {"id": 2, "municipio": "Teste", "valor": 2000.0}
        ]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Fazer consulta
        df = self.api.consultar_bolsa_familia_por_municipio(
            codigo_ibge="1234567",
            mes=1,
            ano=2023
        )
        
        # Verificar resultado
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 2)
        self.assertEqual(df.iloc[0]["valor"], 1000.0)
        
        # Verificar se a requisição foi feita corretamente
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertEqual(kwargs["params"]["codigoIbge"], "1234567")
        self.assertEqual(kwargs["params"]["mesAno"], "01/2023")
    
    @patch('src.api.transparencia.requests.get')
    def test_consultar_endpoint_generico(self, mock_get):
        """Testa o método consultar_endpoint_generico."""
        # Configurar mock
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"id": 1, "nome": "Item 1"},
            {"id": 2, "nome": "Item 2"}
        ]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Fazer consulta
        df = self.api.consultar_endpoint_generico(
            nome_endpoint="orgaos-siafi",
            params={"param": "valor"},
            paginar=False
        )
        
        # Verificar resultado
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 2)
        self.assertEqual(df.iloc[1]["nome"], "Item 2")
        
        # Verificar se a requisição foi feita corretamente
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertEqual(kwargs["params"], {"param": "valor"})
    
    def test_salvar_dados(self):
        """Testa o método salvar_dados."""
        # Criar DataFrame de teste
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "nome": ["Item 1", "Item 2", "Item 3"],
            "valor": [100.0, 200.0, 300.0]
        })
        
        # Definir caminho temporário
        caminho_temp = "/tmp/teste_transparencia"
        
        # Testar diferentes formatos
        formatos = ["csv", "excel", "json", "pickle"]
        
        for formato in formatos:
            try:
                # Salvar dados
                caminho = self.api.salvar_dados(df, caminho_temp, formato)
                
                # Verificar se o arquivo foi criado
                self.assertTrue(os.path.exists(caminho))
                
                # Remover arquivo
                os.remove(caminho)
            except Exception as e:
                # Ignorar erros de dependências não instaladas
                if "No module named" not in str(e):
                    raise
    
    def test_validacao_parametros(self):
        """Testa a validação de parâmetros."""
        # Testar validação de código IBGE
        with self.assertRaises(ValueError):
            self.api.consultar_bolsa_familia_por_municipio("", 1, 2023)
        
        # Testar validação de mês
        with self.assertRaises(ValueError):
            self.api.consultar_bolsa_familia_por_municipio("1234567", 13, 2023)
        
        # Testar validação de ano
        with self.assertRaises(ValueError):
            self.api.consultar_bolsa_familia_por_municipio("1234567", 1, 1900)
        
        # Testar validação de endpoint
        with self.assertRaises(ValueError):
            self.api.consultar_endpoint_generico("endpoint-inexistente")


if __name__ == '__main__':
    unittest.main()
