"""
Módulo principal do projeto.

Este módulo contém as funções e classes principais do projeto,
incluindo inicialização de APIs e configuração do ambiente.
"""

# Importações padrão
import os
import sys
import pandas as pd
import numpy as np
import json
from typing import Dict, List, Union, Optional, Any, Tuple

# Adicionar diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar módulos do projeto
from src.api import PortalTransparenciaAPI, CNDPAPI
from src.utils import (
    normalizar_texto, identificar_colunas_numericas, identificar_colunas_categoricas,
    identificar_colunas_temporais, converter_colunas_temporais, tratar_valores_ausentes,
    detectar_outliers, normalizar_dados, criar_features_temporais,
    identificar_chaves_comuns, cruzar_dataframes, agrupar_e_sumarizar,
    pivotear_dataframe, configurar_tema, grafico_barras, grafico_barras_interativo,
    grafico_linhas, grafico_linhas_interativo, grafico_pizza,
    grafico_pizza_interativo, grafico_dispersao, grafico_dispersao_interativo,
    grafico_boxplot, grafico_boxplot_interativo, grafico_histograma,
    grafico_histograma_interativo, grafico_correlacao, grafico_correlacao_interativo,
    grafico_mapa_calor, grafico_mapa_calor_interativo, grafico_serie_temporal,
    grafico_serie_temporal_interativo, exportar_grafico, figura_para_base64
)

# Configurações globais
__version__ = "0.1.0"
__author__ = "Dados Gov Analytics Team"
