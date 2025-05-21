"""
Módulo de conectores para APIs de dados abertos do governo brasileiro.
"""

from .transparencia import TransparenciaAPI
from .dados_gov import DadosGovAPI

__all__ = ['TransparenciaAPI', 'DadosGovAPI']
