"""
Conector para a API do Portal da Transparência.

Este módulo implementa um conector para a API do Portal da Transparência do Governo Federal,
permitindo acesso programático aos dados de transparência pública.
"""

import requests
import pandas as pd
import time
import json
import os
from typing import Dict, List, Union, Optional, Any
from datetime import datetime


class PortalTransparenciaAPI:
    """
    Classe para interação com a API do Portal da Transparência.
    
    Implementa métodos para acessar os diversos endpoints da API,
    com tratamento de erros, controle de taxa de requisições e
    conversão de dados para formatos adequados para análise.
    """
    
    def __init__(self, token: Optional[str] = None):
        """
        Inicializa o conector para a API do Portal da Transparência.
        
        Args:
            token: Token de autenticação (opcional)
        """
        self.base_url = "https://api.portaldatransparencia.gov.br/api-de-dados"
        self.token = token
        self.headers = {
            "Accept": "application/json",
            "User-Agent": "DadosGovAnalytics/1.0"
        }
        
        if token:
            self.headers["chave-api-dados"] = token
        
        # Configurações para controle de taxa de requisições
        self.rate_limit = 5  # requisições por segundo
        self.last_request_time = 0
        
        # Mapeamento de endpoints disponíveis
        self.endpoints = {
            "bolsa-familia-disponivel-por-municipio": "/bolsa-familia-disponivel-por-municipio",
            "bolsa-familia-por-municipio": "/bolsa-familia-por-municipio",
            "bolsa-familia-por-cpf-ou-nis": "/bolsa-familia-por-cpf-ou-nis",
            "bolsa-familia-sacado-por-nis": "/bolsa-familia-sacado-por-nis",
            "contratos": "/contratos",
            "contratos-por-orgao": "/contratos-por-orgao",
            "despesas-por-orgao": "/despesas/por-orgao",
            "despesas-por-favorecido": "/despesas/por-favorecido",
            "despesas-por-programa": "/despesas/por-programa",
            "despesas-por-acao": "/despesas/por-acao",
            "despesas-por-funcao": "/despesas/por-funcao",
            "despesas-por-subfuncao": "/despesas/por-subfuncao",
            "emendas": "/emendas",
            "emendas-despesas": "/emendas/despesas",
            "licitacoes": "/licitacoes",
            "orgaos-siafi": "/orgaos-siafi",
            "pep": "/pep",
            "servidores": "/servidores",
            "servidores-remuneracao": "/servidores/remuneracao",
            "viagens": "/viagens",
            "viagens-diarias": "/viagens/diarias",
            "viagens-passagens": "/viagens/passagens",
            "viagens-trechos": "/viagens/trechos"
        }
    
    def _respeitar_limite_taxa(self):
        """
        Respeita o limite de taxa de requisições.
        
        Aguarda o tempo necessário para não exceder o limite de requisições por segundo.
        """
        tempo_atual = time.time()
        tempo_desde_ultima_requisicao = tempo_atual - self.last_request_time
        
        if tempo_desde_ultima_requisicao < 1.0 / self.rate_limit:
            time.sleep((1.0 / self.rate_limit) - tempo_desde_ultima_requisicao)
        
        self.last_request_time = time.time()
    
    def _fazer_requisicao(self, endpoint: str, params: Dict = None) -> List[Dict]:
        """
        Faz uma requisição à API do Portal da Transparência.
        
        Args:
            endpoint: Endpoint da API
            params: Parâmetros da requisição (opcional)
            
        Returns:
            Lista de dicionários com os dados retornados
            
        Raises:
            Exception: Se ocorrer um erro na requisição
        """
        # Verificar se o token está configurado
        if not self.token:
            print("Aviso: Token não configurado. Algumas requisições podem falhar.")
        
        # Respeitar limite de taxa
        self._respeitar_limite_taxa()
        
        # Construir URL
        url = f"{self.base_url}{endpoint}"
        
        try:
            # Fazer requisição
            response = requests.get(url, headers=self.headers, params=params)
            
            # Verificar status
            response.raise_for_status()
            
            # Retornar dados
            return response.json()
        
        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                raise Exception("Erro de autenticação. Verifique o token.")
            elif response.status_code == 403:
                raise Exception("Acesso negado. Verifique as permissões do token.")
            elif response.status_code == 404:
                raise Exception(f"Endpoint não encontrado: {endpoint}")
            elif response.status_code == 429:
                print("Limite de requisições excedido. Aguardando...")
                time.sleep(10)  # Aguardar 10 segundos
                return self._fazer_requisicao(endpoint, params)  # Tentar novamente
            else:
                raise Exception(f"Erro HTTP: {e}")
        
        except requests.exceptions.RequestException as e:
            raise Exception(f"Erro na requisição: {e}")
        
        except json.JSONDecodeError:
            raise Exception("Erro ao decodificar resposta JSON")
    
    def _paginar_resultados(self, endpoint: str, params: Dict, 
                           pagina_inicial: int = 1, 
                           itens_por_pagina: int = 10,
                           max_paginas: Optional[int] = None) -> List[Dict]:
        """
        Pagina os resultados de uma requisição.
        
        Args:
            endpoint: Endpoint da API
            params: Parâmetros da requisição
            pagina_inicial: Número da página inicial
            itens_por_pagina: Número de itens por página
            max_paginas: Número máximo de páginas a buscar (opcional)
            
        Returns:
            Lista de dicionários com todos os dados paginados
        """
        todos_resultados = []
        pagina_atual = pagina_inicial
        
        # Adicionar parâmetros de paginação
        params_paginados = params.copy() if params else {}
        params_paginados["pagina"] = pagina_atual
        params_paginados["tamanhoPagina"] = itens_por_pagina
        
        while True:
            # Atualizar número da página
            params_paginados["pagina"] = pagina_atual
            
            # Fazer requisição
            resultados = self._fazer_requisicao(endpoint, params_paginados)
            
            # Verificar se há resultados
            if not resultados:
                break
            
            # Adicionar resultados
            todos_resultados.extend(resultados)
            
            # Verificar se atingiu o máximo de páginas
            if max_paginas and pagina_atual >= max_paginas:
                break
            
            # Incrementar página
            pagina_atual += 1
            
            # Verificar se há mais páginas
            if len(resultados) < itens_por_pagina:
                break
        
        return todos_resultados
    
    def listar_endpoints_disponiveis(self) -> List[str]:
        """
        Lista os endpoints disponíveis na API.
        
        Returns:
            Lista de nomes de endpoints disponíveis
        """
        return list(self.endpoints.keys())
    
    def consultar_bolsa_familia_por_municipio(self, codigo_ibge: str, 
                                             mes: int, ano: int, 
                                             pagina: int = 1, 
                                             itens_por_pagina: int = 10,
                                             max_paginas: Optional[int] = None) -> pd.DataFrame:
        """
        Consulta dados do Bolsa Família por município.
        
        Args:
            codigo_ibge: Código IBGE do município
            mes: Mês de referência (1-12)
            ano: Ano de referência
            pagina: Número da página inicial
            itens_por_pagina: Número de itens por página
            max_paginas: Número máximo de páginas a buscar (opcional)
            
        Returns:
            DataFrame com os dados do Bolsa Família
        """
        # Validar parâmetros
        if not codigo_ibge:
            raise ValueError("Código IBGE do município é obrigatório")
        
        if not (1 <= mes <= 12):
            raise ValueError("Mês deve estar entre 1 e 12")
        
        if not (2000 <= ano <= datetime.now().year):
            raise ValueError(f"Ano deve estar entre 2000 e {datetime.now().year}")
        
        # Preparar parâmetros
        params = {
            "codigoIbge": codigo_ibge,
            "mesAno": f"{mes:02d}/{ano}"
        }
        
        # Fazer requisição paginada
        resultados = self._paginar_resultados(
            self.endpoints["bolsa-familia-por-municipio"],
            params,
            pagina,
            itens_por_pagina,
            max_paginas
        )
        
        # Converter para DataFrame
        if resultados:
            return pd.DataFrame(resultados)
        else:
            return pd.DataFrame()
    
    def consultar_contratos(self, id_contrato: Optional[str] = None,
                           orgao_superior: Optional[str] = None,
                           orgao_contratante: Optional[str] = None,
                           pagina: int = 1, 
                           itens_por_pagina: int = 10,
                           max_paginas: Optional[int] = None) -> pd.DataFrame:
        """
        Consulta dados de contratos.
        
        Args:
            id_contrato: ID do contrato (opcional)
            orgao_superior: Código do órgão superior (opcional)
            orgao_contratante: Código do órgão contratante (opcional)
            pagina: Número da página inicial
            itens_por_pagina: Número de itens por página
            max_paginas: Número máximo de páginas a buscar (opcional)
            
        Returns:
            DataFrame com os dados de contratos
        """
        # Preparar parâmetros
        params = {}
        
        if id_contrato:
            params["id"] = id_contrato
        
        if orgao_superior:
            params["orgaoSuperior"] = orgao_superior
        
        if orgao_contratante:
            params["orgaoContratante"] = orgao_contratante
        
        # Fazer requisição paginada
        resultados = self._paginar_resultados(
            self.endpoints["contratos"],
            params,
            pagina,
            itens_por_pagina,
            max_paginas
        )
        
        # Converter para DataFrame
        if resultados:
            return pd.DataFrame(resultados)
        else:
            return pd.DataFrame()
    
    def consultar_despesas_por_orgao(self, codigo_orgao: str, 
                                    ano: int,
                                    pagina: int = 1, 
                                    itens_por_pagina: int = 10,
                                    max_paginas: Optional[int] = None) -> pd.DataFrame:
        """
        Consulta despesas por órgão.
        
        Args:
            codigo_orgao: Código do órgão
            ano: Ano de referência
            pagina: Número da página inicial
            itens_por_pagina: Número de itens por página
            max_paginas: Número máximo de páginas a buscar (opcional)
            
        Returns:
            DataFrame com os dados de despesas
        """
        # Validar parâmetros
        if not codigo_orgao:
            raise ValueError("Código do órgão é obrigatório")
        
        if not (2000 <= ano <= datetime.now().year):
            raise ValueError(f"Ano deve estar entre 2000 e {datetime.now().year}")
        
        # Preparar parâmetros
        params = {
            "codigoOrgao": codigo_orgao,
            "ano": ano
        }
        
        # Fazer requisição paginada
        resultados = self._paginar_resultados(
            self.endpoints["despesas-por-orgao"],
            params,
            pagina,
            itens_por_pagina,
            max_paginas
        )
        
        # Converter para DataFrame
        if resultados:
            return pd.DataFrame(resultados)
        else:
            return pd.DataFrame()
    
    def consultar_licitacoes(self, orgao_superior: Optional[str] = None,
                            orgao_subordinado: Optional[str] = None,
                            data_inicio: Optional[str] = None,
                            data_fim: Optional[str] = None,
                            pagina: int = 1, 
                            itens_por_pagina: int = 10,
                            max_paginas: Optional[int] = None) -> pd.DataFrame:
        """
        Consulta dados de licitações.
        
        Args:
            orgao_superior: Código do órgão superior (opcional)
            orgao_subordinado: Código do órgão subordinado (opcional)
            data_inicio: Data de início no formato DD/MM/AAAA (opcional)
            data_fim: Data de fim no formato DD/MM/AAAA (opcional)
            pagina: Número da página inicial
            itens_por_pagina: Número de itens por página
            max_paginas: Número máximo de páginas a buscar (opcional)
            
        Returns:
            DataFrame com os dados de licitações
        """
        # Preparar parâmetros
        params = {}
        
        if orgao_superior:
            params["codigoOrgaoSuperior"] = orgao_superior
        
        if orgao_subordinado:
            params["codigoOrgaoSubordinado"] = orgao_subordinado
        
        if data_inicio:
            params["dataInicial"] = data_inicio
        
        if data_fim:
            params["dataFinal"] = data_fim
        
        # Fazer requisição paginada
        resultados = self._paginar_resultados(
            self.endpoints["licitacoes"],
            params,
            pagina,
            itens_por_pagina,
            max_paginas
        )
        
        # Converter para DataFrame
        if resultados:
            return pd.DataFrame(resultados)
        else:
            return pd.DataFrame()
    
    def consultar_servidores(self, cpf: Optional[str] = None,
                            nome: Optional[str] = None,
                            orgao: Optional[str] = None,
                            pagina: int = 1, 
                            itens_por_pagina: int = 10,
                            max_paginas: Optional[int] = None) -> pd.DataFrame:
        """
        Consulta dados de servidores.
        
        Args:
            cpf: CPF do servidor (opcional)
            nome: Nome do servidor (opcional)
            orgao: Código do órgão (opcional)
            pagina: Número da página inicial
            itens_por_pagina: Número de itens por página
            max_paginas: Número máximo de páginas a buscar (opcional)
            
        Returns:
            DataFrame com os dados de servidores
        """
        # Preparar parâmetros
        params = {}
        
        if cpf:
            params["cpf"] = cpf
        
        if nome:
            params["nome"] = nome
        
        if orgao:
            params["orgao"] = orgao
        
        # Fazer requisição paginada
        resultados = self._paginar_resultados(
            self.endpoints["servidores"],
            params,
            pagina,
            itens_por_pagina,
            max_paginas
        )
        
        # Converter para DataFrame
        if resultados:
            return pd.DataFrame(resultados)
        else:
            return pd.DataFrame()
    
    def consultar_viagens(self, orgao: Optional[str] = None,
                         data_inicio: Optional[str] = None,
                         data_fim: Optional[str] = None,
                         pagina: int = 1, 
                         itens_por_pagina: int = 10,
                         max_paginas: Optional[int] = None) -> pd.DataFrame:
        """
        Consulta dados de viagens.
        
        Args:
            orgao: Código do órgão (opcional)
            data_inicio: Data de início no formato DD/MM/AAAA (opcional)
            data_fim: Data de fim no formato DD/MM/AAAA (opcional)
            pagina: Número da página inicial
            itens_por_pagina: Número de itens por página
            max_paginas: Número máximo de páginas a buscar (opcional)
            
        Returns:
            DataFrame com os dados de viagens
        """
        # Preparar parâmetros
        params = {}
        
        if orgao:
            params["codigoOrgao"] = orgao
        
        if data_inicio:
            params["dataIdaProgramadaInicio"] = data_inicio
        
        if data_fim:
            params["dataIdaProgramadaFim"] = data_fim
        
        # Fazer requisição paginada
        resultados = self._paginar_resultados(
            self.endpoints["viagens"],
            params,
            pagina,
            itens_por_pagina,
            max_paginas
        )
        
        # Converter para DataFrame
        if resultados:
            return pd.DataFrame(resultados)
        else:
            return pd.DataFrame()
    
    def consultar_orgaos_siafi(self) -> pd.DataFrame:
        """
        Consulta lista de órgãos SIAFI.
        
        Returns:
            DataFrame com os dados de órgãos SIAFI
        """
        # Fazer requisição
        resultados = self._fazer_requisicao(self.endpoints["orgaos-siafi"])
        
        # Converter para DataFrame
        if resultados:
            return pd.DataFrame(resultados)
        else:
            return pd.DataFrame()
    
    def consultar_endpoint_generico(self, nome_endpoint: str, 
                                   params: Dict = None,
                                   paginar: bool = True,
                                   pagina: int = 1, 
                                   itens_por_pagina: int = 10,
                                   max_paginas: Optional[int] = None) -> pd.DataFrame:
        """
        Consulta um endpoint genérico da API.
        
        Args:
            nome_endpoint: Nome do endpoint (deve estar em listar_endpoints_disponiveis())
            params: Parâmetros da requisição (opcional)
            paginar: Se True, pagina os resultados
            pagina: Número da página inicial
            itens_por_pagina: Número de itens por página
            max_paginas: Número máximo de páginas a buscar (opcional)
            
        Returns:
            DataFrame com os dados retornados
            
        Raises:
            ValueError: Se o endpoint não for reconhecido
        """
        # Verificar se o endpoint existe
        if nome_endpoint not in self.endpoints:
            raise ValueError(f"Endpoint '{nome_endpoint}' não reconhecido. " +
                           f"Use um dos seguintes: {', '.join(self.endpoints.keys())}")
        
        # Obter caminho do endpoint
        endpoint = self.endpoints[nome_endpoint]
        
        # Fazer requisição
        if paginar:
            resultados = self._paginar_resultados(
                endpoint,
                params,
                pagina,
                itens_por_pagina,
                max_paginas
            )
        else:
            resultados = self._fazer_requisicao(endpoint, params)
        
        # Converter para DataFrame
        if resultados:
            return pd.DataFrame(resultados)
        else:
            return pd.DataFrame()
    
    def salvar_dados(self, df: pd.DataFrame, caminho: str, 
                    formato: str = 'csv', index: bool = False) -> str:
        """
        Salva os dados em um arquivo.
        
        Args:
            df: DataFrame com os dados
            caminho: Caminho para o arquivo (sem extensão)
            formato: Formato do arquivo ('csv', 'excel', 'json', 'pickle')
            index: Se True, inclui o índice
            
        Returns:
            Caminho completo do arquivo salvo
            
        Raises:
            ValueError: Se o formato não for suportado
        """
        # Verificar se o DataFrame está vazio
        if df.empty:
            print("Aviso: DataFrame vazio, nenhum arquivo será salvo.")
            return ""
        
        # Criar diretório se não existir
        os.makedirs(os.path.dirname(os.path.abspath(caminho)), exist_ok=True)
        
        # Salvar no formato especificado
        if formato == 'csv':
            caminho_completo = f"{caminho}.csv"
            df.to_csv(caminho_completo, index=index)
        elif formato == 'excel':
            caminho_completo = f"{caminho}.xlsx"
            df.to_excel(caminho_completo, index=index)
        elif formato == 'json':
            caminho_completo = f"{caminho}.json"
            df.to_json(caminho_completo, orient='records')
        elif formato == 'pickle':
            caminho_completo = f"{caminho}.pkl"
            df.to_pickle(caminho_completo)
        else:
            raise ValueError(f"Formato '{formato}' não suportado. Use 'csv', 'excel', 'json' ou 'pickle'.")
        
        print(f"Dados salvos em: {caminho_completo}")
        return caminho_completo
