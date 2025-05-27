"""
Módulo para processamento de dados governamentais.

Este módulo contém funções para limpeza, transformação e enriquecimento
de dados obtidos das APIs do Portal da Transparência e CNDP.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Union, Optional, Any
import re
import unicodedata


def normalizar_texto(texto: str) -> str:
    """
    Normaliza texto removendo acentos, convertendo para minúsculas e removendo caracteres especiais.
    
    Args:
        texto: Texto a ser normalizado
        
    Returns:
        Texto normalizado
    """
    # Remover acentos
    texto_sem_acentos = ''.join(c for c in unicodedata.normalize('NFD', texto)
                              if unicodedata.category(c) != 'Mn')
    
    # Converter para minúsculas
    texto_minusculo = texto_sem_acentos.lower()
    
    # Remover caracteres especiais
    texto_normalizado = re.sub(r'[^a-z0-9\s]', '', texto_minusculo)
    
    # Substituir múltiplos espaços por um único espaço
    texto_normalizado = re.sub(r'\s+', ' ', texto_normalizado).strip()
    
    return texto_normalizado


def identificar_colunas_numericas(df: pd.DataFrame) -> List[str]:
    """
    Identifica colunas numéricas em um DataFrame.
    
    Args:
        df: DataFrame a ser analisado
        
    Returns:
        Lista de nomes de colunas numéricas
    """
    return df.select_dtypes(include=['number']).columns.tolist()


def identificar_colunas_categoricas(df: pd.DataFrame) -> List[str]:
    """
    Identifica colunas categóricas em um DataFrame.
    
    Args:
        df: DataFrame a ser analisado
        
    Returns:
        Lista de nomes de colunas categóricas
    """
    return df.select_dtypes(include=['object', 'category']).columns.tolist()


def identificar_colunas_temporais(df: pd.DataFrame) -> List[str]:
    """
    Identifica colunas temporais em um DataFrame.
    
    Args:
        df: DataFrame a ser analisado
        
    Returns:
        Lista de nomes de colunas temporais
    """
    colunas_temporais = []
    
    for coluna in df.columns:
        # Verificar se o nome da coluna sugere data/tempo
        if any(termo in coluna.lower() for termo in ['data', 'date', 'dt', 'ano', 'mes', 'dia', 'hora', 'time']):
            colunas_temporais.append(coluna)
        # Tentar converter para datetime
        elif df[coluna].dtype == 'object':
            try:
                pd.to_datetime(df[coluna], errors='raise')
                colunas_temporais.append(coluna)
            except:
                pass
    
    return colunas_temporais


def converter_colunas_temporais(df: pd.DataFrame, colunas: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Converte colunas temporais para o tipo datetime.
    
    Args:
        df: DataFrame a ser processado
        colunas: Lista de colunas a converter (opcional, se None, tenta identificar automaticamente)
        
    Returns:
        DataFrame com colunas convertidas
    """
    df_processado = df.copy()
    
    if colunas is None:
        colunas = identificar_colunas_temporais(df)
    
    for coluna in colunas:
        if coluna in df.columns:
            try:
                df_processado[coluna] = pd.to_datetime(df[coluna], errors='coerce')
            except:
                print(f"Não foi possível converter a coluna {coluna} para datetime.")
    
    return df_processado


def tratar_valores_ausentes(df: pd.DataFrame, estrategia: str = 'drop') -> pd.DataFrame:
    """
    Trata valores ausentes em um DataFrame.
    
    Args:
        df: DataFrame a ser processado
        estrategia: Estratégia de tratamento ('drop', 'mean', 'median', 'mode', 'zero')
        
    Returns:
        DataFrame com valores ausentes tratados
    """
    df_processado = df.copy()
    
    if estrategia == 'drop':
        # Remover linhas com valores ausentes
        df_processado = df_processado.dropna()
    
    else:
        # Identificar colunas numéricas e categóricas
        colunas_numericas = identificar_colunas_numericas(df)
        colunas_categoricas = identificar_colunas_categoricas(df)
        
        # Tratar colunas numéricas
        for coluna in colunas_numericas:
            if df_processado[coluna].isna().any():
                if estrategia == 'mean':
                    df_processado[coluna] = df_processado[coluna].fillna(df_processado[coluna].mean())
                elif estrategia == 'median':
                    df_processado[coluna] = df_processado[coluna].fillna(df_processado[coluna].median())
                elif estrategia == 'zero':
                    df_processado[coluna] = df_processado[coluna].fillna(0)
        
        # Tratar colunas categóricas
        for coluna in colunas_categoricas:
            if df_processado[coluna].isna().any():
                if estrategia == 'mode':
                    df_processado[coluna] = df_processado[coluna].fillna(df_processado[coluna].mode()[0])
                else:
                    df_processado[coluna] = df_processado[coluna].fillna('Desconhecido')
    
    return df_processado


def detectar_outliers(df: pd.DataFrame, coluna: str, metodo: str = 'iqr', limite: float = 1.5) -> pd.Series:
    """
    Detecta outliers em uma coluna numérica.
    
    Args:
        df: DataFrame a ser analisado
        coluna: Nome da coluna a analisar
        metodo: Método de detecção ('iqr' ou 'zscore')
        limite: Limite para considerar outlier (1.5 para IQR, 3 para z-score)
        
    Returns:
        Série booleana indicando outliers (True) e não-outliers (False)
    """
    if metodo == 'iqr':
        Q1 = df[coluna].quantile(0.25)
        Q3 = df[coluna].quantile(0.75)
        IQR = Q3 - Q1
        
        limite_inferior = Q1 - limite * IQR
        limite_superior = Q3 + limite * IQR
        
        outliers = (df[coluna] < limite_inferior) | (df[coluna] > limite_superior)
    
    elif metodo == 'zscore':
        from scipy import stats
        z_scores = stats.zscore(df[coluna])
        outliers = abs(z_scores) > limite
    
    else:
        raise ValueError(f"Método '{metodo}' não suportado. Use 'iqr' ou 'zscore'.")
    
    return outliers


def normalizar_dados(df: pd.DataFrame, colunas: Optional[List[str]] = None, metodo: str = 'minmax') -> pd.DataFrame:
    """
    Normaliza colunas numéricas de um DataFrame.
    
    Args:
        df: DataFrame a ser processado
        colunas: Lista de colunas a normalizar (opcional, se None, usa todas as numéricas)
        metodo: Método de normalização ('minmax', 'zscore')
        
    Returns:
        DataFrame com colunas normalizadas
    """
    df_processado = df.copy()
    
    if colunas is None:
        colunas = identificar_colunas_numericas(df)
    
    for coluna in colunas:
        if coluna in df.columns:
            if metodo == 'minmax':
                min_val = df[coluna].min()
                max_val = df[coluna].max()
                
                if max_val > min_val:
                    df_processado[f"{coluna}_norm"] = (df[coluna] - min_val) / (max_val - min_val)
                else:
                    df_processado[f"{coluna}_norm"] = 0
            
            elif metodo == 'zscore':
                mean = df[coluna].mean()
                std = df[coluna].std()
                
                if std > 0:
                    df_processado[f"{coluna}_norm"] = (df[coluna] - mean) / std
                else:
                    df_processado[f"{coluna}_norm"] = 0
            
            else:
                raise ValueError(f"Método '{metodo}' não suportado. Use 'minmax' ou 'zscore'.")
    
    return df_processado


def criar_features_temporais(df: pd.DataFrame, coluna_data: str) -> pd.DataFrame:
    """
    Cria features temporais a partir de uma coluna de data.
    
    Args:
        df: DataFrame a ser processado
        coluna_data: Nome da coluna de data
        
    Returns:
        DataFrame com features temporais adicionadas
    """
    df_processado = df.copy()
    
    # Garantir que a coluna é do tipo datetime
    df_processado = converter_colunas_temporais(df_processado, [coluna_data])
    
    # Criar features
    df_processado[f'{coluna_data}_ano'] = df_processado[coluna_data].dt.year
    df_processado[f'{coluna_data}_mes'] = df_processado[coluna_data].dt.month
    df_processado[f'{coluna_data}_dia'] = df_processado[coluna_data].dt.day
    df_processado[f'{coluna_data}_dia_semana'] = df_processado[coluna_data].dt.dayofweek
    df_processado[f'{coluna_data}_trimestre'] = df_processado[coluna_data].dt.quarter
    df_processado[f'{coluna_data}_semestre'] = ((df_processado[coluna_data].dt.month - 1) // 6) + 1
    
    return df_processado


def identificar_chaves_comuns(df1: pd.DataFrame, df2: pd.DataFrame) -> List[str]:
    """
    Identifica possíveis chaves comuns entre dois DataFrames.
    
    Args:
        df1: Primeiro DataFrame
        df2: Segundo DataFrame
        
    Returns:
        Lista de possíveis chaves comuns
    """
    chaves_comuns = []
    
    # Verificar colunas com mesmo nome
    colunas_comuns = set(df1.columns).intersection(set(df2.columns))
    
    for coluna in colunas_comuns:
        # Verificar se a coluna tem valores únicos em pelo menos um dos DataFrames
        if df1[coluna].nunique() / len(df1) > 0.5 or df2[coluna].nunique() / len(df2) > 0.5:
            chaves_comuns.append(coluna)
    
    return chaves_comuns


def cruzar_dataframes(df1: pd.DataFrame, df2: pd.DataFrame, chave: str, tipo_join: str = 'inner') -> pd.DataFrame:
    """
    Cruza dois DataFrames usando uma chave comum.
    
    Args:
        df1: Primeiro DataFrame
        df2: Segundo DataFrame
        chave: Nome da coluna chave
        tipo_join: Tipo de join ('inner', 'left', 'right', 'outer')
        
    Returns:
        DataFrame resultante do cruzamento
    """
    # Verificar se a chave existe em ambos os DataFrames
    if chave not in df1.columns or chave not in df2.columns:
        raise ValueError(f"A chave '{chave}' não existe em ambos os DataFrames.")
    
    # Adicionar sufixos para evitar conflitos de nomes de colunas
    df_cruzado = df1.merge(df2, on=chave, how=tipo_join, suffixes=('_df1', '_df2'))
    
    return df_cruzado


def agrupar_e_sumarizar(df: pd.DataFrame, colunas_grupo: Union[str, List[str]], 
                       colunas_valor: Union[str, List[str]], 
                       agregacoes: Union[str, List[str]] = 'mean') -> pd.DataFrame:
    """
    Agrupa e sumariza um DataFrame.
    
    Args:
        df: DataFrame a ser processado
        colunas_grupo: Coluna(s) para agrupar
        colunas_valor: Coluna(s) para agregar
        agregacoes: Função(ões) de agregação ('mean', 'sum', 'count', 'min', 'max', etc.)
        
    Returns:
        DataFrame agrupado e sumarizado
    """
    # Converter para listas se necessário
    if isinstance(colunas_grupo, str):
        colunas_grupo = [colunas_grupo]
    
    if isinstance(colunas_valor, str):
        colunas_valor = [colunas_valor]
    
    if isinstance(agregacoes, str):
        agregacoes = [agregacoes]
    
    # Criar dicionário de agregações
    agg_dict = {}
    for coluna in colunas_valor:
        agg_dict[coluna] = agregacoes
    
    # Agrupar e agregar
    df_agrupado = df.groupby(colunas_grupo).agg(agg_dict).reset_index()
    
    return df_agrupado


def pivotear_dataframe(df: pd.DataFrame, indice: str, colunas: str, valores: str, 
                      agregacao: str = 'mean') -> pd.DataFrame:
    """
    Cria uma tabela pivot a partir de um DataFrame.
    
    Args:
        df: DataFrame a ser processado
        indice: Coluna para usar como índice
        colunas: Coluna para usar como colunas
        valores: Coluna para usar como valores
        agregacao: Função de agregação
        
    Returns:
        DataFrame pivoteado
    """
    df_pivot = df.pivot_table(index=indice, columns=colunas, values=valores, aggfunc=agregacao)
    
    return df_pivot
