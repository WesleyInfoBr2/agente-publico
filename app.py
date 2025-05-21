"""
Aplicação principal para análise de dados abertos governamentais.

Este é o arquivo principal da aplicação Streamlit que permite
explorar, visualizar e analisar dados abertos do governo brasileiro.
"""

import os
import streamlit as st
from src.api import transparencia, dados_gov

# Configuração da página
st.set_page_config(
    page_title="Dados Abertos Gov - Análise Facilitada",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicialização das APIs
@st.cache_resource
def inicializar_apis():
    """Inicializa e retorna instâncias das APIs."""
    transparencia_api = TransparenciaAPI()
    dados_gov_api = DadosGovAPI()
    return transparencia_api, dados_gov_api

# Estilo CSS personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
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
    .source-badge {
        background-color: #4e8df5;
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 0.3rem;
        font-size: 0.8rem;
        margin-right: 0.5rem;
    }
    .category-badge {
        background-color: #f5814e;
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 0.3rem;
        font-size: 0.8rem;
        margin-right: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Função principal da aplicação."""
    
    # Inicialização das APIs
    transparencia_api, dados_gov_api = inicializar_apis()
    
    # Cabeçalho
    st.markdown('<div class="main-header">📊 Dados Abertos Gov - Análise Facilitada</div>', unsafe_allow_html=True)
    
    # Sidebar - Navegação Hierárquica
    with st.sidebar:
        st.markdown('<div class="sub-header">Navegação</div>', unsafe_allow_html=True)
        
        # Seleção de Origem
        origem = st.selectbox(
            "Selecione a Origem dos Dados:",
            ["Portal da Transparência", "dados.gov.br"]
        )
        
        # Seleção de Categoria baseada na Origem
        if origem == "Portal da Transparência":
            categorias = transparencia_api.get_categorias()
            categoria = st.selectbox("Selecione a Categoria:", categorias)
            
            # Seleção de Base baseada na Categoria
            bases = transparencia_api.get_bases_por_categoria(categoria)
            base = st.selectbox("Selecione a Base de Dados:", list(bases.keys()))
            
        else:  # dados.gov.br
            categorias = dados_gov_api.get_categorias()
            categoria = st.selectbox("Selecione a Categoria:", categorias)
            
            # Para dados.gov.br, precisamos buscar conjuntos de dados baseados na categoria
            st.info("Buscando conjuntos de dados disponíveis...")
            conjuntos = dados_gov_api.buscar_conjuntos_por_categoria(categoria, limite=20)
            
            if conjuntos:
                opcoes_conjuntos = {conjunto["title"]: conjunto["id"] for conjunto in conjuntos}
                base = st.selectbox("Selecione o Conjunto de Dados:", list(opcoes_conjuntos.keys()))
                id_conjunto = opcoes_conjuntos[base]
            else:
                st.warning("Nenhum conjunto de dados encontrado para esta categoria.")
                base = None
                id_conjunto = None
        
        # Botão para carregar dados
        carregar_dados = st.button("Carregar Dados", type="primary")
        
        # Informações adicionais
        st.markdown("---")
        st.markdown('<div class="sub-header">Sobre</div>', unsafe_allow_html=True)
        st.markdown("""
        Esta aplicação permite explorar e analisar dados abertos do governo brasileiro 
        de forma facilitada, com recursos de visualização e análise estatística.
        """)
        
        st.markdown("---")
        st.markdown("Desenvolvido com ❤️ usando Python e Streamlit")
    
    # Conteúdo principal
    if carregar_dados:
        if origem == "Portal da Transparência" and base:
            st.markdown(f'<div class="sub-header">Dados de {base} <span class="source-badge">{origem}</span> <span class="category-badge">{categoria}</span></div>', unsafe_allow_html=True)
            
            # Exibir parâmetros necessários
            parametros = transparencia_api.listar_parametros_necessarios(categoria, base)
            
            if parametros:
                st.markdown('<div class="info-box">Esta base requer parâmetros adicionais para consulta.</div>', unsafe_allow_html=True)
                
                # Criar formulário para os parâmetros
                with st.form("parametros_form"):
                    valores_parametros = {}
                    
                    for param in parametros:
                        if param["tipo"] == "string":
                            valores_parametros[param["nome"]] = st.text_input(
                                f"{param['nome']} ({param['descricao']})",
                                value=param.get("padrao", "")
                            )
                        elif param["tipo"] == "integer":
                            valores_parametros[param["nome"]] = st.number_input(
                                f"{param['nome']} ({param['descricao']})",
                                value=param.get("padrao", 1),
                                step=1
                            )
                    
                    # Botão de submissão
                    submitted = st.form_submit_button("Consultar")
                    
                    if submitted:
                        with st.spinner("Consultando dados..."):
                            try:
                                dados = transparencia_api.consultar_dados(categoria, base, valores_parametros)
                                
                                if dados:
                                    st.success(f"Dados carregados com sucesso! ({len(dados)} registros)")
                                    st.dataframe(dados)
                                    
                                    # Opção para download
                                    st.download_button(
                                        "Baixar dados (CSV)",
                                        data=pd.DataFrame(dados).to_csv(index=False).encode('utf-8'),
                                        file_name=f"{base.lower().replace(' ', '_')}.csv",
                                        mime="text/csv"
                                    )
                                else:
                                    st.warning("Nenhum dado encontrado para os parâmetros fornecidos.")
                            except Exception as e:
                                st.error(f"Erro ao consultar dados: {str(e)}")
            else:
                # Tentar obter uma amostra de dados
                with st.spinner("Carregando amostra de dados..."):
                    try:
                        dados = transparencia_api.obter_amostra_dados(categoria, base)
                        
                        if dados:
                            st.success(f"Amostra de dados carregada com sucesso! ({len(dados)} registros)")
                            st.dataframe(dados)
                        else:
                            st.warning("Não foi possível obter uma amostra de dados para esta base.")
                    except Exception as e:
                        st.error(f"Erro ao carregar amostra: {str(e)}")
        
        elif origem == "dados.gov.br" and base and id_conjunto:
            st.markdown(f'<div class="sub-header">Conjunto de Dados: {base} <span class="source-badge">{origem}</span> <span class="category-badge">{categoria}</span></div>', unsafe_allow_html=True)
            
            # Obter detalhes do conjunto
            with st.spinner("Carregando detalhes do conjunto..."):
                try:
                    detalhes = dados_gov_api.obter_detalhes_conjunto(id_conjunto)
                    
                    if detalhes:
                        # Exibir informações básicas
                        st.markdown(f"**Descrição:** {detalhes.get('notes', 'Sem descrição')}")
                        st.markdown(f"**Organização:** {detalhes.get('organization', {}).get('title', 'Desconhecida')}")
                        st.markdown(f"**Última atualização:** {detalhes.get('metadata_modified', 'Desconhecida')}")
                        
                        # Listar recursos disponíveis
                        recursos = detalhes.get("resources", [])
                        
                        if recursos:
                            st.markdown('<div class="sub-header">Recursos Disponíveis</div>', unsafe_allow_html=True)
                            
                            for i, recurso in enumerate(recursos):
                                with st.expander(f"{recurso.get('name', f'Recurso {i+1}')} ({recurso.get('format', 'Formato desconhecido')})"):
                                    st.markdown(f"**Descrição:** {recurso.get('description', 'Sem descrição')}")
                                    st.markdown(f"**Formato:** {recurso.get('format', 'Desconhecido')}")
                                    st.markdown(f"**Última atualização:** {recurso.get('last_modified', 'Desconhecida')}")
                                    
                                    # Opções para visualizar ou baixar
                                    col1, col2 = st.columns(2)
                                    
                                    with col1:
                                        if st.button("Visualizar Dados", key=f"view_{i}"):
                                            with st.spinner("Carregando dados..."):
                                                try:
                                                    # Verificar formato para tratamento adequado
                                                    formato = recurso.get('format', '').lower()
                                                    url = recurso.get('url')
                                                    
                                                    if url:
                                                        if formato in ['csv', 'json']:
                                                            # Para formatos estruturados, tentar carregar como DataFrame
                                                            import pandas as pd
                                                            
                                                            if formato == 'csv':
                                                                df = pd.read_csv(url)
                                                            else:  # json
                                                                df = pd.read_json(url)
                                                            
                                                            st.dataframe(df)
                                                            
                                                            # Opção para download
                                                            st.download_button(
                                                                "Baixar dados (CSV)",
                                                                data=df.to_csv(index=False).encode('utf-8'),
                                                                file_name=f"{recurso.get('name', 'dados').lower().replace(' ', '_')}.csv",
                                                                mime="text/csv"
                                                            )
                                                        else:
                                                            st.warning(f"Visualização direta não suportada para o formato {formato}.")
                                                            st.markdown(f"[Abrir URL do recurso]({url})")
                                                    else:
                                                        st.error("URL do recurso não disponível.")
                                                except Exception as e:
                                                    st.error(f"Erro ao carregar dados: {str(e)}")
                                    
                                    with col2:
                                        if recurso.get('url'):
                                            st.markdown(f"[Download Direto]({recurso.get('url')})")
                        else:
                            st.warning("Nenhum recurso disponível para este conjunto de dados.")
                    else:
                        st.error("Não foi possível obter detalhes do conjunto de dados.")
                except Exception as e:
                    st.error(f"Erro ao carregar detalhes: {str(e)}")
        
        else:
            st.info("Selecione uma origem, categoria e base de dados, e clique em 'Carregar Dados'.")
    else:
        # Tela inicial quando nenhum dado foi carregado
        st.markdown('<div class="info-box">', unsafe_allow_html=True)
        st.markdown("""
        ## Bem-vindo à Análise Facilitada de Dados Abertos Governamentais!
        
        Esta aplicação permite explorar e analisar dados abertos do governo brasileiro de forma simples e intuitiva.
        
        ### Como usar:
        
        1. Selecione a **Origem** dos dados no menu lateral (Portal da Transparência ou dados.gov.br)
        2. Escolha uma **Categoria** de dados
        3. Selecione uma **Base de Dados** específica
        4. Clique em **Carregar Dados** para visualizar e analisar
        
        ### Recursos disponíveis:
        
        - Visualização de dados em tabelas interativas
        - Análises estatísticas descritivas e inferenciais
        - Séries temporais e previsões
        - Modelos de machine learning
        - Análise qualitativa com NLP
        
        Navegue pelas diferentes páginas da aplicação para acessar funcionalidades específicas.
        """)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Exibir algumas estatísticas gerais
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="sub-header">Portal da Transparência</div>', unsafe_allow_html=True)
            transparencia_api, _ = inicializar_apis()
            categorias = transparencia_api.get_categorias()
            
            total_bases = sum(len(transparencia_api.get_bases_por_categoria(cat)) for cat in categorias)
            
            st.metric("Categorias disponíveis", len(categorias))
            st.metric("Bases de dados", total_bases)
        
        with col2:
            st.markdown('<div class="sub-header">dados.gov.br</div>', unsafe_allow_html=True)
            _, dados_gov_api = inicializar_apis()
            categorias = dados_gov_api.get_categorias()
            
            # Aqui seria ideal ter o número total de conjuntos, mas isso exigiria muitas requisições
            # Então usamos um valor aproximado
            st.metric("Categorias disponíveis", len(categorias))
            st.metric("Conjuntos de dados (aprox.)", "14.000+")

# Garantir que pandas esteja disponível
import pandas as pd

# Executar a aplicação
if __name__ == "__main__":
    main()
