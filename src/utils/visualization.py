"""
Módulo para visualização de dados governamentais.

Este módulo contém funções para criação de visualizações estáticas e interativas
para dados obtidos das APIs do Portal da Transparência e CNDP.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Union, Optional, Any, Tuple
import os
import io
import base64
from datetime import datetime


# Configurações globais para visualizações
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_theme(style="whitegrid")


def configurar_tema(tema: str = 'default') -> None:
    """
    Configura o tema global para visualizações.
    
    Args:
        tema: Nome do tema ('default', 'dark', 'light', 'minimal')
    """
    if tema == 'default':
        plt.style.use('seaborn-v0_8-whitegrid')
        sns.set_theme(style="whitegrid")
    elif tema == 'dark':
        plt.style.use('dark_background')
        sns.set_theme(style="darkgrid")
    elif tema == 'light':
        plt.style.use('seaborn-v0_8-whitegrid')
        sns.set_theme(style="whitegrid")
    elif tema == 'minimal':
        plt.style.use('seaborn-v0_8-white')
        sns.set_theme(style="ticks")
    else:
        print(f"Tema '{tema}' não reconhecido. Usando tema padrão.")
        plt.style.use('seaborn-v0_8-whitegrid')
        sns.set_theme(style="whitegrid")


def grafico_barras(df: pd.DataFrame, x: str, y: str, titulo: str = None, 
                  xlabel: str = None, ylabel: str = None, 
                  ordenar: bool = False, palette: str = 'viridis',
                  figsize: Tuple[int, int] = (10, 6),
                  salvar: str = None) -> plt.Figure:
    """
    Cria um gráfico de barras.
    
    Args:
        df: DataFrame com os dados
        x: Coluna para o eixo x
        y: Coluna para o eixo y
        titulo: Título do gráfico (opcional)
        xlabel: Rótulo do eixo x (opcional)
        ylabel: Rótulo do eixo y (opcional)
        ordenar: Se True, ordena os dados pelo valor de y
        palette: Paleta de cores
        figsize: Tamanho da figura (largura, altura)
        salvar: Caminho para salvar o gráfico (opcional)
        
    Returns:
        Objeto Figure do matplotlib
    """
    # Preparar dados
    dados = df.copy()
    
    if ordenar:
        dados = dados.sort_values(by=y)
    
    # Criar figura
    fig, ax = plt.subplots(figsize=figsize)
    
    # Criar gráfico
    sns.barplot(data=dados, x=x, y=y, palette=palette, ax=ax)
    
    # Configurar rótulos
    ax.set_title(titulo or f'{y} por {x}')
    ax.set_xlabel(xlabel or x)
    ax.set_ylabel(ylabel or y)
    
    # Rotacionar rótulos do eixo x se necessário
    if len(dados[x].unique()) > 5:
        plt.xticks(rotation=45, ha='right')
    
    # Ajustar layout
    plt.tight_layout()
    
    # Salvar se caminho fornecido
    if salvar:
        plt.savefig(salvar, dpi=300, bbox_inches='tight')
    
    return fig


def grafico_barras_interativo(df: pd.DataFrame, x: str, y: str, 
                             cor: str = None, titulo: str = None,
                             xlabel: str = None, ylabel: str = None,
                             ordenar: bool = False,
                             template: str = 'plotly_white') -> go.Figure:
    """
    Cria um gráfico de barras interativo com Plotly.
    
    Args:
        df: DataFrame com os dados
        x: Coluna para o eixo x
        y: Coluna para o eixo y
        cor: Coluna para colorir as barras (opcional)
        titulo: Título do gráfico (opcional)
        xlabel: Rótulo do eixo x (opcional)
        ylabel: Rótulo do eixo y (opcional)
        ordenar: Se True, ordena os dados pelo valor de y
        template: Template do Plotly
        
    Returns:
        Objeto Figure do Plotly
    """
    # Preparar dados
    dados = df.copy()
    
    if ordenar:
        dados = dados.sort_values(by=y)
    
    # Configurar rótulos
    labels = {
        x: xlabel or x,
        y: ylabel or y
    }
    
    if cor:
        labels[cor] = cor
    
    # Criar gráfico
    fig = px.bar(
        dados, 
        x=x, 
        y=y, 
        color=cor,
        title=titulo or f'{y} por {x}',
        labels=labels,
        template=template
    )
    
    # Ajustar layout
    fig.update_layout(
        xaxis_tickangle=-45 if len(dados[x].unique()) > 5 else 0
    )
    
    return fig


def grafico_linhas(df: pd.DataFrame, x: str, y: Union[str, List[str]], 
                  titulo: str = None, xlabel: str = None, ylabel: str = None,
                  figsize: Tuple[int, int] = (10, 6),
                  salvar: str = None) -> plt.Figure:
    """
    Cria um gráfico de linhas.
    
    Args:
        df: DataFrame com os dados
        x: Coluna para o eixo x
        y: Coluna ou lista de colunas para o eixo y
        titulo: Título do gráfico (opcional)
        xlabel: Rótulo do eixo x (opcional)
        ylabel: Rótulo do eixo y (opcional)
        figsize: Tamanho da figura (largura, altura)
        salvar: Caminho para salvar o gráfico (opcional)
        
    Returns:
        Objeto Figure do matplotlib
    """
    # Preparar dados
    dados = df.copy()
    
    # Converter y para lista se for string
    if isinstance(y, str):
        y = [y]
    
    # Criar figura
    fig, ax = plt.subplots(figsize=figsize)
    
    # Criar gráfico para cada coluna y
    for coluna in y:
        ax.plot(dados[x], dados[coluna], marker='o', linestyle='-', label=coluna)
    
    # Configurar rótulos
    ax.set_title(titulo or f'Evolução de {", ".join(y)} por {x}')
    ax.set_xlabel(xlabel or x)
    ax.set_ylabel(ylabel or (y[0] if len(y) == 1 else 'Valor'))
    
    # Adicionar legenda se múltiplas colunas
    if len(y) > 1:
        ax.legend()
    
    # Rotacionar rótulos do eixo x se necessário
    if len(dados[x].unique()) > 5:
        plt.xticks(rotation=45, ha='right')
    
    # Ajustar layout
    plt.tight_layout()
    
    # Adicionar grade
    ax.grid(True, linestyle='--', alpha=0.7)
    
    # Salvar se caminho fornecido
    if salvar:
        plt.savefig(salvar, dpi=300, bbox_inches='tight')
    
    return fig


def grafico_linhas_interativo(df: pd.DataFrame, x: str, y: Union[str, List[str]],
                             cor: str = None, titulo: str = None,
                             xlabel: str = None, ylabel: str = None,
                             template: str = 'plotly_white') -> go.Figure:
    """
    Cria um gráfico de linhas interativo com Plotly.
    
    Args:
        df: DataFrame com os dados
        x: Coluna para o eixo x
        y: Coluna ou lista de colunas para o eixo y
        cor: Coluna para colorir as linhas (opcional)
        titulo: Título do gráfico (opcional)
        xlabel: Rótulo do eixo x (opcional)
        ylabel: Rótulo do eixo y (opcional)
        template: Template do Plotly
        
    Returns:
        Objeto Figure do Plotly
    """
    # Preparar dados
    dados = df.copy()
    
    # Configurar rótulos
    labels = {
        x: xlabel or x
    }
    
    # Converter y para lista se for string
    if isinstance(y, str):
        y = [y]
        labels[y[0]] = ylabel or y[0]
    else:
        for coluna in y:
            labels[coluna] = coluna
    
    if cor:
        labels[cor] = cor
    
    # Criar gráfico
    if len(y) == 1 and cor:
        # Gráfico de linha com cor
        fig = px.line(
            dados, 
            x=x, 
            y=y[0], 
            color=cor,
            title=titulo or f'Evolução de {y[0]} por {x}',
            labels=labels,
            template=template,
            markers=True
        )
    elif len(y) == 1:
        # Gráfico de linha simples
        fig = px.line(
            dados, 
            x=x, 
            y=y[0],
            title=titulo or f'Evolução de {y[0]} por {x}',
            labels=labels,
            template=template,
            markers=True
        )
    else:
        # Múltiplas linhas
        fig = go.Figure()
        
        for coluna in y:
            fig.add_trace(
                go.Scatter(
                    x=dados[x],
                    y=dados[coluna],
                    mode='lines+markers',
                    name=coluna
                )
            )
        
        fig.update_layout(
            title=titulo or f'Evolução de múltiplas variáveis por {x}',
            xaxis_title=xlabel or x,
            yaxis_title=ylabel or 'Valor',
            template=template
        )
    
    # Ajustar layout
    fig.update_layout(
        xaxis_tickangle=-45 if len(dados[x].unique()) > 5 else 0
    )
    
    return fig


def grafico_pizza(df: pd.DataFrame, coluna: str, valores: str = None,
                 titulo: str = None, figsize: Tuple[int, int] = (10, 8),
                 salvar: str = None) -> plt.Figure:
    """
    Cria um gráfico de pizza.
    
    Args:
        df: DataFrame com os dados
        coluna: Coluna para as fatias
        valores: Coluna para os valores (opcional, se None usa contagem)
        titulo: Título do gráfico (opcional)
        figsize: Tamanho da figura (largura, altura)
        salvar: Caminho para salvar o gráfico (opcional)
        
    Returns:
        Objeto Figure do matplotlib
    """
    # Preparar dados
    if valores:
        dados = df.groupby(coluna)[valores].sum().reset_index()
        valores_pizza = dados[valores]
        rotulos = dados[coluna]
    else:
        dados = df[coluna].value_counts().reset_index()
        valores_pizza = dados[coluna]
        rotulos = dados['index']
    
    # Criar figura
    fig, ax = plt.subplots(figsize=figsize)
    
    # Criar gráfico
    wedges, texts, autotexts = ax.pie(
        valores_pizza,
        labels=rotulos,
        autopct='%1.1f%%',
        startangle=90,
        shadow=False
    )
    
    # Melhorar legibilidade
    plt.setp(autotexts, size=10, weight='bold')
    plt.setp(texts, size=12)
    
    # Configurar rótulos
    ax.set_title(titulo or f'Distribuição de {coluna}')
    
    # Ajustar layout
    plt.tight_layout()
    
    # Salvar se caminho fornecido
    if salvar:
        plt.savefig(salvar, dpi=300, bbox_inches='tight')
    
    return fig


def grafico_pizza_interativo(df: pd.DataFrame, coluna: str, valores: str = None,
                            titulo: str = None, template: str = 'plotly_white') -> go.Figure:
    """
    Cria um gráfico de pizza interativo com Plotly.
    
    Args:
        df: DataFrame com os dados
        coluna: Coluna para as fatias
        valores: Coluna para os valores (opcional, se None usa contagem)
        titulo: Título do gráfico (opcional)
        template: Template do Plotly
        
    Returns:
        Objeto Figure do Plotly
    """
    # Preparar dados
    if valores:
        dados = df.groupby(coluna)[valores].sum().reset_index()
        valores_coluna = valores
    else:
        dados = df[coluna].value_counts().reset_index()
        coluna, valores_coluna = 'index', coluna
    
    # Criar gráfico
    fig = px.pie(
        dados,
        names=coluna,
        values=valores_coluna,
        title=titulo or f'Distribuição de {coluna}',
        template=template
    )
    
    # Ajustar layout
    fig.update_traces(textposition='inside', textinfo='percent+label')
    
    return fig


def grafico_dispersao(df: pd.DataFrame, x: str, y: str, cor: str = None,
                     tamanho: str = None, titulo: str = None,
                     xlabel: str = None, ylabel: str = None,
                     figsize: Tuple[int, int] = (10, 6),
                     salvar: str = None) -> plt.Figure:
    """
    Cria um gráfico de dispersão.
    
    Args:
        df: DataFrame com os dados
        x: Coluna para o eixo x
        y: Coluna para o eixo y
        cor: Coluna para colorir os pontos (opcional)
        tamanho: Coluna para o tamanho dos pontos (opcional)
        titulo: Título do gráfico (opcional)
        xlabel: Rótulo do eixo x (opcional)
        ylabel: Rótulo do eixo y (opcional)
        figsize: Tamanho da figura (largura, altura)
        salvar: Caminho para salvar o gráfico (opcional)
        
    Returns:
        Objeto Figure do matplotlib
    """
    # Criar figura
    fig, ax = plt.subplots(figsize=figsize)
    
    # Criar gráfico
    if cor:
        scatter = sns.scatterplot(
            data=df,
            x=x,
            y=y,
            hue=cor,
            size=tamanho,
            alpha=0.7,
            ax=ax
        )
    else:
        scatter = sns.scatterplot(
            data=df,
            x=x,
            y=y,
            size=tamanho,
            alpha=0.7,
            ax=ax
        )
    
    # Configurar rótulos
    ax.set_title(titulo or f'Relação entre {x} e {y}')
    ax.set_xlabel(xlabel or x)
    ax.set_ylabel(ylabel or y)
    
    # Adicionar grade
    ax.grid(True, linestyle='--', alpha=0.7)
    
    # Ajustar layout
    plt.tight_layout()
    
    # Salvar se caminho fornecido
    if salvar:
        plt.savefig(salvar, dpi=300, bbox_inches='tight')
    
    return fig


def grafico_dispersao_interativo(df: pd.DataFrame, x: str, y: str, 
                                cor: str = None, tamanho: str = None,
                                texto: str = None, titulo: str = None,
                                xlabel: str = None, ylabel: str = None,
                                template: str = 'plotly_white') -> go.Figure:
    """
    Cria um gráfico de dispersão interativo com Plotly.
    
    Args:
        df: DataFrame com os dados
        x: Coluna para o eixo x
        y: Coluna para o eixo y
        cor: Coluna para colorir os pontos (opcional)
        tamanho: Coluna para o tamanho dos pontos (opcional)
        texto: Coluna para o texto ao passar o mouse (opcional)
        titulo: Título do gráfico (opcional)
        xlabel: Rótulo do eixo x (opcional)
        ylabel: Rótulo do eixo y (opcional)
        template: Template do Plotly
        
    Returns:
        Objeto Figure do Plotly
    """
    # Configurar rótulos
    labels = {
        x: xlabel or x,
        y: ylabel or y
    }
    
    if cor:
        labels[cor] = cor
    
    if tamanho:
        labels[tamanho] = tamanho
    
    # Criar gráfico
    fig = px.scatter(
        df,
        x=x,
        y=y,
        color=cor,
        size=tamanho,
        hover_name=texto,
        title=titulo or f'Relação entre {x} e {y}',
        labels=labels,
        template=template
    )
    
    # Adicionar linha de tendência
    if df[x].dtype in [np.int64, np.float64] and df[y].dtype in [np.int64, np.float64]:
        fig.update_layout(
            shapes=[
                dict(
                    type='line',
                    xref='x', yref='y',
                    x0=df[x].min(), y0=np.polyval(np.polyfit(df[x], df[y], 1), df[x].min()),
                    x1=df[x].max(), y1=np.polyval(np.polyfit(df[x], df[y], 1), df[x].max()),
                    line=dict(color='red', width=2, dash='dash')
                )
            ]
        )
    
    return fig


def grafico_boxplot(df: pd.DataFrame, x: str = None, y: str = None,
                   cor: str = None, titulo: str = None,
                   xlabel: str = None, ylabel: str = None,
                   figsize: Tuple[int, int] = (10, 6),
                   salvar: str = None) -> plt.Figure:
    """
    Cria um gráfico boxplot.
    
    Args:
        df: DataFrame com os dados
        x: Coluna categórica para o eixo x (opcional)
        y: Coluna numérica para o eixo y (opcional)
        cor: Coluna para colorir os boxplots (opcional)
        titulo: Título do gráfico (opcional)
        xlabel: Rótulo do eixo x (opcional)
        ylabel: Rótulo do eixo y (opcional)
        figsize: Tamanho da figura (largura, altura)
        salvar: Caminho para salvar o gráfico (opcional)
        
    Returns:
        Objeto Figure do matplotlib
    """
    # Criar figura
    fig, ax = plt.subplots(figsize=figsize)
    
    # Criar gráfico
    if x and y:
   
(Content truncated due to size limit. Use line ranges to read in chunks)