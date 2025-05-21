"""
Página para cruzamento de dados entre diferentes fontes.

Esta página permite selecionar conjuntos de dados de diferentes fontes,
identificar chaves comuns e realizar operações de cruzamento.
"""

import streamlit as st
import pandas as pd
import numpy as np
import time
import os
from src.utils.data_crosser import DataCrosser
from src.utils.data_visualizer import DataVisualizer
from src.ai.openai_assistant import OpenAIAssistant

# Inicialização dos objetos
@st.cache_resource
def inicializar_recursos():
    """Inicializa e retorna recursos necessários."""
    data_crosser = DataCrosser()
    data_visualizer = DataVisualizer()
    openai_assistant = OpenAIAssistant()
    return data_crosser, data_visualizer, openai_assistant

# Configuração da página
st.set_page_config(
    page_title="Cruzamento de Dados - Dados Abertos Gov",
    page_icon="🔄",
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

# Função para carregar dados da sessão
def carregar_dataframes_sessao():
    """Carrega DataFrames armazenados na sessão."""
    if "dataframes" not in st.session_state:
        st.session_state.dataframes = {}
    
    return st.session_state.dataframes

# Função para adicionar DataFrame à sessão
def adicionar_dataframe_sessao(nome, df, metadados=None):
    """Adiciona um DataFrame à sessão."""
    if "dataframes" not in st.session_state:
        st.session_state.dataframes = {}
    
    st.session_state.dataframes[nome] = {
        "data": df,
        "metadados": metadados or {}
    }

# Função principal
def main():
    """Função principal da página."""
    
    # Inicialização dos recursos
    data_crosser, data_visualizer, openai_assistant = inicializar_recursos()
    
    # Cabeçalho
    st.markdown('<div class="main-header">🔄 Cruzamento de Dados</div>', unsafe_allow_html=True)
    
    # Carregar DataFrames da sessão
    dataframes = carregar_dataframes_sessao()
    
    # Verificar se há DataFrames disponíveis
    if not dataframes:
        st.markdown('<div class="info-box">', unsafe_allow_html=True)
        st.markdown("""
        ## Nenhum conjunto de dados carregado
        
        Para realizar cruzamentos, você precisa primeiro carregar conjuntos de dados na página principal.
        
        1. Vá para a página inicial
        2. Selecione uma origem, categoria e base de dados
        3. Carregue os dados
        4. Retorne a esta página para realizar cruzamentos
        """)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Botão para navegar para a página inicial
        if st.button("Ir para a Página Inicial"):
            st.switch_page("app.py")
        
        return
    
    # Exibir DataFrames disponíveis
    st.markdown('<div class="sub-header">Conjuntos de Dados Disponíveis</div>', unsafe_allow_html=True)
    
    # Criar colunas para exibir os DataFrames disponíveis
    cols = st.columns(min(3, len(dataframes)))
    
    for i, (nome, info) in enumerate(dataframes.items()):
        col_idx = i % len(cols)
        with cols[col_idx]:
            st.markdown(f"**{nome}**")
            st.markdown(f"Linhas: {len(info['data'])}, Colunas: {len(info['data'].columns)}")
            
            # Exibir badges de origem e categoria, se disponíveis
            metadados = info.get("metadados", {})
            if "origem" in metadados or "categoria" in metadados:
                badges = ""
                if "origem" in metadados:
                    badges += f'<span class="source-badge">{metadados["origem"]}</span>'
                if "categoria" in metadados:
                    badges += f'<span class="category-badge">{metadados["categoria"]}</span>'
                st.markdown(badges, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Seção de cruzamento de dados
    st.markdown('<div class="sub-header">Cruzar Conjuntos de Dados</div>', unsafe_allow_html=True)
    
    # Selecionar DataFrames para cruzamento
    col1, col2 = st.columns(2)
    
    with col1:
        df1_nome = st.selectbox("Primeiro Conjunto de Dados:", list(dataframes.keys()), key="df1_select")
    
    with col2:
        df2_nome = st.selectbox("Segundo Conjunto de Dados:", 
                               [nome for nome in dataframes.keys() if nome != df1_nome],
                               key="df2_select")
    
    # Obter DataFrames selecionados
    if df1_nome and df2_nome:
        df1 = dataframes[df1_nome]["data"]
        df2 = dataframes[df2_nome]["data"]
        
        # Identificar chaves potenciais
        with st.spinner("Identificando chaves potenciais para cruzamento..."):
            chaves_potenciais = data_crosser.identificar_chaves_potenciais(df1, df2)
        
        if chaves_potenciais:
            st.success(f"Encontradas {len(chaves_potenciais)} possíveis chaves para cruzamento!")
            
            # Exibir chaves potenciais
            st.markdown("### Chaves Potenciais Identificadas")
            
            for i, (chave_df1, chave_df2, score) in enumerate(chaves_potenciais[:5]):
                st.markdown(f"**Opção {i+1}:** Cruzar `{chave_df1}` com `{chave_df2}` (Score: {score:.2f})")
            
            # Permitir seleção manual de chaves
            st.markdown("### Selecionar Chaves para Cruzamento")
            
            col1, col2 = st.columns(2)
            
            with col1:
                chave_df1 = st.selectbox("Coluna do Primeiro Conjunto:", df1.columns)
            
            with col2:
                chave_df2 = st.selectbox("Coluna do Segundo Conjunto:", df2.columns)
            
            # Selecionar método de junção
            metodo = st.selectbox(
                "Método de Junção:",
                ["inner", "left", "right", "outer"],
                format_func=lambda x: {
                    "inner": "Inner Join (apenas registros que existem em ambos)",
                    "left": "Left Join (todos do primeiro + correspondentes do segundo)",
                    "right": "Right Join (todos do segundo + correspondentes do primeiro)",
                    "outer": "Outer Join (todos os registros de ambos)"
                }.get(x)
            )
            
            # Botão para realizar o cruzamento
            if st.button("Realizar Cruzamento", type="primary"):
                with st.spinner("Realizando cruzamento de dados..."):
                    try:
                        # Realizar o cruzamento
                        df_resultado = data_crosser.cruzar_dataframes(df1, df2, chave_df1, chave_df2, metodo)
                        
                        # Avaliar qualidade do cruzamento
                        metricas = data_crosser.avaliar_qualidade_cruzamento(df_resultado, df1, df2)
                        
                        # Exibir resultados
                        st.success(f"Cruzamento realizado com sucesso! Resultado: {len(df_resultado)} linhas")
                        
                        # Exibir métricas
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Taxa de Correspondência (1º)", f"{metricas['taxa_correspondencia_df1']:.1%}")
                        
                        with col2:
                            st.metric("Taxa de Correspondência (2º)", f"{metricas['taxa_correspondencia_df2']:.1%}")
                        
                        with col3:
                            st.metric("Completude", f"{metricas['completude']:.1%}")
                        
                        # Exibir resultado
                        st.markdown("### Resultado do Cruzamento")
                        st.dataframe(df_resultado)
                        
                        # Opção para download
                        csv = df_resultado.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            "Baixar Resultado (CSV)",
                            data=csv,
                            file_name=f"cruzamento_{df1_nome}_{df2_nome}.csv",
                            mime="text/csv"
                        )
                        
                        # Adicionar à sessão
                        nome_resultado = f"Cruzamento {df1_nome} + {df2_nome}"
                        adicionar_dataframe_sessao(
                            nome_resultado, 
                            df_resultado,
                            {
                                "origem": "Cruzamento",
                                "df1": df1_nome,
                                "df2": df2_nome,
                                "metodo": metodo
                            }
                        )
                        
                        # Sugerir visualizações
                        st.markdown("### Visualizações Sugeridas")
                        
                        with st.spinner("Gerando sugestões de visualização..."):
                            sugestoes = data_visualizer.sugerir_visualizacoes(df_resultado)
                        
                        if sugestoes:
                            # Exibir até 3 visualizações sugeridas
                            for i, sugestao in enumerate(sugestoes[:3]):
                                with st.expander(f"{sugestao['titulo']}"):
                                    st.markdown(sugestao['descricao'])
                                    
                                    try:
                                        fig = data_visualizer.criar_visualizacao(
                                            df_resultado,
                                            tipo=sugestao['tipo'],
                                            colunas=sugestao['colunas'],
                                            titulo=sugestao['titulo']
                                        )
                                        
                                        st.plotly_chart(fig, use_container_width=True)
                                        
                                        # Opção para download da visualização
                                        img_bytes = data_visualizer.exportar_visualizacao(fig, formato="png")
                                        st.download_button(
                                            "Baixar Visualização (PNG)",
                                            data=img_bytes,
                                            file_name=f"vis_{sugestao['tipo']}_{i}.png",
                                            mime="image/png"
                                        )
                                    except Exception as e:
                                        st.error(f"Erro ao criar visualização: {str(e)}")
                        else:
                            st.info("Nenhuma visualização sugerida para este conjunto de dados.")
                        
                    except Exception as e:
                        st.error(f"Erro ao realizar cruzamento: {str(e)}")
        else:
            st.warning("Não foram encontradas chaves potenciais para cruzamento automático. Selecione as chaves manualmente.")
            
            # Permitir seleção manual de chaves
            col1, col2 = st.columns(2)
            
            with col1:
                chave_df1 = st.selectbox("Coluna do Primeiro Conjunto:", df1.columns)
            
            with col2:
                chave_df2 = st.selectbox("Coluna do Segundo Conjunto:", df2.columns)
            
            # Botão para realizar o cruzamento
            if st.button("Realizar Cruzamento", type="primary"):
                # Implementar cruzamento manual
                pass
    
    # Seção de IA para sugestão de cruzamentos
    st.markdown("---")
    st.markdown('<div class="sub-header">Assistente de Cruzamento com IA</div>', unsafe_allow_html=True)
    
    # Verificar se a API da OpenAI está disponível
    if openai_assistant.is_available():
        st.markdown("""
        Descreva em linguagem natural o tipo de cruzamento ou análise que você deseja realizar.
        O assistente irá sugerir as melhores abordagens com base nos dados disponíveis.
        """)
        
        # Campo para entrada do usuário
        solicitacao = st.text_area("Sua solicitação:", height=100, 
                                 placeholder="Ex: Quero cruzar dados de despesas com servidores para analisar gastos por órgão")
        
        if solicitacao:
            if st.button("Gerar Sugestões", type="primary"):
                with st.spinner("Processando sua solicitação com IA..."):
                    try:
                        # Preparar informações sobre os dados disponíveis
                        dados_info = {}
                        for nome, info in dataframes.items():
                            df = info["data"]
                            colunas_info = {}
                            
                            for col in df.columns:
                                colunas_info[col] = {
                                    "tipo": str(df[col].dtype),
                                    "n_valores_unicos": df[col].nunique(),
                                    "tem_nulos": df[col].isna().any()
                                }
                            
                            dados_info[nome] = {
                                "n_linhas": len(df),
                                "n_colunas": len(df.columns),
                                "colunas": colunas_info,
                                "metadados": info.get("metadados", {})
                            }
                        
                        # Interpretar a solicitação
                        interpretacao = openai_assistant.interpretar_solicitacao(solicitacao)
                        
                        # Gerar código Python
                        codigo = openai_assistant.gerar_codigo_python(
                            solicitacao,
                            dados_info
                        )
                        
                        # Exibir interpretação
                        st.markdown("### Interpretação da Solicitação")
                        st.json(interpretacao)
                        
                        # Exibir código gerado
                        st.markdown("### Código Python Sugerido")
                        st.code(codigo, language="python")
                        
                        # Opção para executar o código
                        if st.button("Executar Código Sugerido"):
                            with st.spinner("Executando código..."):
                                try:
                                    # Preparar ambiente de execução
                                    locals_dict = {
                                        "pd": pd,
                                        "np": np,
                                        "plt": plt,
                                        "sns": sns,
                                        "px": px,
                                        "go": go,
     
(Content truncated due to size limit. Use line ranges to read in chunks)