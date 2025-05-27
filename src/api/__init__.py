"""
Módulo de conectores para APIs de dados governamentais.

Este pacote contém conectores para diferentes APIs de dados governamentais brasileiros,
incluindo o Portal da Transparência e o Catálogo Nacional de Dados Públicos (CNDP).
"""

from .transparencia import PortalTransparenciaAPI
from .cndp import CNDPAPI

__all__ = ['PortalTransparenciaAPI', 'CNDPAPI']
