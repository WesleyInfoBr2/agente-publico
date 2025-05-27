"""
Conector para a API do Catálogo Nacional de Dados Públicos (CNDP).

Este módulo implementa um conector para a API do CNDP,
permitindo acesso programático aos dados disponíveis no catálogo.
"""

import requests
import pandas as pd
import time
import json
import os
from typing import Dict, List, Union, Optional, Any
from datetime import datetime


class CNDPAPI:
    """
    Classe para interação com a API do Catálogo Nacional de Dados Públicos (CNDP).
    
    Implementa métodos para acessar os diversos endpoints da API,
    com tratamento de erros, controle de taxa de requisições e
    conversão de dados para formatos adequados para análise.
    """
    
    def __init__(self, token: Optional[str] = None):
        """
        Inicializa o conector para a API do CNDP.
        
        Args:
            token: Token de autenticação (opcional)
        """
        self.base_url = "https://dados.gov.br/api/1"
        self.token = token
        self.headers = {
            "Accept": "application/json",
            "User-Agent": "DadosGovAnalytics/1.0"
        }
        
        if token:
            self.headers["Authorization"] = f"Bearer {token}"
        
        # Configurações para controle de taxa de requisições
        self.rate_limit = 5  # requisições por segundo
        self.last_request_time = 0
    
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
    
    def _fazer_requisicao(self, endpoint: str, params: Dict = None) -> Dict:
        """
        Faz uma requisição à API do CNDP.
        
        Args:
            endpoint: Endpoint da API
            params: Parâmetros da requisição (opcional)
            
        Returns:
            Dicionário com os dados retornados
            
        Raises:
            Exception: Se ocorrer um erro na requisição
        """
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
    
    def listar_temas(self) -> pd.DataFrame:
        """
        Lista os temas disponíveis no CNDP.
        
        Returns:
            DataFrame com os temas disponíveis
        """
        # Fazer requisição
        resultado = self._fazer_requisicao("/action/group_list")
        
        # Verificar se há resultados
        if not resultado or "result" not in resultado:
            return pd.DataFrame()
        
        # Converter para DataFrame
        df = pd.DataFrame(resultado["result"])
        
        return df
    
    def listar_organizacoes(self) -> pd.DataFrame:
        """
        Lista as organizações disponíveis no CNDP.
        
        Returns:
            DataFrame com as organizações disponíveis
        """
        # Fazer requisição
        resultado = self._fazer_requisicao("/action/organization_list")
        
        # Verificar se há resultados
        if not resultado or "result" not in resultado:
            return pd.DataFrame()
        
        # Converter para DataFrame
        df = pd.DataFrame(resultado["result"])
        
        return df
    
    def buscar_conjuntos_dados(self, query: str = "", 
                              tema: str = "", 
                              organizacao: str = "",
                              pagina: int = 1,
                              itens_por_pagina: int = 10) -> pd.DataFrame:
        """
        Busca conjuntos de dados no CNDP.
        
        Args:
            query: Termo de busca (opcional)
            tema: ID do tema (opcional)
            organizacao: ID da organização (opcional)
            pagina: Número da página
            itens_por_pagina: Número de itens por página
            
        Returns:
            DataFrame com os conjuntos de dados encontrados
        """
        # Preparar parâmetros
        params = {
            "q": query,
            "rows": itens_por_pagina,
            "start": (pagina - 1) * itens_por_pagina
        }
        
        if tema:
            params["groups"] = tema
        
        if organizacao:
            params["organization"] = organizacao
        
        # Fazer requisição
        resultado = self._fazer_requisicao("/action/package_search", params)
        
        # Verificar se há resultados
        if not resultado or "result" not in resultado or "results" not in resultado["result"]:
            return pd.DataFrame()
        
        # Extrair resultados
        resultados = resultado["result"]["results"]
        
        # Converter para DataFrame
        if resultados:
            # Normalizar dados para DataFrame
            dados_normalizados = []
            
            for item in resultados:
                dados_item = {
                    "id": item.get("id", ""),
                    "nome": item.get("name", ""),
                    "titulo": item.get("title", ""),
                    "descricao": item.get("notes", ""),
                    "organizacao": item.get("organization", {}).get("name", "") if item.get("organization") else "",
                    "data_criacao": item.get("metadata_created", ""),
                    "data_modificacao": item.get("metadata_modified", ""),
                    "url": item.get("url", ""),
                    "num_recursos": len(item.get("resources", [])),
                    "temas": [g.get("name", "") for g in item.get("groups", [])]
                }
                
                dados_normalizados.append(dados_item)
            
            df = pd.DataFrame(dados_normalizados)
            
            # Adicionar informações de paginação
            df.attrs["total"] = resultado["result"].get("count", 0)
            df.attrs["pagina_atual"] = pagina
            df.attrs["itens_por_pagina"] = itens_por_pagina
            df.attrs["total_paginas"] = (resultado["result"].get("count", 0) + itens_por_pagina - 1) // itens_por_pagina
            
            return df
        else:
            return pd.DataFrame()
    
    def obter_detalhes_conjunto(self, id_conjunto: str) -> Dict:
        """
        Obtém detalhes de um conjunto de dados.
        
        Args:
            id_conjunto: ID do conjunto de dados
            
        Returns:
            Dicionário com os detalhes do conjunto de dados
        """
        # Validar parâmetros
        if not id_conjunto:
            raise ValueError("ID do conjunto de dados é obrigatório")
        
        # Fazer requisição
        resultado = self._fazer_requisicao(f"/action/package_show", {"id": id_conjunto})
        
        # Verificar se há resultados
        if not resultado or "result" not in resultado:
            return {}
        
        return resultado["result"]
    
    def listar_recursos_conjunto(self, id_conjunto: str) -> pd.DataFrame:
        """
        Lista os recursos de um conjunto de dados.
        
        Args:
            id_conjunto: ID do conjunto de dados
            
        Returns:
            DataFrame com os recursos do conjunto de dados
        """
        # Obter detalhes do conjunto
        detalhes = self.obter_detalhes_conjunto(id_conjunto)
        
        # Verificar se há recursos
        if not detalhes or "resources" not in detalhes:
            return pd.DataFrame()
        
        # Extrair recursos
        recursos = detalhes["resources"]
        
        # Converter para DataFrame
        if recursos:
            df = pd.DataFrame(recursos)
            return df
        else:
            return pd.DataFrame()
    
    def baixar_recurso(self, id_recurso: str, caminho_destino: str) -> str:
        """
        Baixa um recurso para o disco.
        
        Args:
            id_recurso: ID do recurso
            caminho_destino: Caminho para salvar o recurso
            
        Returns:
            Caminho completo do arquivo baixado
            
        Raises:
            Exception: Se ocorrer um erro ao baixar o recurso
        """
        # Validar parâmetros
        if not id_recurso:
            raise ValueError("ID do recurso é obrigatório")
        
        # Obter detalhes do recurso
        resultado = self._fazer_requisicao(f"/action/resource_show", {"id": id_recurso})
        
        # Verificar se há resultados
        if not resultado or "result" not in resultado:
            raise Exception(f"Recurso não encontrado: {id_recurso}")
        
        # Extrair URL do recurso
        url = resultado["result"].get("url", "")
        
        if not url:
            raise Exception(f"URL do recurso não encontrada: {id_recurso}")
        
        # Criar diretório de destino se não existir
        os.makedirs(os.path.dirname(os.path.abspath(caminho_destino)), exist_ok=True)
        
        # Baixar recurso
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            with open(caminho_destino, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"Recurso baixado para: {caminho_destino}")
            return caminho_destino
        
        except Exception as e:
            raise Exception(f"Erro ao baixar recurso: {e}")
    
    def carregar_recurso_para_dataframe(self, id_recurso: str, 
                                       formato: Optional[str] = None) -> pd.DataFrame:
        """
        Carrega um recurso diretamente para um DataFrame.
        
        Args:
            id_recurso: ID do recurso
            formato: Formato do recurso ('csv', 'excel', 'json') (opcional, detectado automaticamente)
            
        Returns:
            DataFrame com os dados do recurso
            
        Raises:
            Exception: Se ocorrer um erro ao carregar o recurso
        """
        # Validar parâmetros
        if not id_recurso:
            raise ValueError("ID do recurso é obrigatório")
        
        # Obter detalhes do recurso
        resultado = self._fazer_requisicao(f"/action/resource_show", {"id": id_recurso})
        
        # Verificar se há resultados
        if not resultado or "result" not in resultado:
            raise Exception(f"Recurso não encontrado: {id_recurso}")
        
        # Extrair URL e formato do recurso
        url = resultado["result"].get("url", "")
        formato_detectado = resultado["result"].get("format", "").lower()
        
        if not url:
            raise Exception(f"URL do recurso não encontrada: {id_recurso}")
        
        # Determinar formato
        formato_final = formato or formato_detectado
        
        # Baixar e carregar recurso
        try:
            if formato_final in ['csv', 'text/csv']:
                return pd.read_csv(url)
            elif formato_final in ['xlsx', 'xls', 'excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/vnd.ms-excel']:
                return pd.read_excel(url)
            elif formato_final in ['json', 'application/json']:
                return pd.read_json(url)
            else:
                raise Exception(f"Formato não suportado: {formato_final}")
        
        except Exception as e:
            raise Exception(f"Erro ao carregar recurso: {e}")
    
    def buscar_recursos_por_formato(self, formato: str, 
                                   query: str = "",
                                   pagina: int = 1,
                                   itens_por_pagina: int = 10) -> pd.DataFrame:
        """
        Busca recursos por formato.
        
        Args:
            formato: Formato do recurso ('csv', 'excel', 'json', etc.)
            query: Termo de busca (opcional)
            pagina: Número da página
            itens_por_pagina: Número de itens por página
            
        Returns:
            DataFrame com os recursos encontrados
        """
        # Preparar parâmetros
        params = {
            "query": f"format:{formato}",
            "rows": itens_por_pagina,
            "start": (pagina - 1) * itens_por_pagina
        }
        
        if query:
            params["query"] += f" {query}"
        
        # Fazer requisição
        resultado = self._fazer_requisicao("/action/resource_search", params)
        
        # Verificar se há resultados
        if not resultado or "result" not in resultado or "results" not in resultado["result"]:
            return pd.DataFrame()
        
        # Extrair resultados
        resultados = resultado["result"]["results"]
        
        # Converter para DataFrame
        if resultados:
            df = pd.DataFrame(resultados)
            
            # Adicionar informações de paginação
            df.attrs["total"] = resultado["result"].get("count", 0)
            df.attrs["pagina_atual"] = pagina
            df.attrs["itens_por_pagina"] = itens_por_pagina
            df.attrs["total_paginas"] = (resultado["result"].get("count", 0) + itens_por_pagina - 1) // itens_por_pagina
            
            return df
        else:
            return pd.DataFrame()
    
    def navegar_hierarquia(self) -> Dict:
        """
        Navega pela hierarquia de temas e organizações.
        
        Returns:
            Dicionário com a hierarquia de temas e organizações
        """
        # Obter temas
        temas_df = self.listar_temas()
        
        # Obter organizações
        organizacoes_df = self.listar_organizacoes()
        
        # Construir hierarquia
        hierarquia = {
            "temas": {},
            "organizacoes": {}
        }
        
        # Adicionar temas
        if not temas_df.empty:
            for _, tema in temas_df.iterrows():
                id_tema = tema.get("id", "")
                nome_tema = tema.get("display_name", "")
                
                if id_tema and nome_tema:
                    # Buscar conjuntos de dados do tema
                    conjuntos_df = self.buscar_conjuntos_dados(tema=id_tema, itens_por_pagina=5)
                    
                    hierarquia["temas"][id_tema] = {
                        "nome": nome_tema,
                        "descricao": tema.get("description", ""),
                        "total_conjuntos": conjuntos_df.attrs.get("total", 0) if hasattr(conjuntos_df, "attrs") else 0,
                        "conjuntos_amostra": []
                    }
                    
                    # Adicionar amostra de conjuntos
                    if not conjuntos_df.empty:
                        for _, conjunto in conjuntos_df.iterrows():
                            hierarquia["temas"][id_tema]["conjuntos_amostra"].append({
                                "id": conjunto.get("id", ""),
                                "titulo": conjunto.get("titulo", ""),
                                "organizacao": conjunto.get("organizacao", "")
                            })
        
        # Adicionar organizações
        if not organizacoes_df.empty:
            for _, org in organizacoes_df.iterrows():
                id_org = org.get("id", "")
                nome_org = org.get("display_name", "")
                
                if id_org and nome_org:
                    # Buscar conjuntos de dados da organização
                    conjuntos_df = self.buscar_conjuntos_dados(organizacao=id_org, itens_por_pagina=5)
                    
                    hierarquia["organizacoes"][id_org] = {
                        "nome": nome_org,
                        "descricao": org.get("description", ""),
                        "total_conjuntos": conjuntos_df.attrs.get("total", 0) if hasattr(conjuntos_df, "attrs") else 0,
                        "conjuntos_amostra": []
                    }
                    
                    # Adicionar amostra de conjuntos
                    if not conjuntos_df.empty:
                        for _, conjunto in conjuntos_df.iterrows():
                            hierarquia["organizacoes"][id_org]["conjuntos_amostra"].append({
                                "id": conjunto.get("id", ""),
                                "titulo": conjunto.get("titulo", ""),
                                "temas": conjunto.get("temas", [])
                            })
        
        return hierarquia
    
    def obter_estatisticas_catalogo(self) -> Dict:
        """
        Obtém estatísticas gerais do catálogo.
        
        Returns:
            Dicionário com estatísticas do catálogo
        """
        # Fazer requisição
        resultado = self._fazer_requisicao("/action/site_read")
        
        # Verificar se há resultados
        if not resultado or "result" not in resultado:
            return {}
        
        # Extrair estatísticas
        estatisticas = {
            "total_conjuntos": resultado["result"].get("package_count", 0),
            "total_organizacoes": resultado["result"].get("organization_count", 0),
            "total_temas": resultado["result"].get("group_count", 0),
            "total_usuarios": resultado["result"].get("user_count", 0),
            "titulo_site": resultado["result"].get("site_title", ""),
            "descricao_site": resultado["result"].get("site_description", "")
        }
        
        return estatisticas
    
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
