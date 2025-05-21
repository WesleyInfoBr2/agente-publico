"""
Página para validação da aplicação piloto com usuários.

Esta página permite coletar feedback dos usuários sobre a aplicação,
identificar problemas e sugestões de melhorias.
"""

import streamlit as st
import pandas as pd
import time
import datetime
import os
import json

# Configuração da página
st.set_page_config(
    page_title="Validação da Aplicação - Dados Abertos Gov",
    page_icon="✅",
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
    .feedback-box {
        background-color: #e8f4f9;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 1rem;
        border-left: 5px solid #4e8df5;
    }
</style>
""", unsafe_allow_html=True)

# Função para salvar feedback
def salvar_feedback(feedback_data):
    """Salva o feedback do usuário em um arquivo JSON."""
    # Criar diretório de feedback se não existir
    os.makedirs("feedback", exist_ok=True)
    
    # Nome do arquivo baseado na data/hora
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"feedback/feedback_{timestamp}.json"
    
    # Adicionar timestamp ao feedback
    feedback_data["timestamp"] = timestamp
    
    # Salvar como JSON
    with open(filename, "w") as f:
        json.dump(feedback_data, f, indent=4)
    
    return filename

# Função principal
def main():
    """Função principal da página."""
    
    # Cabeçalho
    st.markdown('<div class="main-header">✅ Validação da Aplicação Piloto</div>', unsafe_allow_html=True)
    
    st.markdown("""
    Sua opinião é muito importante para melhorarmos esta aplicação. 
    Por favor, dedique alguns minutos para compartilhar sua experiência e sugestões.
    """)
    
    # Formulário de feedback
    with st.form("feedback_form"):
        st.markdown("### Informações Gerais")
        
        col1, col2 = st.columns(2)
        
        with col1:
            nome = st.text_input("Nome (opcional):")
            perfil = st.selectbox(
                "Seu perfil:",
                ["Pesquisador", "Agente Público", "Estudante", "Desenvolvedor", "Jornalista", "Outro"]
            )
        
        with col2:
            email = st.text_input("E-mail (opcional):")
            area_atuacao = st.text_input("Área de atuação:")
        
        st.markdown("### Avaliação da Aplicação")
        
        # Avaliação geral
        st.markdown("#### Avaliação Geral")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            usabilidade = st.slider("Facilidade de uso:", 1, 5, 3)
        
        with col2:
            utilidade = st.slider("Utilidade das funcionalidades:", 1, 5, 3)
        
        with col3:
            desempenho = st.slider("Desempenho e velocidade:", 1, 5, 3)
        
        # Avaliação de funcionalidades específicas
        st.markdown("#### Avaliação de Funcionalidades")
        
        col1, col2 = st.columns(2)
        
        with col1:
            acesso_dados = st.slider("Acesso aos dados:", 1, 5, 3)
            cruzamento = st.slider("Cruzamento de dados:", 1, 5, 3)
        
        with col2:
            visualizacao = st.slider("Visualizações:", 1, 5, 3)
            assistente_ia = st.slider("Assistente com IA:", 1, 5, 3)
        
        # Feedback qualitativo
        st.markdown("#### Feedback Detalhado")
        
        pontos_positivos = st.text_area("Pontos positivos:", height=100)
        pontos_negativos = st.text_area("Pontos a melhorar:", height=100)
        sugestoes = st.text_area("Sugestões de novas funcionalidades:", height=100)
        
        # Problemas encontrados
        st.markdown("#### Problemas Encontrados")
        
        encontrou_problemas = st.checkbox("Encontrei problemas durante o uso")
        
        if encontrou_problemas:
            descricao_problema = st.text_area("Descreva o problema encontrado:", height=100)
            passos_reproducao = st.text_area("Passos para reproduzir o problema:", height=100)
        else:
            descricao_problema = ""
            passos_reproducao = ""
        
        # Uso futuro
        st.markdown("#### Uso Futuro")
        
        usaria_novamente = st.radio(
            "Você utilizaria esta aplicação novamente?",
            ["Sim, definitivamente", "Provavelmente sim", "Talvez", "Provavelmente não", "Não"]
        )
        
        recomendaria = st.radio(
            "Você recomendaria esta aplicação para colegas?",
            ["Sim, definitivamente", "Provavelmente sim", "Talvez", "Provavelmente não", "Não"]
        )
        
        # Botão de envio
        submitted = st.form_submit_button("Enviar Feedback")
        
        if submitted:
            # Coletar todos os dados do formulário
            feedback_data = {
                "nome": nome,
                "email": email,
                "perfil": perfil,
                "area_atuacao": area_atuacao,
                "avaliacao": {
                    "usabilidade": usabilidade,
                    "utilidade": utilidade,
                    "desempenho": desempenho,
                    "acesso_dados": acesso_dados,
                    "cruzamento": cruzamento,
                    "visualizacao": visualizacao,
                    "assistente_ia": assistente_ia
                },
                "feedback_qualitativo": {
                    "pontos_positivos": pontos_positivos,
                    "pontos_negativos": pontos_negativos,
                    "sugestoes": sugestoes
                },
                "problemas": {
                    "encontrou_problemas": encontrou_problemas,
                    "descricao": descricao_problema,
                    "passos_reproducao": passos_reproducao
                },
                "uso_futuro": {
                    "usaria_novamente": usaria_novamente,
                    "recomendaria": recomendaria
                }
            }
            
            try:
                # Salvar feedback
                filename = salvar_feedback(feedback_data)
                
                # Exibir mensagem de sucesso
                st.success(f"Feedback enviado com sucesso! Obrigado por sua contribuição.")
                
                # Exibir resumo do feedback
                st.markdown('<div class="feedback-box">', unsafe_allow_html=True)
                st.markdown("### Resumo do seu feedback")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**Avaliação geral:** {(usabilidade + utilidade + desempenho) / 3:.1f}/5")
                    st.markdown(f"**Funcionalidades:** {(acesso_dados + cruzamento + visualizacao + assistente_ia) / 4:.1f}/5")
                
                with col2:
                    st.markdown(f"**Usaria novamente:** {usaria_novamente}")
                    st.markdown(f"**Recomendaria:** {recomendaria}")
                
                st.markdown("</div>", unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"Erro ao salvar feedback: {str(e)}")
    
    # Seção de feedback já recebidos (apenas para demonstração)
    st.markdown("---")
    st.markdown('<div class="sub-header">Feedback Recebido</div>', unsafe_allow_html=True)
    
    # Dados de exemplo para demonstração
    feedback_exemplo = [
        {
            "nome": "Maria Silva",
            "perfil": "Pesquisadora",
            "avaliacao_geral": 4.2,
            "comentario": "Aplicação muito útil para minha pesquisa sobre políticas públicas. A integração com IA facilita muito a análise dos dados."
        },
        {
            "nome": "João Santos",
            "perfil": "Agente Público",
            "avaliacao_geral": 3.8,
            "comentario": "Boa ferramenta para acompanhamento de dados governamentais. Poderia ter mais opções de visualização para séries temporais."
        },
        {
            "nome": "Ana Oliveira",
            "perfil": "Estudante",
            "avaliacao_geral": 4.5,
            "comentario": "Excelente para trabalhos acadêmicos! Consegui cruzar dados de diferentes fontes com facilidade."
        }
    ]
    
    # Exibir feedback de exemplo
    for feedback in feedback_exemplo:
        st.markdown(f"""
        <div class="feedback-box">
            <strong>{feedback['nome']}</strong> ({feedback['perfil']}) - Avaliação: {feedback['avaliacao_geral']}/5<br>
            "{feedback['comentario']}"
        </div>
        """, unsafe_allow_html=True)
    
    # Nota sobre feedback de exemplo
    st.caption("Nota: Os feedbacks acima são exemplos para demonstração.")

# Executar a aplicação
if __name__ == "__main__":
    main()
