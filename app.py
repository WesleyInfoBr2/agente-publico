"""
Versão completa da aplicação Dados Abertos Gov para deploy no Streamlit Cloud.
Este arquivo contém todas as funcionalidades em um único arquivo, incluindo cruzamento de dados.
"""

import streamlit as st
import pandas as pd
import numpy as np
import requests
import json
import time
import logging
import os
from typing import Dict, List, Any, Optional, Union, Tuple
from urllib.parse import urljoin
import plotly.express as px
import plotly.graph_objects as go
import io
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Dados Abertos Gov - Análise Facilitada",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Estilo CSS personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .info-box {
        background-color: #f0f2f6;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    .source-badge {
        background-color: #4e8df5;
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 0.3rem;
        font-size: 0.8rem;
        margin-right: 0.5rem;
    }
    .category-badge {
        background-color: #f5814e;
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 0.3rem;
        font-size: 0.8rem;
        margin-right: 0.5rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 4px 4px 0 0;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #4e8df5;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Classes simplificadas para API do Portal da Transparência
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

# Classes simplificadas para API do dados.gov.br
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

# Classe para cruzamento de dados
class DataCrosser:
    """
    Classe para cruzamento de dados entre diferentes fontes.
    """
    
    def __init__(self):
        """Inicializa o objeto DataCrosser."""
        pass
    
    def identificar_colunas_comuns(self, df1: pd.DataFrame, df2: pd.DataFrame) -> List[str]:
        """
        Identifica colunas com nomes idênticos entre dois DataFrames.
        
        Args:
            df1: Primeiro DataFrame.
            df2: Segundo DataFrame.
            
        Returns:
            Lista de nomes de colunas comuns.
        """
        return list(set(df1.columns).intersection(set(df2.columns)))
    
    def sugerir_colunas_para_cruzamento(self, df1: pd.DataFrame, df2: pd.DataFrame) -> List[Tuple[str, str]]:
        """
        Sugere pares de colunas que podem ser usadas para cruzamento.
        
        Args:
            df1: Primeiro DataFrame.
            df2: Segundo DataFrame.
            
        Returns:
            Lista de tuplas (coluna_df1, coluna_df2) sugeridas para cruzamento.
        """
        sugestoes = []
        
        # Primeiro, verificar colunas com nomes idênticos
        colunas_comuns = self.identificar_colunas_comuns(df1, df2)
        for col in colunas_comuns:
            sugestoes.append((col, col))
        
        # Depois, procurar por colunas com nomes similares
        # Isso é uma simplificação, idealmente usaria algoritmos mais sofisticados
        palavras_chave = {
            "id": ["id", "codigo", "code", "identificador"],
            "nome": ["nome", "name", "razao_social", "razao social"],
            "data": ["data", "date", "dt", "periodo"],
            "valor": ["valor", "value", "montante", "amount"],
            "municipio": ["municipio", "cidade", "city", "local"],
            "estado": ["estado", "uf", "state", "provincia"],
            "cpf": ["cpf", "cnpj", "documento", "document"],
        }
        
        for categoria, termos in palavras_chave.items():
            colunas_df1 = [col for col in df1.columns if any(termo in col.lower() for termo in termos)]
            colunas_df2 = [col for col in df2.columns if any(termo in col.lower() for termo in termos)]
            
            for col1 in colunas_df1:
                for col2 in colunas_df2:
                    if (col1, col2) not in sugestoes and col1 != col2:
                        sugestoes.append((col1, col2))
        
        return sugestoes
    
    def cruzar_dados(self, df1: pd.DataFrame, df2: pd.DataFrame, 
                    coluna_df1: str, coluna_df2: str, 
                    metodo: str = "inner", sufixos: Tuple[str, str] = ("_1", "_2")) -> pd.DataFrame:
        """
        Cruza dois DataFrames com base em colunas específicas.
        
        Args:
            df1: Primeiro DataFrame.
            df2: Segundo DataFrame.
            coluna_df1: Coluna do primeiro DataFrame para cruzamento.
            coluna_df2: Coluna do segundo DataFrame para cruzamento.
            metodo: Método de junção ('inner', 'left', 'right', 'outer').
            sufixos: Sufixos para colunas com nomes duplicados.
            
        Returns:
            DataFrame resultante do cruzamento.
            
        Raises:
            ValueError: Se as colunas especificadas não existirem ou o método for inválido.
        """
        # Verificar se as colunas existem
        if coluna_df1 not in df1.columns:
            raise ValueError(f"Coluna '{coluna_df1}' não encontrada no primeiro DataFrame.")
        
        if coluna_df2 not in df2.columns:
            raise ValueError(f"Coluna '{coluna_df2}' não encontrada no segundo DataFrame.")
        
        # Verificar o método
        metodos_validos = ["inner", "left", "right", "outer"]
        if metodo not in metodos_validos:
            raise ValueError(f"Método '{metodo}' inválido. Métodos válidos: {', '.join(metodos_validos)}")
        
        # Realizar o cruzamento
        if metodo == "inner":
            resultado = pd.merge(df1, df2, left_on=coluna_df1, right_on=coluna_df2, how="inner", suffixes=sufixos)
        elif metodo == "left":
            resultado = pd.merge(df1, df2, left_on=coluna_df1, right_on=coluna_df2, how="left", suffixes=sufixos)
        elif metodo == "right":
            resultado = pd.merge(df1, df2, left_on=coluna_df1, right_on=coluna_df2, how="right", suffixes=sufixos)
        else:  # outer
            resultado = pd.merge(df1, df2, left_on=coluna_df1, right_on=coluna_df2, how="outer", suffixes=sufixos)
        
        return resultado
    
    def avaliar_qualidade_cruzamento(self, df1: pd.DataFrame, df2: pd.DataFrame, 
                                   df_resultado: pd.DataFrame) -> Dict[str, Any]:
        """
        Avalia a qualidade do cruzamento realizado.
        
        Args:
            df1: Primeiro DataFrame original.
            df2: Segundo DataFrame original.
            df_resultado: DataFrame resultante do cruzamento.
            
        Returns:
            Dicionário com métricas de qualidade do cruzamento.
        """
        # Calcular métricas básicas
        linhas_df1 = len(df1)
        linhas_df2 = len(df2)
        linhas_resultado = len(df_resultado)
        
        # Calcular taxas de correspondência
        taxa_df1 = (linhas_resultado / linhas_df1) * 100 if linhas_df1 > 0 else 0
        taxa_df2 = (linhas_resultado / linhas_df2) * 100 if linhas_df2 > 0 else 0
        
        # Calcular outras métricas
        colunas_df1 = len(df1.columns)
        colunas_df2 = len(df2.columns)
        colunas_resultado = len(df_resultado.columns)
        
        # Retornar métricas
        return {
            "linhas_df1": linhas_df1,
            "linhas_df2": linhas_df2,
            "linhas_resultado": linhas_resultado,
            "taxa_correspondencia_df1": taxa_df1,
            "taxa_correspondencia_df2": taxa_df2,
            "colunas_df1": colunas_df1,
            "colunas_df2": colunas_df2,
            "colunas_resultado": colunas_resultado
        }

# Classe simplificada para visualização de dados
class DataVisualizer:
    """
    Classe para criação de visualizações de dados.
    """
    
    def __init__(self, tema: str = "streamlit"):
        """
        Inicializa o objeto DataVisualizer.
        
        Args:
            tema: Tema de visualização a ser utilizado.
        """
        self.tema = tema
    
    def criar_visualizacao(self, df: pd.DataFrame, tipo: str, 
                          colunas: List[str], titulo: Optional[str] = None,
                          parametros: Optional[Dict[str, Any]] = None) -> Any:
        """
        Cria uma visualização específica a partir de um DataFrame.
        
        Args:
            df: DataFrame com os dados.
            tipo: Tipo de visualização a ser criada.
            colunas: Lista de colunas a serem utilizadas.
            titulo: Título da visualização (opcional).
            parametros: Parâmetros adicionais para a visualização (opcional).
            
        Returns:
            Objeto de visualização (figura do Plotly).
        """
        # Verificar se as colunas existem
        for col in colunas:
            if col not in df.columns:
                raise ValueError(f"Coluna '{col}' não encontrada no DataFrame.")
        
        # Parâmetros padrão
        params = parametros or {}
        
        # Criar visualização de acordo com o tipo
        if tipo == "histograma":
            if len(colunas) < 1:
                raise ValueError("Histograma requer pelo menos uma coluna numérica.")
            
            fig = px.histogram(
                df, x=colunas[0],
                title=titulo or f"Distribuição de {colunas[0]}",
                nbins=params.get("nbins", 30),
                opacity=params.get("opacity", 0.7),
                color_discrete_sequence=params.get("cores", ["#4e8df5"])
            )
            
            return fig
        
        elif tipo == "barras":
            if len(colunas) < 1:
                raise ValueError("Gráfico de barras requer pelo menos uma coluna categórica.")
            
            # Calcular contagem
            contagem = df[colunas[0]].value_counts().reset_index()
            contagem.columns = [colunas[0], 'contagem']
            
            # Ordenar se solicitado
            if params.get("ordenar", True):
                contagem = contagem.sort_values("contagem", ascending=False)
            
            # Limitar número de categorias se necessário
            max_categorias = params.get("max_categorias", 20)
            if len(contagem) > max_categorias:
                outros = pd.DataFrame({
                    colunas[0]: ["Outros"],
                    "contagem": [contagem.iloc[max_categorias:]["contagem"].sum()]
                })
                contagem = pd.concat([contagem.iloc[:max_categorias], outros])
            
            fig = px.bar(
                contagem, x=colunas[0], y="contagem",
                title=titulo or f"Contagem de {colunas[0]}",
                color_discrete_sequence=params.get("cores", ["#4e8df5"])
            )
            
            return fig
        
        elif tipo == "dispersao":
            if len(colunas) < 2:
                raise ValueError("Gráfico de dispersão requer pelo menos duas colunas numéricas.")
            
            fig = px.scatter(
                df, x=colunas[0], y=colunas[1],
                title=titulo or f"Relação entre {colunas[0]} e {colunas[1]}",
                opacity=params.get("opacity", 0.7),
                color=params.get("cor_por", None),
                size=params.get("tamanho_por", None),
                trendline=params.get("linha_tendencia", None),
                color_discrete_sequence=params.get("cores", ["#4e8df5"])
            )
            
            return fig
        
        elif tipo == "linha":
            if len(colunas) < 2:
                raise ValueError("Gráfico de linha requer pelo menos duas colunas (x e y).")
            
            fig = px.line(
                df, x=colunas[0], y=colunas[1],
                title=titulo or f"Série temporal de {colunas[1]} por {colunas[0]}",
                markers=params.get("marcadores", True),
                color=params.get("cor_por", None),
                color_discrete_sequence=params.get("cores", ["#4e8df5"])
            )
            
            return fig
        
        elif tipo == "pizza":
            if len(colunas) < 1:
                raise ValueError("Gráfico de pizza requer pelo menos uma coluna categórica.")
            
            # Calcular contagem
            contagem = df[colunas[0]].value_counts().reset_index()
            contagem.columns = [colunas[0], 'contagem']
            
            # Limitar número de categorias se necessário
            max_categorias = params.get("max_categorias", 10)
            if len(contagem) > max_categorias:
                outros = pd.DataFrame({
                    colunas[0]: ["Outros"],
                    "contagem": [contagem.iloc[max_categorias:]["contagem"].sum()]
                })
                contagem = pd.concat([contagem.iloc[:max_categorias], outros])
            
            fig = px.pie(
                contagem, names=colunas[0], values="contagem",
                title=titulo or f"Distribuição de {colunas[0]}",
                color_discrete_sequence=params.get("cores", px.colors.qualitative.Plotly)
            )
            
            return fig
        
        elif tipo == "boxplot":
            if len(colunas) < 1:
                raise ValueError("Boxplot requer pelo menos uma coluna numérica.")
            
            fig = px.box(
                df, y=colunas[0],
                title=titulo or f"Boxplot de {colunas[0]}",
                color=params.get("cor_por", None),
                color_discrete_sequence=params.get("cores", ["#4e8df5"])
            )
            
            return fig
        
        else:
            raise ValueError(f"Tipo de visualização '{tipo}' não suportado.")

# Inicialização das APIs
@st.cache_resource
def inicializar_apis():
    """Inicializa e retorna instâncias das APIs."""
    transparencia_api = TransparenciaAPI()
    dados_gov_api = DadosGovAPI()
    return transparencia_api, dados_gov_api

# Função para carregar dados da sessão
def carregar_dataframes_sessao():
    """Carrega DataFrames armazenados na sessão."""
    if "dataframes" not in st.session_state:
        st.session_state.dataframes = {}
    
    return st.session_state.dataframes

# Função para adicionar DataFrame à sessão
def adicionar_dataframe_sessao(nome, df, metadados=None):
    """Adiciona um DataFrame à sessão."""
    if "dataframes" not in st.session_state:
        st.session_state.dataframes = {}
    
    st.session_state.dataframes[nome] = {
        "data": df,
        "metadados": metadados or {},
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

# Função para página de cruzamento de dados
def pagina_cruzamento_dados():
    """Página para cruzamento de dados entre diferentes fontes."""
    
    # Cabeçalho
    st.markdown('<div class="main-header">🔄 Cruzamento de Dados</div>', unsafe_allow_html=True)
    
    st.markdown("""
    Esta página permite cruzar dados de diferentes fontes, identificando relações e padrões entre conjuntos de dados.
    """)
    
    # Carregar DataFrames disponíveis
    dataframes = carregar_dataframes_sessao()
    
    if not dataframes:
        st.warning("Nenhum conjunto de dados disponível para cruzamento. Por favor, carregue dados na página principal.")
        return
    
    # Seleção de DataFrames para cruzamento
    st.markdown('<div class="sub-header">Selecione os Conjuntos de Dados</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Primeiro Conjunto")
        df1_nome = st.selectbox(
            "Selecione o primeiro conjunto de dados:",
            list(dataframes.keys()),
            key="df1_select"
        )
        
        if df1_nome:
            df1 = dataframes[df1_nome]["data"]
            st.markdown(f"**Dimensões:** {df1.shape[0]} linhas × {df1.shape[1]} colunas")
            st.markdown(f"**Origem:** {dataframes[df1_nome]['metadados'].get('origem', 'Desconhecida')}")
            st.markdown(f"**Categoria:** {dataframes[df1_nome]['metadados'].get('categoria', 'Desconhecida')}")
            
            # Exibir amostra
            with st.expander("Visualizar amostra"):
                st.dataframe(df1.head())
    
    with col2:
        st.markdown("### Segundo Conjunto")
        df2_options = [nome for nome in dataframes.keys() if nome != df1_nome]
        
        if df2_options:
            df2_nome = st.selectbox(
                "Selecione o segundo conjunto de dados:",
                df2_options,
                key="df2_select"
            )
            
            if df2_nome:
                df2 = dataframes[df2_nome]["data"]
                st.markdown(f"**Dimensões:** {df2.shape[0]} linhas × {df2.shape[1]} colunas")
                st.markdown(f"**Origem:** {dataframes[df2_nome]['metadados'].get('origem', 'Desconhecida')}")
                st.markdown(f"**Categoria:** {dataframes[df2_nome]['metadados'].get('categoria', 'Desconhecida')}")
                
                # Exibir amostra
                with st.expander("Visualizar amostra"):
                    st.dataframe(df2.head())
        else:
            st.warning("Carregue pelo menos dois conjuntos de dados para realizar o cruzamento.")
            return
    
    # Configuração do cruzamento
    st.markdown('<div class="sub-header">Configuração do Cruzamento</div>', unsafe_allow_html=True)
    
    # Inicializar objeto de cruzamento
    data_crosser = DataCrosser()
    
    # Sugerir colunas para cruzamento
    sugestoes = data_crosser.sugerir_colunas_para_cruzamento(df1, df2)
    
    if sugestoes:
        st.markdown("### Colunas Sugeridas para Cruzamento")
        
        # Exibir sugestões em formato de tabela
        sugestoes_df = pd.DataFrame(sugestoes, columns=["Coluna em " + df1_nome, "Coluna em " + df2_nome])
        st.dataframe(sugestoes_df)
    
    # Seleção manual de colunas
    st.markdown("### Seleção de Colunas para Cruzamento")
    
    col1, col2 = st.columns(2)
    
    with col1:
        coluna_df1 = st.selectbox(
            f"Coluna de {df1_nome}:",
            df1.columns.tolist(),
            key="coluna_df1"
        )
    
    with col2:
        coluna_df2 = st.selectbox(
            f"Coluna de {df2_nome}:",
            df2.columns.tolist(),
            key="coluna_df2"
        )
    
    # Método de cruzamento
    metodo = st.selectbox(
        "Método de cruzamento:",
        ["inner", "left", "right", "outer"],
        format_func=lambda x: {
            "inner": "Inner Join (apenas correspondências)",
            "left": "Left Join (mantém todas as linhas do primeiro conjunto)",
            "right": "Right Join (mantém todas as linhas do segundo conjunto)",
            "outer": "Outer Join (mantém todas as linhas de ambos os conjuntos)"
        }.get(x, x),
        key="metodo_cruzamento"
    )
    
    # Sufixos para colunas duplicadas
    col1, col2 = st.columns(2)
    
    with col1:
        sufixo1 = st.text_input("Sufixo para colunas do primeiro conjunto:", f"_{df1_nome}", key="sufixo1")
    
    with col2:
        sufixo2 = st.text_input("Sufixo para colunas do segundo conjunto:", f"_{df2_nome}", key="sufixo2")
    
    # Botão para realizar o cruzamento
    if st.button("Realizar Cruzamento", type="primary"):
        with st.spinner("Cruzando dados..."):
            try:
                # Realizar o cruzamento
                resultado = data_crosser.cruzar_dados(
                    df1, df2,
                    coluna_df1, coluna_df2,
                    metodo=metodo,
                    sufixos=(sufixo1, sufixo2)
                )
                
                # Avaliar qualidade do cruzamento
                metricas = data_crosser.avaliar_qualidade_cruzamento(df1, df2, resultado)
                
                # Exibir resultados
                st.markdown('<div class="sub-header">Resultados do Cruzamento</div>', unsafe_allow_html=True)
                
                # Métricas
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Linhas no resultado", metricas["linhas_resultado"])
                
                with col2:
                    st.metric(
                        f"Taxa de correspondência ({df1_nome})", 
                        f"{metricas['taxa_correspondencia_df1']:.1f}%"
                    )
                
                with col3:
                    st.metric(
                        f"Taxa de correspondência ({df2_nome})", 
                        f"{metricas['taxa_correspondencia_df2']:.1f}%"
                    )
                
                # Exibir DataFrame resultante
                st.markdown("### Dados Cruzados")
                st.dataframe(resultado)
                
                # Adicionar à sessão
                nome_resultado = f"Cruzamento_{df1_nome}_{df2_nome}"
                adicionar_dataframe_sessao(
                    nome_resultado,
                    resultado,
                    {
                        "tipo": "cruzamento",
                        "fonte1": df1_nome,
                        "fonte2": df2_nome,
                        "metodo": metodo,
                        "coluna1": coluna_df1,
                        "coluna2": coluna_df2
                    }
                )
                
                # Opção para download
                st.download_button(
                    "Baixar resultado (CSV)",
                    data=resultado.to_csv(index=False).encode('utf-8'),
                    file_name=f"cruzamento_{df1_nome}_{df2_nome}.csv",
                    mime="text/csv"
                )
                
                # Visualizações básicas
                if len(resultado) > 0:
                    st.markdown("### Visualizações")
                    
                    # Selecionar colunas para visualização
                    colunas_numericas = resultado.select_dtypes(include=['number']).columns.tolist()
                    colunas_categoricas = resultado.select_dtypes(exclude=['number']).columns.tolist()
                    
                    if colunas_numericas and colunas_categoricas:
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            col_num = st.selectbox("Selecione uma coluna numérica:", colunas_numericas, key="viz_num")
                            col_cat = st.selectbox("Selecione uma coluna categórica:", colunas_categoricas, key="viz_cat")
                            
                            # Criar visualização
                            visualizador = DataVisualizer()
                            
                            try:
                                fig = visualizador.criar_visualizacao(
                                    resultado, 
                                    tipo="barras",
                                    colunas=[col_cat],
                                    titulo=f"Contagem de {col_cat}"
                                )
                                
                                st.plotly_chart(fig, use_container_width=True)
                            except Exception as e:
                                st.error(f"Erro ao criar visualização: {str(e)}")
                        
                        with col2:
                            try:
                                fig = visualizador.criar_visualizacao(
                                    resultado, 
                                    tipo="boxplot",
                                    colunas=[col_num],
                                    titulo=f"Distribuição de {col_num}",
                                    parametros={"cor_por": col_cat}
                                )
                                
                                st.plotly_chart(fig, use_container_width=True)
                            except Exception as e:
                                st.error(f"Erro ao criar visualização: {str(e)}")
            
            except Exception as e:
                st.error(f"Erro ao realizar cruzamento: {str(e)}")

# Função principal
def main():
    """Função principal da aplicação."""
    
    # Inicialização das APIs
    transparencia_api, dados_gov_api = inicializar_apis()
    
    # Configuração da barra lateral
    with st.sidebar:
        st.markdown('<div class="sub-header">Navegação</div>', unsafe_allow_html=True)
        
        # Seleção de página
        pagina = st.radio(
            "Selecione a página:",
            ["Explorar Dados", "Cruzamento de Dados"],
            index=0
        )
        
        st.markdown("---")
        
        # Seleção de Origem (apenas para Explorar Dados)
        if pagina == "Explorar Dados":
            st.markdown('<div class="sub-header">Filtros</div>', unsafe_allow_html=True)
            
            # Seleção de Origem
            origem = st.selectbox(
                "Selecione a Origem dos Dados:",
                ["Portal da Transparência", "dados.gov.br"]
            )
            
            # Seleção de Categoria baseada na Origem
            if origem == "Portal da Transparência":
                categorias = transparencia_api.get_categorias()
                categoria = st.selectbox("Selecione a Categoria:", categorias)
                
                # Seleção de Base baseada na Categoria
                bases = transparencia_api.get_bases_por_categoria(categoria)
                base = st.selectbox("Selecione a Base de Dados:", list(bases.keys()))
                
            else:  # dados.gov.br
                categorias = dados_gov_api.get_categorias()
                categoria = st.selectbox("Selecione a Categoria:", categorias)
                
                # Para dados.gov.br, precisamos buscar conjuntos de dados baseados na categoria
                with st.spinner("Buscando conjuntos de dados..."):
                    conjuntos = dados_gov_api.buscar_conjuntos_por_categoria(categoria, limite=20)
                    
                    if conjuntos:
                        opcoes_conjuntos = {conjunto["title"]: conjunto["id"] for conjunto in conjuntos}
                        base = st.selectbox("Selecione o Conjunto de Dados:", list(opcoes_conjuntos.keys()))
                        id_conjunto = opcoes_conjuntos[base]
                    else:
                        st.warning("Nenhum conjunto de dados encontrado para esta categoria.")
                        base = None
                        id_conjunto = None
            
            # Botão para carregar dados
            carregar_dados = st.button("Carregar Dados", type="primary")
        
        # Informações adicionais
        st.markdown("---")
        st.markdown('<div class="sub-header">Sobre</div>', unsafe_allow_html=True)
        st.markdown("""
        Esta aplicação permite explorar e analisar dados abertos do governo brasileiro 
        de forma facilitada, com recursos de visualização e análise estatística.
        """)
        
        st.markdown("---")
        st.markdown("Desenvolvido com ❤️ usando Python e Streamlit")
    
    # Conteúdo principal
    if pagina == "Explorar Dados":
        # Cabeçalho
        st.markdown('<div class="main-header">📊 Dados Abertos Gov - Análise Facilitada</div>', unsafe_allow_html=True)
        
        if "carregar_dados" in locals() and carregar_dados:
            if origem == "Portal da Transparência" and base:
                st.markdown(f'<div class="sub-header">Dados de {base} <span class="source-badge">{origem}</span> <span class="category-badge">{categoria}</span></div>', unsafe_allow_html=True)
                
                # Exibir parâmetros necessários
                parametros = transparencia_api.listar_parametros_necessarios(categoria, base)
                
                if parametros:
                    st.markdown('<div class="info-box">Esta base requer parâmetros adicionais para consulta.</div>', unsafe_allow_html=True)
                    
                    # Criar formulário para os parâmetros
                    with st.form("parametros_form"):
                        valores_parametros = {}
                        
                        for param in parametros:
                            if param["tipo"] == "string":
                                valores_parametros[param["nome"]] = st.text_input(
                                    f"{param['nome']} ({param['descricao']})",
                                    value=param.get("padrao", "")
                                )
                            elif param["tipo"] == "integer":
                                valores_parametros[param["nome"]] = st.number_input(
                                    f"{param['nome']} ({param['descricao']})",
                                    value=param.get("padrao", 1),
                                    step=1
                                )
                        
                        # Botão de submissão
                        submitted = st.form_submit_button("Consultar")
                        
                        if submitted:
                            with st.spinner("Consultando dados..."):
                                try:
                                    dados = transparencia_api.consultar_dados(categoria, base, valores_parametros)
                                    
                                    if dados:
                                        st.success(f"Dados carregados com sucesso! ({len(dados)} registros)")
                                        
                                        # Converter para DataFrame
                                        df = pd.DataFrame(dados)
                                        st.dataframe(df)
                                        
                                        # Adicionar à sessão
                                        nome_df = f"{base} - {categoria}"
                                        adicionar_dataframe_sessao(
                                            nome_df, 
                                            df,
                                            {
                                                "origem": origem,
                                                "categoria": categoria,
                                                "base": base
                                            }
                                        )
                                        
                                        # Opção para download
                                        st.download_button(
                                            "Baixar dados (CSV)",
                                            data=df.to_csv(index=False).encode('utf-8'),
                                            file_name=f"{base.lower().replace(' ', '_')}.csv",
                                            mime="text/csv"
                                        )
                                        
                                        # Visualizações básicas
                                        if len(df) > 0:
                                            st.markdown("### Visualizações Básicas")
                                            
                                            # Selecionar colunas para visualização
                                            colunas_numericas = df.select_dtypes(include=['number']).columns.tolist()
                                            colunas_categoricas = df.select_dtypes(exclude=['number']).columns.tolist()
                                            
                                            if colunas_numericas:
                                                col1, col2 = st.columns(2)
                                                
                                                with col1:
                                                    col_num = st.selectbox("Selecione uma coluna numérica:", colunas_numericas)
                                                    
                                                    # Criar visualização
                                                    visualizador = DataVisualizer()
                                                    fig = visualizador.criar_visualizacao(
                                                        df, 
                                                        tipo="histograma",
                                                        colunas=[col_num],
                                                        titulo=f"Distribuição de {col_num}"
                                                    )
                                                    
                                                    st.plotly_chart(fig, use_container_width=True)
                                                
                                                with col2:
                                                    if colunas_categoricas:
                                                        col_cat = st.selectbox("Selecione uma coluna categórica:", colunas_categoricas)
                                                        
                                                        # Criar visualização
                                                        fig = visualizador.criar_visualizacao(
                                                            df, 
                                                            tipo="barras",
                                                            colunas=[col_cat],
                                                            titulo=f"Contagem de {col_cat}"
                                                        )
                                                        
                                                        st.plotly_chart(fig, use_container_width=True)
                                    else:
                                        st.warning("Nenhum dado encontrado para os parâmetros fornecidos.")
                                except Exception as e:
                                    st.error(f"Erro ao consultar dados: {str(e)}")
                else:
                    # Tentar obter uma amostra de dados
                    with st.spinner("Carregando amostra de dados..."):
                        try:
                            dados = transparencia_api.obter_amostra_dados(categoria, base)
                            
                            if dados:
                                st.success(f"Amostra de dados carregada com sucesso! ({len(dados)} registros)")
                                
                                # Converter para DataFrame
                                df = pd.DataFrame(dados)
                                st.dataframe(df)
                                
                                # Adicionar à sessão
                                nome_df = f"{base} - {categoria}"
                                adicionar_dataframe_sessao(
                                    nome_df, 
                                    df,
                                    {
                                        "origem": origem,
                                        "categoria": categoria,
                                        "base": base
                                    }
                                )
                                
                                # Opção para download
                                st.download_button(
                                    "Baixar dados (CSV)",
                                    data=df.to_csv(index=False).encode('utf-8'),
                                    file_name=f"{base.lower().replace(' ', '_')}.csv",
                                    mime="text/csv"
                                )
                            else:
                                st.warning("Não foi possível obter uma amostra de dados para esta base.")
                        except Exception as e:
                            st.error(f"Erro ao carregar amostra: {str(e)}")
            
            elif origem == "dados.gov.br" and base and "id_conjunto" in locals() and id_conjunto:
                st.markdown(f'<div class="sub-header">Conjunto de Dados: {base} <span class="source-badge">{origem}</span> <span class="category-badge">{categoria}</span></div>', unsafe_allow_html=True)
                
                # Obter detalhes do conjunto
                with st.spinner("Carregando detalhes do conjunto..."):
                    try:
                        detalhes = dados_gov_api.obter_detalhes_conjunto(id_conjunto)
                        
                        if detalhes:
                            # Exibir informações básicas
                            st.markdown(f"**Descrição:** {detalhes.get('notes', 'Sem descrição')}")
                            st.markdown(f"**Organização:** {detalhes.get('organization', {}).get('title', 'Desconhecida')}")
                            st.markdown(f"**Última atualização:** {detalhes.get('metadata_modified', 'Desconhecida')}")
                            
                            # Listar recursos disponíveis
                            recursos = detalhes.get("resources", [])
                            
                            if recursos:
                                st.markdown('<div class="sub-header">Recursos Disponíveis</div>', unsafe_allow_html=True)
                                
                                for i, recurso in enumerate(recursos):
                                    with st.expander(f"{recurso.get('name', f'Recurso {i+1}')} ({recurso.get('format', 'Formato desconhecido')})"):
                                        st.markdown(f"**Descrição:** {recurso.get('description', 'Sem descrição')}")
                                        st.markdown(f"**Formato:** {recurso.get('format', 'Desconhecido')}")
                                        st.markdown(f"**Última atualização:** {recurso.get('last_modified', 'Desconhecida')}")
                                        
                                        # Opções para visualizar ou baixar
                                        col1, col2 = st.columns(2)
                                        
                                        with col1:
                                            if st.button("Visualizar Dados", key=f"view_{i}"):
                                                with st.spinner("Carregando dados..."):
                                                    try:
                                                        # Verificar formato para tratamento adequado
                                                        formato = recurso.get('format', '').lower()
                                                        url = recurso.get('url')
                                                        
                                                        if url:
                                                            if formato in ['csv', 'json']:
                                                                # Para formatos estruturados, tentar carregar como DataFrame
                                                                if formato == 'csv':
                                                                    df = pd.read_csv(url)
                                                                else:  # json
                                                                    df = pd.read_json(url)
                                                                
                                                                st.dataframe(df)
                                                                
                                                                # Adicionar à sessão
                                                                nome_df = f"{recurso.get('name', 'Recurso')} - {base}"
                                                                adicionar_dataframe_sessao(
                                                                    nome_df, 
                                                                    df,
                                                                    {
                                                                        "origem": origem,
                                                                        "categoria": categoria,
                                                                        "conjunto": base,
                                                                        "recurso": recurso.get('name')
                                                                    }
                                                                )
                                                                
                                                                # Opção para download
                                                                st.download_button(
                                                                    "Baixar dados (CSV)",
                                                                    data=df.to_csv(index=False).encode('utf-8'),
                                                                    file_name=f"{recurso.get('name', 'dados').lower().replace(' ', '_')}.csv",
                                                                    mime="text/csv"
                                                                )
                                                            else:
                                                                st.warning(f"Visualização direta não suportada para o formato {formato}.")
                                                                st.markdown(f"[Abrir URL do recurso]({url})")
                                                        else:
                                                            st.error("URL do recurso não disponível.")
                                                    except Exception as e:
                                                        st.error(f"Erro ao carregar dados: {str(e)}")
                                        
                                        with col2:
                                            if recurso.get('url'):
                                                st.markdown(f"[Download Direto]({recurso.get('url')})")
                            else:
                                st.warning("Nenhum recurso disponível para este conjunto de dados.")
                        else:
                            st.error("Não foi possível obter detalhes do conjunto de dados.")
                    except Exception as e:
                        st.error(f"Erro ao carregar detalhes: {str(e)}")
            
            else:
                st.info("Selecione uma origem, categoria e base de dados, e clique em 'Carregar Dados'.")
        else:
            # Tela inicial quando nenhum dado foi carregado
            st.markdown('<div class="info-box">', unsafe_allow_html=True)
            st.markdown("""
            ## Bem-vindo à Análise Facilitada de Dados Abertos Governamentais!
            
            Esta aplicação permite explorar e analisar dados abertos do governo brasileiro de forma simples e intuitiva.
            
            ### Como usar:
            
            1. Selecione a **Origem** dos dados no menu lateral (Portal da Transparência ou dados.gov.br)
            2. Escolha uma **Categoria** de dados
            3. Selecione uma **Base de Dados** específica
            4. Clique em **Carregar Dados** para visualizar e analisar
            
            ### Recursos disponíveis:
            
            - Visualização de dados em tabelas interativas
            - Análises estatísticas descritivas
            - Visualizações básicas
            - Cruzamento de diferentes fontes de dados
            - Exportação de resultados
            """)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Exibir algumas estatísticas gerais
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown('<div class="sub-header">Portal da Transparência</div>', unsafe_allow_html=True)
                transparencia_api, _ = inicializar_apis()
                categorias = transparencia_api.get_categorias()
                
                total_bases = sum(len(transparencia_api.get_bases_por_categoria(cat)) for cat in categorias)
                
                st.metric("Categorias disponíveis", len(categorias))
                st.metric("Bases de dados", total_bases)
            
            with col2:
                st.markdown('<div class="sub-header">dados.gov.br</div>', unsafe_allow_html=True)
                _, dados_gov_api = inicializar_apis()
                categorias = dados_gov_api.get_categorias()
                
                # Aqui seria ideal ter o número total de conjuntos, mas isso exigiria muitas requisições
                # Então usamos um valor aproximado
                st.metric("Categorias disponíveis", len(categorias))
                st.metric("Conjuntos de dados (aprox.)", "14.000+")
            
            # Exibir DataFrames já carregados
            dataframes = carregar_dataframes_sessao()
            
            if dataframes:
                st.markdown('<div class="sub-header">Conjuntos de Dados Carregados</div>', unsafe_allow_html=True)
                
                for nome, info in dataframes.items():
                    with st.expander(f"{nome} ({info['data'].shape[0]} linhas × {info['data'].shape[1]} colunas)"):
                        st.markdown(f"**Origem:** {info['metadados'].get('origem', 'Desconhecida')}")
                        st.markdown(f"**Categoria:** {info['metadados'].get('categoria', 'Desconhecida')}")
                        st.markdown(f"**Carregado em:** {info.get('timestamp', 'Desconhecido')}")
                        
                        # Exibir amostra
                        st.dataframe(info['data'].head())
                        
                        # Opção para download
                        st.download_button(
                            "Baixar dados (CSV)",
                            data=info['data'].to_csv(index=False).encode('utf-8'),
                            file_name=f"{nome.lower().replace(' ', '_')}.csv",
                            mime="text/csv"
                        )
    
    elif pagina == "Cruzamento de Dados":
        # Chamar a função da página de cruzamento
        pagina_cruzamento_dados()

# Executar a aplicação
if __name__ == "__main__":
    main()
