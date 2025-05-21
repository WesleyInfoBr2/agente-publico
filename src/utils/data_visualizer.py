"""
Módulo para funcionalidades de visualização de dados.

Este módulo fornece funções para criar visualizações atraentes
e informativas a partir de diferentes tipos de dados.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Any, Optional, Union, Tuple
import logging
import io
import base64
from PIL import Image

# Configuração de logging
logger = logging.getLogger(__name__)

class DataVisualizer:
    """
    Classe para criação de visualizações de dados.
    
    Permite gerar diferentes tipos de gráficos e visualizações
    a partir de DataFrames e outros formatos de dados.
    """
    
    def __init__(self, tema: str = "streamlit"):
        """
        Inicializa o objeto DataVisualizer.
        
        Args:
            tema: Tema de visualização a ser utilizado.
        """
        self.tema = tema
        
        # Configurar tema do seaborn
        if tema == "dark":
            sns.set_theme(style="darkgrid")
        else:
            sns.set_theme(style="whitegrid")
    
    def detectar_tipos_colunas(self, df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        """
        Detecta os tipos de dados de cada coluna e sugere visualizações apropriadas.
        
        Args:
            df: DataFrame a ser analisado.
            
        Returns:
            Dicionário com informações sobre cada coluna.
        """
        info_colunas = {}
        
        for coluna in df.columns:
            # Informações básicas
            tipo_pandas = df[coluna].dtype
            n_valores_unicos = df[coluna].nunique()
            n_nulos = df[coluna].isna().sum()
            percentual_nulos = n_nulos / len(df) if len(df) > 0 else 0
            
            # Determinar tipo semântico
            if pd.api.types.is_numeric_dtype(tipo_pandas):
                if n_valores_unicos <= 10:
                    tipo_semantico = "categórico_numérico"
                else:
                    tipo_semantico = "numérico_contínuo"
            elif pd.api.types.is_datetime64_dtype(tipo_pandas):
                tipo_semantico = "data_hora"
            else:  # object, string, etc.
                if n_valores_unicos <= 20:
                    tipo_semantico = "categórico"
                else:
                    tipo_semantico = "texto"
            
            # Sugerir visualizações apropriadas
            visualizacoes_sugeridas = []
            
            if tipo_semantico == "numérico_contínuo":
                visualizacoes_sugeridas = ["histograma", "boxplot", "densidade", "dispersão"]
            elif tipo_semantico in ["categórico", "categórico_numérico"]:
                visualizacoes_sugeridas = ["barras", "pizza", "contagem"]
            elif tipo_semantico == "data_hora":
                visualizacoes_sugeridas = ["linha_temporal", "calendário_heatmap"]
            elif tipo_semantico == "texto":
                visualizacoes_sugeridas = ["nuvem_palavras", "barras_frequencia"]
            
            # Armazenar informações
            info_colunas[coluna] = {
                "tipo_pandas": str(tipo_pandas),
                "tipo_semantico": tipo_semantico,
                "n_valores_unicos": n_valores_unicos,
                "n_nulos": n_nulos,
                "percentual_nulos": percentual_nulos,
                "visualizacoes_sugeridas": visualizacoes_sugeridas
            }
        
        return info_colunas
    
    def sugerir_visualizacoes(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Sugere visualizações apropriadas com base na estrutura do DataFrame.
        
        Args:
            df: DataFrame a ser analisado.
            
        Returns:
            Lista de sugestões de visualizações.
        """
        sugestoes = []
        info_colunas = self.detectar_tipos_colunas(df)
        
        # Identificar colunas por tipo semântico
        colunas_numericas = [col for col, info in info_colunas.items() 
                            if info["tipo_semantico"] == "numérico_contínuo"]
        colunas_categoricas = [col for col, info in info_colunas.items() 
                              if info["tipo_semantico"] in ["categórico", "categórico_numérico"]]
        colunas_temporais = [col for col, info in info_colunas.items() 
                            if info["tipo_semantico"] == "data_hora"]
        
        # Sugestões para colunas numéricas individuais
        for col in colunas_numericas:
            sugestoes.append({
                "tipo": "histograma",
                "colunas": [col],
                "titulo": f"Distribuição de {col}",
                "descricao": f"Histograma mostrando a distribuição de valores de {col}"
            })
            
            sugestoes.append({
                "tipo": "boxplot",
                "colunas": [col],
                "titulo": f"Boxplot de {col}",
                "descricao": f"Boxplot mostrando estatísticas de {col} (mediana, quartis, outliers)"
            })
        
        # Sugestões para colunas categóricas individuais
        for col in colunas_categoricas:
            sugestoes.append({
                "tipo": "barras",
                "colunas": [col],
                "titulo": f"Contagem de {col}",
                "descricao": f"Gráfico de barras mostrando a contagem de cada valor de {col}"
            })
            
            if info_colunas[col]["n_valores_unicos"] <= 10:
                sugestoes.append({
                    "tipo": "pizza",
                    "colunas": [col],
                    "titulo": f"Proporção de {col}",
                    "descricao": f"Gráfico de pizza mostrando a proporção de cada valor de {col}"
                })
        
        # Sugestões para colunas temporais
        for col in colunas_temporais:
            for col_num in colunas_numericas:
                sugestoes.append({
                    "tipo": "linha_temporal",
                    "colunas": [col, col_num],
                    "titulo": f"Evolução de {col_num} ao longo do tempo",
                    "descricao": f"Gráfico de linha mostrando a evolução de {col_num} ao longo de {col}"
                })
        
        # Sugestões para relações entre variáveis numéricas
        if len(colunas_numericas) >= 2:
            for i in range(len(colunas_numericas)):
                for j in range(i+1, len(colunas_numericas)):
                    col1 = colunas_numericas[i]
                    col2 = colunas_numericas[j]
                    
                    sugestoes.append({
                        "tipo": "dispersao",
                        "colunas": [col1, col2],
                        "titulo": f"Relação entre {col1} e {col2}",
                        "descricao": f"Gráfico de dispersão mostrando a relação entre {col1} e {col2}"
                    })
        
        # Sugestões para relações entre variáveis numéricas e categóricas
        if colunas_numericas and colunas_categoricas:
            for col_num in colunas_numericas:
                for col_cat in colunas_categoricas:
                    if info_colunas[col_cat]["n_valores_unicos"] <= 10:
                        sugestoes.append({
                            "tipo": "boxplot_grupo",
                            "colunas": [col_cat, col_num],
                            "titulo": f"{col_num} por {col_cat}",
                            "descricao": f"Boxplot de {col_num} agrupado por {col_cat}"
                        })
                        
                        sugestoes.append({
                            "tipo": "barras_grupo",
                            "colunas": [col_cat, col_num],
                            "titulo": f"Média de {col_num} por {col_cat}",
                            "descricao": f"Gráfico de barras mostrando a média de {col_num} para cada {col_cat}"
                        })
        
        # Limitar número de sugestões
        return sugestoes[:15]  # Retornar no máximo 15 sugestões
    
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
            Objeto de visualização (figura do Plotly ou Matplotlib).
            
        Raises:
            ValueError: Se o tipo de visualização não for suportado ou as colunas não existirem.
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
        
        elif tipo == "boxplot":
            if len(colunas) < 1:
                raise ValueError("Boxplot requer pelo menos uma coluna numérica.")
            
            fig = px.box(
                df, y=colunas[0],
                title=titulo or f"Boxplot de {colunas[0]}",
                points=params.get("points", "outliers"),
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
                title=titulo or f"Proporção de {colunas[0]}",
                hole=params.get("hole", 0.3),
                color_discrete_sequence=params.get("cores", px.colors.qualitative.Plotly)
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
        
        elif tipo == "linha_temporal":
            if len(colunas) < 2:
                raise ValueError("Gráfico de linha temporal requer uma coluna temporal e uma numérica.")
            
            # Agrupar por data se necessário
            if params.get("agrupar", True):
                df_agrupado = df.groupby(colunas[0])[colunas[1]].agg(params.get("agregacao", "mean")).reset_index()
            else:
                df_agrupado = df[[colunas[0], colunas[1]]].copy()
            
            fig = px.line(
                df_agrupado, x=colunas[0], y=colunas[1],
                title=titulo or f"Evolução de {colunas[1]} ao longo do tempo",
                markers=params.get("marcadores", True),
                color_discrete_sequence=params.get("cores", ["#4e8df5"])
            )
            
            return fig
        
        elif tipo == "boxplot_grupo":
            if len(colunas) < 2:
                raise ValueError("Boxplot agrupado requer uma coluna categórica e uma numérica.")
            
            fig = px.box(
                df, x=colunas[0], y=colunas[1],
                title=titulo or f"{colunas[1]} por {colunas[0]}",
                points=params.get("points", "outliers"),
                color=colunas[0],
                color_discrete_sequence=params.get("cores", px.colors.qualitative.Plotly)
            )
            
            return fig
        
        elif tipo == "barras_grupo":
            if len(colunas) < 2:
                raise ValueError("Gráfico de barras agrupado requer uma coluna categórica e uma numérica.")
            
            # Calcular estatística por grupo
            agregacao = params.get("agregacao", "mean")
            df_agrupado = df.groupby(colunas[0])[colunas[1]].agg(agregacao).reset_index()
            
            # Ordenar se solicitado
            if params.get("ordenar", True):
                df_agrupado = df_agrupado.sort_values(colunas[1], ascending=False)
            
            # Limitar número de categorias se necessário
            max_categorias = params.get("max_categorias", 20)
            if len(df_agrupado) > max_categorias:
                df_agrupado = df_agrupado.iloc[:max_categorias]
            
            fig = px.bar(
                df_agrupado, x=colunas[0], y=colunas[1],
                title=titulo or f"{agregacao.capitalize()} de {colunas[1]} por {colunas[0]}",
                color_discrete_sequence=params.get("cores", ["#4e8df5"])
            )
            
            return fig
        
        elif tipo == "heatmap_correlacao":
            # Selecionar apenas colunas numéricas
            df_num = df.select_dtypes(include=['number'])
            
            if df_num
(Content truncated due to size limit. Use line ranges to read in chunks)