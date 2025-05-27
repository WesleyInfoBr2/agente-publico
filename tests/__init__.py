# Inicialização do Projeto

Este arquivo contém os testes iniciais para garantir que o ambiente está configurado corretamente.

```python
import unittest

def test_imports():
    """Testa se as importações básicas funcionam."""
    try:
        import pandas as pd
        import numpy as np
        import matplotlib.pyplot as plt
        import seaborn as sns
        import plotly.express as px
        import requests
        print("✓ Todas as bibliotecas básicas foram importadas com sucesso.")
        return True
    except ImportError as e:
        print(f"✗ Erro ao importar bibliotecas: {e}")
        return False

def test_project_structure():
    """Testa se a estrutura do projeto está correta."""
    import os
    
    # Verificar diretórios principais
    directories = ['src', 'src/api', 'src/utils', 'tests', 'notebooks']
    missing = []
    
    for directory in directories:
        if not os.path.exists(directory):
            missing.append(directory)
    
    if missing:
        print(f"✗ Diretórios ausentes: {', '.join(missing)}")
        return False
    else:
        print("✓ Todos os diretórios principais estão presentes.")
        return True

def test_api_modules():
    """Testa se os módulos de API podem ser importados."""
    try:
        from src.api import PortalTransparenciaAPI, CNDPAPI
        print("✓ Módulos de API importados com sucesso.")
        return True
    except ImportError as e:
        print(f"✗ Erro ao importar módulos de API: {e}")
        return False

def test_utils_modules():
    """Testa se os módulos utilitários podem ser importados."""
    try:
        from src.utils import (
            normalizar_texto, identificar_colunas_numericas,
            grafico_barras, grafico_linhas_interativo
        )
        print("✓ Módulos utilitários importados com sucesso.")
        return True
    except ImportError as e:
        print(f"✗ Erro ao importar módulos utilitários: {e}")
        return False

def run_all_tests():
    """Executa todos os testes de inicialização."""
    print("=== Testes de Inicialização ===")
    
    results = [
        ("Importações básicas", test_imports()),
        ("Estrutura do projeto", test_project_structure()),
        ("Módulos de API", test_api_modules()),
        ("Módulos utilitários", test_utils_modules())
    ]
    
    print("\n=== Resumo dos Testes ===")
    all_passed = True
    
    for name, result in results:
        status = "PASSOU" if result else "FALHOU"
        print(f"{name}: {status}")
        all_passed = all_passed and result
    
    if all_passed:
        print("\n✓ Todos os testes passaram! O ambiente está configurado corretamente.")
    else:
        print("\n✗ Alguns testes falharam. Verifique os erros acima.")
    
    return all_passed

if __name__ == "__main__":
    run_all_tests()
```

## Próximos Passos

Após verificar que o ambiente está configurado corretamente, você pode começar a explorar os notebooks:

1. **00_Introducao.ipynb**: Visão geral do projeto
2. **01_Configuracao_e_Autenticacao.ipynb**: Configuração de APIs e autenticação
3. **02_Portal_Transparencia_Exploracao.ipynb**: Exploração de dados do Portal da Transparência
4. **03_CNDP_Exploracao.ipynb**: Exploração de dados do CNDP
5. **04_Analise_Estatistica_Basica.ipynb**: Análises estatísticas básicas

Para executar os testes unitários, use:

```bash
python -m unittest discover tests
```
