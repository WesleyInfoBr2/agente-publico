"""
Testes para o conector da API do Catálogo Nacional de Dados Públicos (CNDP).

Este módulo contém testes unitários para o conector da API do CNDP,
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
from src.api.cndp import CNDPAPI


class TestCNDPAPI(unittest.TestCase):
    """Testes para a classe CNDPAPI."""
    
    def setUp(self):
        """Configuração inicial para os testes."""
        # Criar instância do conector com token de teste
        self.api = CNDPAPI(token="token_teste")
    
    @patch('src.api.cndp.requests.get')
    def test_fazer_requisicao(self, mock_get):
        """Testa o método _fazer_requisicao."""
        # Configurar mock
        mock_response = MagicMock()
        mock_response.json.return_value = {"result": [{"id": 1, "name": "Teste"}]}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Fazer requisição
        resultado = self.api._fazer_requisicao("/endpoint-teste", {"param": "valor"})
        
        # Verificar resultado
        self.assertIsInstance(resultado, dict)
        self.assertIn("result", resultado)
        self.assertEqual(len(resultado["result"]), 1)
        self.assertEqual(resultado["result"][0]["id"], 1)
        
        # Verificar se a requisição foi feita corretamente
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer token_teste")
        self.assertEqual(kwargs["params"], {"param": "valor"})
    
    @patch('src.api.cndp.requests.get')
    def test_listar_temas(self, mock_get):
        """Testa o método listar_temas."""
        # Configurar mock
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": [
                {"id": "tema1", "name": "Tema 1", "display_name": "Tema 1", "description": "Descrição 1"},
                {"id": "tema2", "name": "Tema 2", "display_name": "Tema 2", "description": "Descrição 2"}
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Fazer consulta
        df = self.api.listar_temas()
        
        # Verificar resultado
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 2)
        self.assertEqual(df.iloc[0]["display_name"], "Tema 1")
        
        # Verificar se a requisição foi feita corretamente
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertTrue(args[0].endswith("/action/group_list"))
    
    @patch('src.api.cndp.requests.get')
    def test_listar_organizacoes(self, mock_get):
        """Testa o método listar_organizacoes."""
        # Configurar mock
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": [
                {"id": "org1", "name": "Org 1", "display_name": "Organização 1", "description": "Descrição 1"},
                {"id": "org2", "name": "Org 2", "display_name": "Organização 2", "description": "Descrição 2"}
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Fazer consulta
        df = self.api.listar_organizacoes()
        
        # Verificar resultado
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 2)
        self.assertEqual(df.iloc[1]["display_name"], "Organização 2")
        
        # Verificar se a requisição foi feita corretamente
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertTrue(args[0].endswith("/action/organization_list"))
    
    @patch('src.api.cndp.requests.get')
    def test_buscar_conjuntos_dados(self, mock_get):
        """Testa o método buscar_conjuntos_dados."""
        # Configurar mock
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": {
                "count": 2,
                "results": [
                    {
                        "id": "conj1",
                        "name": "conjunto-1",
                        "title": "Conjunto 1",
                        "notes": "Descrição 1",
                        "organization": {"name": "org1"},
                        "metadata_created": "2023-01-01",
                        "metadata_modified": "2023-01-02",
                        "url": "http://exemplo.com/conj1",
                        "resources": [{"id": "rec1"}, {"id": "rec2"}],
                        "groups": [{"name": "tema1"}]
                    },
                    {
                        "id": "conj2",
                        "name": "conjunto-2",
                        "title": "Conjunto 2",
                        "notes": "Descrição 2",
                        "organization": {"name": "org2"},
                        "metadata_created": "2023-02-01",
                        "metadata_modified": "2023-02-02",
                        "url": "http://exemplo.com/conj2",
                        "resources": [{"id": "rec3"}],
                        "groups": [{"name": "tema2"}]
                    }
                ]
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Fazer consulta
        df = self.api.buscar_conjuntos_dados(
            query="teste",
            tema="tema1",
            organizacao="org1",
            pagina=1,
            itens_por_pagina=10
        )
        
        # Verificar resultado
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 2)
        self.assertEqual(df.iloc[0]["titulo"], "Conjunto 1")
        self.assertEqual(df.iloc[1]["titulo"], "Conjunto 2")
        self.assertEqual(df.attrs["total"], 2)
        
        # Verificar se a requisição foi feita corretamente
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertTrue(args[0].endswith("/action/package_search"))
        self.assertEqual(kwargs["params"]["q"], "teste")
        self.assertEqual(kwargs["params"]["groups"], "tema1")
        self.assertEqual(kwargs["params"]["organization"], "org1")
        self.assertEqual(kwargs["params"]["rows"], 10)
        self.assertEqual(kwargs["params"]["start"], 0)
    
    @patch('src.api.cndp.requests.get')
    def test_obter_detalhes_conjunto(self, mock_get):
        """Testa o método obter_detalhes_conjunto."""
        # Configurar mock
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": {
                "id": "conj1",
                "name": "conjunto-1",
                "title": "Conjunto 1",
                "notes": "Descrição 1",
                "organization": {"name": "org1"},
                "resources": [
                    {"id": "rec1", "name": "Recurso 1", "format": "CSV"},
                    {"id": "rec2", "name": "Recurso 2", "format": "JSON"}
                ]
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Fazer consulta
        detalhes = self.api.obter_detalhes_conjunto("conj1")
        
        # Verificar resultado
        self.assertIsInstance(detalhes, dict)
        self.assertEqual(detalhes["id"], "conj1")
        self.assertEqual(detalhes["title"], "Conjunto 1")
        self.assertEqual(len(detalhes["resources"]), 2)
        
        # Verificar se a requisição foi feita corretamente
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertTrue(args[0].endswith("/action/package_show"))
        self.assertEqual(kwargs["params"]["id"], "conj1")
    
    @patch('src.api.cndp.requests.get')
    def test_listar_recursos_conjunto(self, mock_get):
        """Testa o método listar_recursos_conjunto."""
        # Configurar mock para obter_detalhes_conjunto
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": {
                "id": "conj1",
                "name": "conjunto-1",
                "resources": [
                    {"id": "rec1", "name": "Recurso 1", "format": "CSV", "url": "http://exemplo.com/rec1.csv"},
                    {"id": "rec2", "name": "Recurso 2", "format": "JSON", "url": "http://exemplo.com/rec2.json"}
                ]
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Fazer consulta
        df = self.api.listar_recursos_conjunto("conj1")
        
        # Verificar resultado
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 2)
        self.assertEqual(df.iloc[0]["name"], "Recurso 1")
        self.assertEqual(df.iloc[1]["format"], "JSON")
        
        # Verificar se a requisição foi feita corretamente
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertTrue(args[0].endswith("/action/package_show"))
        self.assertEqual(kwargs["params"]["id"], "conj1")
    
    @patch('src.api.cndp.requests.get')
    def test_buscar_recursos_por_formato(self, mock_get):
        """Testa o método buscar_recursos_por_formato."""
        # Configurar mock
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": {
                "count": 2,
                "results": [
                    {"id": "rec1", "name": "Recurso 1", "format": "CSV", "url": "http://exemplo.com/rec1.csv"},
                    {"id": "rec2", "name": "Recurso 2", "format": "CSV", "url": "http://exemplo.com/rec2.csv"}
                ]
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Fazer consulta
        df = self.api.buscar_recursos_por_formato(
            formato="CSV",
            query="dados",
            pagina=1,
            itens_por_pagina=10
        )
        
        # Verificar resultado
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 2)
        self.assertEqual(df.iloc[0]["name"], "Recurso 1")
        self.assertEqual(df.iloc[1]["format"], "CSV")
        self.assertEqual(df.attrs["total"], 2)
        
        # Verificar se a requisição foi feita corretamente
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertTrue(args[0].endswith("/action/resource_search"))
        self.assertEqual(kwargs["params"]["query"], "format:CSV dados")
        self.assertEqual(kwargs["params"]["rows"], 10)
        self.assertEqual(kwargs["params"]["start"], 0)
    
    def test_salvar_dados(self):
        """Testa o método salvar_dados."""
        # Criar DataFrame de teste
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "nome": ["Item 1", "Item 2", "Item 3"],
            "valor": [100.0, 200.0, 300.0]
        })
        
        # Definir caminho temporário
        caminho_temp = "/tmp/teste_cndp"
        
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


if __name__ == '__main__':
    unittest.main()
