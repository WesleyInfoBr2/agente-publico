import streamlit as st
import pandas as pd
import numpy as np
import os

# Configuração da página
st.set_page_config(
    page_title="Dados Abertos Gov - Requisitos",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo CSS personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 2rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .info-box {
        background-color: #f0f2f6;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Cabeçalho
st.markdown('<div class="main-header">📋 Requisitos da Aplicação</div>', unsafe_allow_html=True)

# Visão geral
st.markdown("""
Esta página documenta os requisitos e especificações da aplicação Dados Abertos Gov, 
servindo como referência para desenvolvedores e usuários.
""")

# Requisitos funcionais
st.markdown('<div class="sub-header">Requisitos Funcionais</div>', unsafe_allow_html=True)

requisitos_funcionais = [
    {
        "id": "RF01",
        "titulo": "Navegação Hierárquica de Dados",
        "descricao": "A aplicação deve permitir navegação hierárquica por Origem (Portal da Transparência, dados.gov.br), Fonte (agrupamento por área) e Base (conjuntos específicos).",
        "prioridade": "Alta"
    },
    {
        "id": "RF02",
        "titulo": "Carregamento Sob Demanda",
        "descricao": "Os dados devem ser carregados apenas quando solicitados pelo usuário, sem armazenamento prévio de grandes volumes.",
        "prioridade": "Alta"
    },
    {
        "id": "RF03",
        "titulo": "Análise Estatística Descritiva",
        "descricao": "Permitir análise descritiva dos dados, incluindo medidas estatísticas e visualizações.",
        "prioridade": "Alta"
    },
    {
        "id": "RF04",
        "titulo": "Estatística Inferencial",
        "descricao": "Suportar análises de correlação, regressão e outros métodos inferenciais.",
        "prioridade": "Média"
    },
    {
        "id": "RF05",
        "titulo": "Análise de Séries Temporais",
        "descricao": "Implementar funcionalidades para análise de séries temporais, incluindo média móvel e modelos ARIMA.",
        "prioridade": "Média"
    },
    {
        "id": "RF06",
        "titulo": "Modelos de Machine Learning",
        "descricao": "Permitir a criação e aplicação de modelos de machine learning como redes neurais, classificação e agrupamento.",
        "prioridade": "Baixa"
    },
    {
        "id": "RF07",
        "titulo": "Análise Qualitativa (NLP)",
        "descricao": "Suportar análise qualitativa de dados textuais usando processamento de linguagem natural.",
        "prioridade": "Baixa"
    },
    {
        "id": "RF08",
        "titulo": "Cruzamento de Dados",
        "descricao": "Permitir o cruzamento de dados de diferentes fontes e bases.",
        "prioridade": "Alta"
    },
    {
        "id": "RF09",
        "titulo": "Exportação de Resultados",
        "descricao": "Permitir a exportação de resultados em formato de imagem (gráficos) e CSV (tabelas/dataframes).",
        "prioridade": "Alta"
    },
    {
        "id": "RF10",
        "titulo": "Assistência com IA",
        "descricao": "Utilizar IA para interpretar necessidades dos usuários e gerar código Python para análises.",
        "prioridade": "Média"
    }
]

# Exibir requisitos funcionais em tabela
st.dataframe(
    pd.DataFrame(requisitos_funcionais),
    use_container_width=True,
    hide_index=True
)

# Requisitos não funcionais
st.markdown('<div class="sub-header">Requisitos Não Funcionais</div>', unsafe_allow_html=True)

requisitos_nao_funcionais = [
    {
        "id": "RNF01",
        "categoria": "Usabilidade",
        "descricao": "A interface deve ser intuitiva e facilitar a compreensão das bases disponíveis.",
        "critério": "Usuários sem conhecimento técnico devem conseguir realizar análises básicas."
    },
    {
        "id": "RNF02",
        "categoria": "Desempenho",
        "descricao": "A aplicação deve processar apenas os dados mobilizados mediante solicitação.",
        "critério": "Tempo de resposta para consultas simples < 5 segundos."
    },
    {
        "id": "RNF03",
        "categoria": "Compatibilidade",
        "descricao": "A aplicação deve ser compatível com as APIs do Portal da Transparência e dados.gov.br.",
        "critério": "Integração bem-sucedida com todas as APIs especificadas."
    },
    {
        "id": "RNF04",
        "categoria": "Escalabilidade",
        "descricao": "A estrutura deve permitir fácil adição de novas fontes de dados.",
        "critério": "Adição de nova fonte sem modificação da arquitetura principal."
    },
    {
        "id": "RNF05",
        "categoria": "Tecnologia",
        "descricao": "Utilizar Python, Streamlit, OpenAI e pacotes Python para análises estatísticas.",
        "critério": "Conformidade com as tecnologias especificadas."
    },
    {
        "id": "RNF06",
        "categoria": "Hospedagem",
        "descricao": "A aplicação deve ser hospedada no Streamlit Cloud.",
        "critério": "Deploy bem-sucedido e acessível via URL pública."
    },
    {
        "id": "RNF07",
        "categoria": "Responsividade",
        "descricao": "A interface deve ser responsiva e funcionar em diferentes dispositivos.",
        "critério": "Funcionamento adequado em desktop e dispositivos móveis."
    }
]

# Exibir requisitos não funcionais em tabela
st.dataframe(
    pd.DataFrame(requisitos_nao_funcionais),
    use_container_width=True,
    hide_index=True
)

# Fontes de dados
st.markdown('<div class="sub-header">Fontes de Dados</div>', unsafe_allow_html=True)

st.markdown("""
### Portal da Transparência
- **URL Base**: http://api.portaldatransparencia.gov.br/api-de-dados/
- **Autenticação**: Chave de API (opcional para algumas consultas)
- **Formato**: JSON
- **Categorias Principais**:
  - Bolsa Família e Benefícios Sociais
  - Servidores Públicos
  - Despesas e Orçamento
  - Contratos e Licitações
  - Cadastros (CEIS, CNEP, CEPIM, CEAF)

### dados.gov.br
- **URL Base**: https://dados.gov.br/api/3/
- **Autenticação**: Não requerida para a maioria das consultas
- **Formato**: JSON, CSV, XML (dependendo do recurso)
- **Categorias Principais**:
  - Saúde
  - Educação
  - Economia e Finanças
  - Infraestrutura e Meio Ambiente
  - Agricultura
  - Segurança Pública
  - Cultura e Esporte
  - Administração Pública
""")

# Diagrama de arquitetura (texto representando um diagrama)
st.markdown('<div class="sub-header">Arquitetura da Aplicação</div>', unsafe_allow_html=True)

st.markdown("""
```
+------------------+     +------------------+     +------------------+
|                  |     |                  |     |                  |
|  Usuário Final   +---->+  Interface Web   +---->+  Processamento   |
|                  |     |   (Streamlit)    |     |    (Python)      |
|                  |     |                  |     |                  |
+------------------+     +------------------+     +--------+---------+
                                                          |
                                                          v
+------------------+     +------------------+     +------------------+
|                  |     |                  |     |                  |
|  Exportação de   |     |   Visualização   |<----+  Conectores API  |
|   Resultados     |<----+    de Dados      |     |                  |
|                  |     |                  |     |                  |
+------------------+     +------------------+     +--------+---------+
                                                          |
                                                          v
                                               +------------------+
                                               |                  |
                                               |  APIs Externas   |
                                               |  (Dados Abertos) |
                                               |                  |
                                               +------------------+
```
""")

# Fluxo de uso
st.markdown('<div class="sub-header">Fluxo de Uso Principal</div>', unsafe_allow_html=True)

st.markdown("""
1. Usuário acessa a aplicação via navegador
2. Seleciona a origem dos dados (Portal da Transparência ou dados.gov.br)
3. Navega pela hierarquia de categorias e bases disponíveis
4. Seleciona uma base específica para análise
5. Configura parâmetros de consulta (se necessário)
6. Visualiza os dados carregados
7. Realiza análises estatísticas ou cruzamentos com outras bases
8. Exporta resultados em formato desejado (CSV, imagem)
""")

# Métricas de sucesso
st.markdown('<div class="sub-header">Métricas de Sucesso</div>', unsafe_allow_html=True)

metricas = [
    {
        "categoria": "Desempenho",
        "metrica": "Tempo de resposta para consultas simples",
        "alvo": "< 5 segundos"
    },
    {
        "categoria": "Desempenho",
        "metrica": "Capacidade de processamento",
        "alvo": "Datasets de até 1 milhão de linhas"
    },
    {
        "categoria": "Usabilidade",
        "metrica": "Precisão na interpretação de solicitações em linguagem natural",
        "alvo": "> 80%"
    },
    {
        "categoria": "Usabilidade",
        "metrica": "Satisfação do usuário",
        "alvo": "> 4/5 em pesquisas de feedback"
    },
    {
        "categoria": "Funcionalidade",
        "metrica": "Cobertura de fontes de dados",
        "alvo": "100% das fontes prioritárias"
    },
    {
        "categoria": "Funcionalidade",
        "metrica": "Sucesso em operações de cruzamento",
        "alvo": "> 90% para bases compatíveis"
    }
]

# Exibir métricas em tabela
st.dataframe(
    pd.DataFrame(metricas),
    use_container_width=True,
    hide_index=True
)

# Limitações conhecidas
st.markdown('<div class="sub-header">Limitações Conhecidas</div>', unsafe_allow_html=True)

st.markdown("""
- **Volume de Dados**: Processamento limitado para conjuntos muito grandes
- **Disponibilidade de APIs**: Dependência da disponibilidade e estabilidade das APIs externas
- **Complexidade de Análises**: Algumas análises avançadas podem requerer ajustes manuais
- **Autenticação**: Algumas consultas ao Portal da Transparência requerem chave de API
- **Integração com IA**: Requer chave de API da OpenAI para funcionalidades completas
""")

# Rodapé
st.markdown("---")
st.caption("Documento de Requisitos - Aplicação Dados Abertos Gov - Versão 1.0")
