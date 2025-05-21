"""
Módulo para funcionalidades de cruzamento de dados entre diferentes fontes.

Este módulo fornece funções para cruzar dados de diferentes fontes,
identificar chaves comuns e realizar operações de junção.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union, Tuple
import logging

# Configuração de logging
logger = logging.getLogger(__name__)

class DataCrosser:
    """
    Classe para cruzamento de dados entre diferentes fontes.
    
    Permite identificar chaves comuns, realizar operações de junção
    e preparar dados para análise conjunta.
    """
    
    def __init__(self):
        """Inicializa o objeto DataCrosser."""
        pass
    
    def identificar_chaves_potenciais(self, df1: pd.DataFrame, df2: pd.DataFrame) -> List[Tuple[str, str, float]]:
        """
        Identifica potenciais chaves para cruzamento entre dois DataFrames.
        
        Args:
            df1: Primeiro DataFrame.
            df2: Segundo DataFrame.
            
        Returns:
            Lista de tuplas (coluna_df1, coluna_df2, score_similaridade).
        """
        chaves_potenciais = []
        
        # Verificar nomes de colunas idênticos
        colunas_comuns = set(df1.columns).intersection(set(df2.columns))
        
        # Para cada coluna comum, verificar se pode ser uma chave
        for coluna in colunas_comuns:
            # Verificar cardinalidade
            unique_ratio_df1 = df1[coluna].nunique() / len(df1)
            unique_ratio_df2 = df2[coluna].nunique() / len(df2)
            
            # Colunas com alta cardinalidade são boas candidatas a chaves
            if unique_ratio_df1 > 0.5 and unique_ratio_df2 > 0.5:
                # Verificar sobreposição de valores
                valores_df1 = set(df1[coluna].dropna().unique())
                valores_df2 = set(df2[coluna].dropna().unique())
                
                if valores_df1 and valores_df2:  # Evitar conjuntos vazios
                    sobreposicao = len(valores_df1.intersection(valores_df2))
                    score = sobreposicao / max(len(valores_df1), len(valores_df2))
                    
                    chaves_potenciais.append((coluna, coluna, score))
        
        # Verificar colunas com nomes diferentes mas conteúdo similar
        # (simplificado - em uma implementação real, usaríamos técnicas mais avançadas)
        for col1 in df1.columns:
            for col2 in df2.columns:
                # Pular colunas já verificadas
                if col1 == col2:
                    continue
                
                # Verificar se ambas são do mesmo tipo
                if df1[col1].dtype.kind == df2[col2].dtype.kind:
                    # Para colunas numéricas, verificar distribuição
                    if df1[col1].dtype.kind in 'iuf':  # inteiro, unsigned int, float
                        continue  # Simplificado - pular análise numérica
                    
                    # Para colunas de texto, verificar padrões comuns (CPF, CNPJ, códigos)
                    elif df1[col1].dtype.kind in 'OSU':  # Object, String, Unicode
                        # Verificar se parecem códigos (alta cardinalidade)
                        unique_ratio_df1 = df1[col1].nunique() / len(df1)
                        unique_ratio_df2 = df2[col2].nunique() / len(df2)
                        
                        if unique_ratio_df1 > 0.5 and unique_ratio_df2 > 0.5:
                            # Verificar sobreposição de valores
                            valores_df1 = set(df1[col1].dropna().astype(str).unique())
                            valores_df2 = set(df2[col2].dropna().astype(str).unique())
                            
                            if valores_df1 and valores_df2:  # Evitar conjuntos vazios
                                sobreposicao = len(valores_df1.intersection(valores_df2))
                                score = sobreposicao / max(len(valores_df1), len(valores_df2))
                                
                                if score > 0.1:  # Limiar mínimo de sobreposição
                                    chaves_potenciais.append((col1, col2, score))
        
        # Ordenar por score de similaridade
        return sorted(chaves_potenciais, key=lambda x: x[2], reverse=True)
    
    def cruzar_dataframes(self, df1: pd.DataFrame, df2: pd.DataFrame, 
                         chave_df1: str, chave_df2: str, 
                         metodo: str = 'inner') -> pd.DataFrame:
        """
        Cruza dois DataFrames usando as chaves especificadas.
        
        Args:
            df1: Primeiro DataFrame.
            df2: Segundo DataFrame.
            chave_df1: Coluna a ser usada como chave no primeiro DataFrame.
            chave_df2: Coluna a ser usada como chave no segundo DataFrame.
            metodo: Método de junção ('inner', 'left', 'right', 'outer').
            
        Returns:
            DataFrame resultante do cruzamento.
            
        Raises:
            ValueError: Se as chaves não existirem nos DataFrames.
        """
        # Verificar se as chaves existem
        if chave_df1 not in df1.columns:
            raise ValueError(f"Chave '{chave_df1}' não encontrada no primeiro DataFrame.")
        
        if chave_df2 not in df2.columns:
            raise ValueError(f"Chave '{chave_df2}' não encontrada no segundo DataFrame.")
        
        # Preparar DataFrames para junção
        df1_copy = df1.copy()
        df2_copy = df2.copy()
        
        # Adicionar prefixos para evitar conflitos de nomes de colunas
        df1_copy = df1_copy.add_prefix('df1_')
        df2_copy = df2_copy.add_prefix('df2_')
        
        # Renomear colunas de chave para facilitar a junção
        df1_copy = df1_copy.rename(columns={f'df1_{chave_df1}': 'chave_juncao'})
        df2_copy = df2_copy.rename(columns={f'df2_{chave_df2}': 'chave_juncao'})
        
        # Realizar a junção
        df_resultado = pd.merge(
            df1_copy, df2_copy, 
            on='chave_juncao', 
            how=metodo
        )
        
        return df_resultado
    
    def sugerir_cruzamentos(self, dfs: Dict[str, pd.DataFrame]) -> List[Dict[str, Any]]:
        """
        Sugere possíveis cruzamentos entre múltiplos DataFrames.
        
        Args:
            dfs: Dicionário de DataFrames {nome: dataframe}.
            
        Returns:
            Lista de sugestões de cruzamento.
        """
        sugestoes = []
        
        # Comparar todos os pares de DataFrames
        nomes = list(dfs.keys())
        
        for i in range(len(nomes)):
            for j in range(i+1, len(nomes)):
                nome1 = nomes[i]
                nome2 = nomes[j]
                df1 = dfs[nome1]
                df2 = dfs[nome2]
                
                # Identificar chaves potenciais
                chaves = self.identificar_chaves_potenciais(df1, df2)
                
                # Adicionar sugestões se houver chaves com score razoável
                for chave_df1, chave_df2, score in chaves:
                    if score > 0.2:  # Limiar mínimo para sugestão
                        sugestoes.append({
                            'df1': nome1,
                            'df2': nome2,
                            'chave_df1': chave_df1,
                            'chave_df2': chave_df2,
                            'score': score,
                            'descricao': f"Cruzar '{nome1}' e '{nome2}' usando '{chave_df1}' e '{chave_df2}' (score: {score:.2f})"
                        })
        
        # Ordenar por score
        return sorted(sugestoes, key=lambda x: x['score'], reverse=True)
    
    def avaliar_qualidade_cruzamento(self, df_resultado: pd.DataFrame, 
                                   df1_original: pd.DataFrame, 
                                   df2_original: pd.DataFrame) -> Dict[str, Any]:
        """
        Avalia a qualidade de um cruzamento realizado.
        
        Args:
            df_resultado: DataFrame resultante do cruzamento.
            df1_original: Primeiro DataFrame original.
            df2_original: Segundo DataFrame original.
            
        Returns:
            Dicionário com métricas de qualidade do cruzamento.
        """
        # Calcular métricas básicas
        n_linhas_df1 = len(df1_original)
        n_linhas_df2 = len(df2_original)
        n_linhas_resultado = len(df_resultado)
        
        # Calcular taxas de correspondência
        taxa_df1 = n_linhas_resultado / n_linhas_df1 if n_linhas_df1 > 0 else 0
        taxa_df2 = n_linhas_resultado / n_linhas_df2 if n_linhas_df2 > 0 else 0
        
        # Calcular completude (porcentagem de valores não nulos)
        completude = 1 - (df_resultado.isna().sum().sum() / (df_resultado.shape[0] * df_resultado.shape[1]))
        
        return {
            'n_linhas_df1': n_linhas_df1,
            'n_linhas_df2': n_linhas_df2,
            'n_linhas_resultado': n_linhas_resultado,
            'taxa_correspondencia_df1': taxa_df1,
            'taxa_correspondencia_df2': taxa_df2,
            'completude': completude,
            'qualidade_geral': (taxa_df1 + taxa_df2 + completude) / 3  # Média simples das métricas
        }
