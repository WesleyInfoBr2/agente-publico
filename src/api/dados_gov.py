"""
Conector para a API do Portal Brasileiro de Dados Abertos (dados.gov.br).

Este módulo fornece classes e funções para acessar os dados disponíveis
na API do Portal Brasileiro de Dados Abertos (https://dados.gov.br/).
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

class DadosGovAPI:
    """
    Cliente para a API do Portal Brasileiro de Dados Abertos.
    
    Permite navegar e acessar dados disponíveis no Portal Brasileiro de Dados Abertos
    através de sua API CKAN.
    """
    
    BASE_URL = "https://dados.gov.br/api/3/"
    
    # Categorias principais (temas)
    CATEGORIAS = {
        "Saúde": ["saude", "covid-19", "datasus", "hospitais", "medicamentos"],
        "Educação": ["educacao", "escolas", "universidades", "inep", "enem"],
        "Economia e Finanças": ["economia", "financas", "orcamento", "banco-central", "comercio-exterior"],
        "Infraestrutura e Meio Ambiente": ["meio-ambiente", "infraestrutura", "transportes", "energia", "recursos-naturais"],
        "Agricultura": ["agricultura", "agropecuaria", "pesca", "extrativismo"],
        "Segurança Pública": ["seguranca-publica", "criminalidade", "sistema-prisional"],
        "Cultura e Esporte": ["cultura", "esporte", "turismo", "lazer"],
        "Administração Pública": ["administracao-publica", "servidores", "orgaos-publicos"]
    }
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Inicializa o cliente da API do Portal Brasileiro de Dados Abertos.
        
        Args:
            api_key: Chave de API (opcional, a maioria das consultas não requer).
                    Se não fornecida, tentará obter da variável de ambiente DADOSGOV_API_KEY.
        """
        self.api_key = api_key or os.environ.get("DADOSGOV_API_KEY")
        
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "DadosGovBR-Python-Client/1.0"
        })
        
        if self.api_key:
            self.session.headers.update({"Authorization": self.api_key})
    
    def get_categorias(self) -> List[str]:
        """
        Retorna a lista de categorias disponíveis.
        
        Returns:
            Lista de nomes das categorias.
        """
        return list(self.CATEGORIAS.keys())
    
    def get_tags_por_categoria(self, categoria: str) -> List[str]:
        """
        Retorna as tags associadas a uma categoria.
        
        Args:
            categoria: Nome da categoria.
            
        Returns:
            Lista de tags.
            
        Raises:
            ValueError: Se a categoria não existir.
        """
        if categoria not in self.CATEGORIAS:
            raise ValueError(f"Categoria '{categoria}' não encontrada. "
                            f"Categorias disponíveis: {', '.join(self.get_categorias())}")
        
        return self.CATEGORIAS[categoria]
    
    def get_estrutura_hierarquica(self) -> Dict[str, List[str]]:
        """
        Retorna a estrutura hierárquica completa das categorias e tags.
        
        Returns:
            Dicionário com a estrutura hierárquica (categoria -> tags).
        """
        return self.CATEGORIAS
    
    def _make_request(self, action: str, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Realiza uma requisição à API.
        
        Args:
            action: Ação da API (ex: 'action').
            endpoint: Endpoint específico (ex: 'package_search').
            params: Parâmetros da requisição.
            
        Returns:
            Resposta da API em formato JSON.
            
        Raises:
            requests.HTTPError: Se a requisição falhar.
        """
        url = urljoin(self.BASE_URL, f"{action}/{endpoint}")
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            # Alguns endpoints retornam listas vazias em vez de objetos JSON
            if not response.text.strip():
                return []
                
            return response.json()
        except requests.HTTPError as e:
            logger.error(f"Erro ao acessar a API do Portal Brasileiro de Dados Abertos: {e}")
            
            # Tratamento específico para erros comuns
            if response.status_code == 429:
                logger.warning("Limite de requisições atingido. Aguardando 60 segundos...")
                time.sleep(60)
                return self._make_request(action, endpoint, params)
            
            raise
        except json.JSONDecodeError:
            logger.error(f"Erro ao decodificar resposta da API: {response.text}")
            return {"error": "Formato de resposta inválido", "raw_response": response.text}
    
    def buscar_conjuntos_dados(self, termo: Optional[str] = None, 
                              tags: Optional[List[str]] = None,
                              organizacao: Optional[str] = None,
                              limite: int = 10) -> List[Dict[str, Any]]:
        """
        Busca conjuntos de dados no portal.
        
        Args:
            termo: Termo de busca (opcional).
            tags: Lista de tags para filtrar (opcional).
            organizacao: Nome da organização (opcional).
            limite: Número máximo de resultados.
            
        Returns:
            Lista de conjuntos de dados encontrados.
        """
        params = {
            "q": termo or "",
            "rows": limite
        }
        
        # Adiciona filtros de tags se fornecidos
        if tags:
            params["fq"] = " AND ".join([f'tags:"{tag}"' for tag in tags])
        
        # Adiciona filtro de organização se fornecido
        if organizacao:
            params["fq"] = params.get("fq", "") + f' organization:"{organizacao}"'
        
        response = self._make_request("action", "package_search", params)
        
        if "result" in response and "results" in response["result"]:
            return response["result"]["results"]
        
        return []
    
    def buscar_conjuntos_por_categoria(self, categoria: str, limite: int = 10) -> List[Dict[str, Any]]:
        """
        Busca conjuntos de dados por categoria.
        
        Args:
            categoria: Nome da categoria.
            limite: Número máximo de resultados.
            
        Returns:
            Lista de conjuntos de dados encontrados.
            
        Raises:
            ValueError: Se a categoria não existir.
        """
        tags = self.get_tags_por_categoria(categoria)
        return self.buscar_conjuntos_dados(tags=tags, limite=limite)
    
    def obter_detalhes_conjunto(self, id_conjunto: str) -> Dict[str, Any]:
        """
        Obtém detalhes de um conjunto de dados específico.
        
        Args:
            id_conjunto: ID ou nome do conjunto de dados.
            
        Returns:
            Dicionário com detalhes do conjunto de dados.
        """
        response = self._make_request("action", "package_show", {"id": id_conjunto})
        
        if "result" in response:
            return response["result"]
        
        return {}
    
    def listar_recursos_conjunto(self, id_conjunto: str) -> List[Dict[str, Any]]:
        """
        Lista os recursos disponíveis em um conjunto de dados.
        
        Args:
            id_conjunto: ID ou nome do conjunto de dados.
            
        Returns:
            Lista de recursos disponíveis.
        """
        detalhes = self.obter_detalhes_conjunto(id_conjunto)
        
        if "resources" in detalhes:
            return detalhes["resources"]
        
        return []
    
    def obter_metadados_recurso(self, id_recurso: str) -> Dict[str, Any]:
        """
        Obtém metadados de um recurso específico.
        
        Args:
            id_recurso: ID do recurso.
            
        Returns:
            Dicionário com metadados do recurso.
        """
        response = self._make_request("action", "resource_show", {"id": id_recurso})
        
        if "result" in response:
            return response["result"]
        
        return {}
    
    def obter_dados_recurso(self, url_recurso: str) -> Any:
        """
        Obtém os dados de um recurso específico.
        
        Args:
            url_recurso: URL do recurso.
            
        Returns:
            Conteúdo do recurso (formato depende do tipo de recurso).
            
        Raises:
            requests.HTTPError: Se a requisição falhar.
        """
        try:
            response = self.session.get(url_recurso)
            response.raise_for_status()
            
            # Tenta determinar o tipo de conteúdo
            content_type = response.headers.get("Content-Type", "")
            
            if "json" in content_type:
                return response.json()
            elif "csv" in content_type:
                return response.text
            else:
                return response.content
        except requests.HTTPError as e:
            logger.error(f"Erro ao acessar recurso: {e}")
            raise
    
    def listar_organizacoes(self, limite: int = 100) -> List[Dict[str, Any]]:
        """
        Lista as organizações disponíveis no portal.
        
        Args:
            limite: Número máximo de resultados.
            
        Returns:
            Lista de organizações.
        """
        response = self._make_request("action", "organization_list", {"all_fields": True, "limit": limite})
        
        if "result" in response:
            return response["result"]
        
        return []
    
    def obter_amostra_dados(self, categoria: str, limite: int = 5) -> List[Dict[str, Any]]:
        """
        Obtém uma amostra de conjuntos de dados de uma categoria.
        
        Args:
            categoria: Nome da categoria.
            limite: Número máximo de resultados.
            
        Returns:
            Lista com amostra de conjuntos de dados.
            
        Raises:
            ValueError: Se a categoria não existir.
        """
        try:
            return self.buscar_conjuntos_por_categoria(categoria, limite)
        except Exception as e:
            logger.error(f"Erro ao obter amostra de dados: {e}")
            return []
