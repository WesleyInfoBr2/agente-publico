"""
Conector para a API do Portal da Transparência do Governo Federal.

Este módulo fornece classes e funções para acessar os dados disponíveis
na API do Portal da Transparência (http://api.portaldatransparencia.gov.br/).
"""

import os
import json
import time
import logging
import requests
from typing import Dict, List, Any, Optional, Union, Tuple
from urllib.parse import urljoin

# Configuração de logging
logger = logging.getLogger(__name__)

class TransparenciaAPI:
    """
    Cliente para a API do Portal da Transparência.
    
    Permite navegar e acessar dados disponíveis no Portal da Transparência
    do Governo Federal através de sua API REST.
    """
    
    BASE_URL = "http://api.portaldatransparencia.gov.br/api-de-dados/"
    
    # Mapeamento de categorias e endpoints
    CATEGORIAS = {
        "Bolsa Família e Benefícios Sociais": {
            "Bolsa Família": "bolsa-familia-por-municipio",
            "Garantia-Safra": "garantia-safra",
            "Seguro Defeso": "seguro-defeso",
        },
        "Servidores Públicos": {
            "Cadastro de Servidores": "servidores",
            "Remuneração": "remuneracao",
            "Afastamentos": "afastamentos",
        },
        "Despesas e Orçamento": {
            "Execução de Despesas": "despesas",
            "Transferências": "transferencias",
            "Emendas Parlamentares": "emendas",
        },
        "Contratos e Licitações": {
            "Contratos": "contratos",
            "Licitações": "licitacoes",
            "Empresas Contratadas": "empresas-contratadas",
        },
        "Cadastros": {
            "CEIS": "ceis",
            "CNEP": "cnep",
            "CEPIM": "cepim",
            "CEAF": "ceaf",
        }
    }
    
    def __init__(self, api_token: Optional[str] = None):
        """
        Inicializa o cliente da API do Portal da Transparência.
        
        Args:
            api_token: Token de acesso à API. Se não fornecido, tentará obter da
                       variável de ambiente TRANSPARENCIA_API_TOKEN.
        """
        self.api_token = api_token or os.environ.get("TRANSPARENCIA_API_TOKEN")
        if not self.api_token:
            logger.warning("Token da API do Portal da Transparência não fornecido. "
                          "Algumas consultas podem falhar.")
        
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "chave-api-dados": self.api_token or ""
        })
    
    def get_categorias(self) -> List[str]:
        """
        Retorna a lista de categorias disponíveis.
        
        Returns:
            Lista de nomes das categorias.
        """
        return list(self.CATEGORIAS.keys())
    
    def get_bases_por_categoria(self, categoria: str) -> Dict[str, str]:
        """
        Retorna as bases de dados disponíveis para uma categoria.
        
        Args:
            categoria: Nome da categoria.
            
        Returns:
            Dicionário com nomes das bases e seus endpoints.
            
        Raises:
            ValueError: Se a categoria não existir.
        """
        if categoria not in self.CATEGORIAS:
            raise ValueError(f"Categoria '{categoria}' não encontrada. "
                            f"Categorias disponíveis: {', '.join(self.get_categorias())}")
        
        return self.CATEGORIAS[categoria]
    
    def get_estrutura_hierarquica(self) -> Dict[str, Dict[str, str]]:
        """
        Retorna a estrutura hierárquica completa das bases disponíveis.
        
        Returns:
            Dicionário com a estrutura hierárquica (categoria -> base -> endpoint).
        """
        return self.CATEGORIAS
    
    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Realiza uma requisição à API.
        
        Args:
            endpoint: Endpoint da API.
            params: Parâmetros da requisição.
            
        Returns:
            Resposta da API em formato JSON.
            
        Raises:
            requests.HTTPError: Se a requisição falhar.
        """
        url = urljoin(self.BASE_URL, endpoint)
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            # Alguns endpoints retornam listas vazias em vez de objetos JSON
            if not response.text.strip():
                return []
                
            return response.json()
        except requests.HTTPError as e:
            logger.error(f"Erro ao acessar a API do Portal da Transparência: {e}")
            
            # Tratamento específico para erros comuns
            if response.status_code == 429:
                logger.warning("Limite de requisições atingido. Aguardando 60 segundos...")
                time.sleep(60)
                return self._make_request(endpoint, params)
            
            if response.status_code == 401:
                logger.error("Token de API inválido ou não fornecido.")
            
            raise
        except json.JSONDecodeError:
            logger.error(f"Erro ao decodificar resposta da API: {response.text}")
            return {"error": "Formato de resposta inválido", "raw_response": response.text}
    
    def get_metadados_base(self, categoria: str, base: str) -> Dict[str, Any]:
        """
        Obtém metadados sobre uma base específica.
        
        Args:
            categoria: Nome da categoria.
            base: Nome da base de dados.
            
        Returns:
            Dicionário com metadados da base.
            
        Raises:
            ValueError: Se a categoria ou base não existirem.
        """
        bases = self.get_bases_por_categoria(categoria)
        
        if base not in bases:
            raise ValueError(f"Base '{base}' não encontrada na categoria '{categoria}'. "
                            f"Bases disponíveis: {', '.join(bases.keys())}")
        
        # Aqui seria ideal ter um endpoint de metadados, mas como a API não fornece,
        # retornamos informações básicas
        return {
            "nome": base,
            "categoria": categoria,
            "endpoint": bases[base],
            "descricao": f"Dados de {base} do Portal da Transparência",
            "requer_parametros": True
        }
    
    def listar_parametros_necessarios(self, categoria: str, base: str) -> List[Dict[str, Any]]:
        """
        Lista os parâmetros necessários para consultar uma base específica.
        
        Args:
            categoria: Nome da categoria.
            base: Nome da base de dados.
            
        Returns:
            Lista de dicionários com informações sobre os parâmetros necessários.
            
        Raises:
            ValueError: Se a categoria ou base não existirem.
        """
        # Mapeamento de parâmetros por base
        # Isso é uma simplificação, idealmente viria da documentação da API
        parametros_por_base = {
            "Bolsa Família": [
                {"nome": "mesAno", "tipo": "string", "formato": "MM/YYYY", "obrigatorio": True, 
                 "descricao": "Mês e ano de referência (ex: 01/2023)"},
                {"nome": "codigoIbge", "tipo": "string", "obrigatorio": False, 
                 "descricao": "Código IBGE do município (opcional)"},
                {"nome": "pagina", "tipo": "integer", "obrigatorio": False, "padrao": 1, 
                 "descricao": "Número da página de resultados"}
            ],
            "Servidores": [
                {"nome": "orgao", "tipo": "string", "obrigatorio": True, 
                 "descricao": "Código do órgão (ex: 26000)"},
                {"nome": "pagina", "tipo": "integer", "obrigatorio": False, "padrao": 1, 
                 "descricao": "Número da página de resultados"}
            ],
            # Adicionar outros conforme necessário
        }
        
        bases = self.get_bases_por_categoria(categoria)
        
        if base not in bases:
            raise ValueError(f"Base '{base}' não encontrada na categoria '{categoria}'.")
        
        # Retorna parâmetros específicos ou um conjunto padrão
        return parametros_por_base.get(base, [
            {"nome": "pagina", "tipo": "integer", "obrigatorio": False, "padrao": 1, 
             "descricao": "Número da página de resultados"}
        ])
    
    def consultar_dados(self, categoria: str, base: str, 
                       parametros: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Consulta dados de uma base específica.
        
        Args:
            categoria: Nome da categoria.
            base: Nome da base de dados.
            parametros: Parâmetros da consulta.
            
        Returns:
            Lista de registros retornados pela API.
            
        Raises:
            ValueError: Se a categoria ou base não existirem.
            requests.HTTPError: Se a requisição à API falhar.
        """
        bases = self.get_bases_por_categoria(categoria)
        
        if base not in bases:
            raise ValueError(f"Base '{base}' não encontrada na categoria '{categoria}'.")
        
        endpoint = bases[base]
        
        # Validação básica de parâmetros obrigatórios
        parametros_necessarios = self.listar_parametros_necessarios(categoria, base)
        parametros = parametros or {}
        
        for param in parametros_necessarios:
            if param.get("obrigatorio", False) and param["nome"] not in parametros:
                raise ValueError(f"Parâmetro obrigatório '{param['nome']}' não fornecido para a base '{base}'.")
        
        # Realiza a consulta
        return self._make_request(endpoint, parametros)
    
    def obter_amostra_dados(self, categoria: str, base: str, 
                           tamanho: int = 5) -> List[Dict[str, Any]]:
        """
        Obtém uma amostra de dados de uma base específica.
        
        Args:
            categoria: Nome da categoria.
            base: Nome da base de dados.
            tamanho: Número de registros a serem retornados.
            
        Returns:
            Lista com amostra de registros.
            
        Raises:
            ValueError: Se a categoria ou base não existirem.
            requests.HTTPError: Se a requisição à API falhar.
        """
        # Parâmetros padrão para obter uma amostra
        # Isso é uma simplificação, cada base pode exigir parâmetros diferentes
        parametros_padrao = {
            "Bolsa Família": {"mesAno": "01/2023", "pagina": 1},
            "Servidores": {"orgao": "26000", "pagina": 1},
            # Adicionar outros conforme necessário
        }
        
        bases = self.get_bases_por_categoria(categoria)
        
        if base not in bases:
            raise ValueError(f"Base '{base}' não encontrada na categoria '{categoria}'.")
        
        # Usa parâmetros padrão específicos ou genéricos
        parametros = parametros_padrao.get(base, {"pagina": 1})
        
        try:
            dados = self.consultar_dados(categoria, base, parametros)
            return dados[:tamanho] if isinstance(dados, list) else []
        except Exception as e:
            logger.error(f"Erro ao obter amostra de dados: {e}")
            return []
