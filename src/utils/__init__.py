"""
Módulo de utilidades para o projeto.

Este pacote contém funções e classes utilitárias para processamento de dados,
visualização e outras funcionalidades comuns.
"""

from .data_processing import *
from .visualization import *

__all__ = [
    # Data Processing
    'normalizar_texto', 'identificar_colunas_numericas', 'identificar_colunas_categoricas',
    'identificar_colunas_temporais', 'converter_colunas_temporais', 'tratar_valores_ausentes',
    'detectar_outliers', 'normalizar_dados', 'criar_features_temporais',
    'identificar_chaves_comuns', 'cruzar_dataframes', 'agrupar_e_sumarizar',
    'pivotear_dataframe',
    
    # Visualization
    'configurar_tema', 'grafico_barras', 'grafico_barras_interativo',
    'grafico_linhas', 'grafico_linhas_interativo', 'grafico_pizza',
    'grafico_pizza_interativo', 'grafico_dispersao', 'grafico_dispersao_interativo',
    'grafico_boxplot', 'grafico_boxplot_interativo', 'grafico_histograma',
    'grafico_histograma_interativo', 'grafico_correlacao', 'grafico_correlacao_interativo',
    'grafico_mapa_calor', 'grafico_mapa_calor_interativo', 'grafico_serie_temporal',
    'grafico_serie_temporal_interativo', 'exportar_grafico', 'figura_para_base64'
]
