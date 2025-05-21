"""
Módulo para integração com a API da OpenAI.

Este módulo fornece funções para processamento de linguagem natural
e geração de código Python usando a API da OpenAI.
"""

import os
import logging
import json
from typing import Dict, List, Any, Optional, Union
import openai

# Configuração de logging
logger = logging.getLogger(__name__)

class OpenAIAssistant:
    """
    Cliente para a API da OpenAI.
    
    Permite processar linguagem natural e gerar código Python
    para análise de dados usando a API da OpenAI.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        """
        Inicializa o cliente da API da OpenAI.
        
        Args:
            api_key: Chave de API da OpenAI. Se não fornecida, tentará obter
                    da variável de ambiente OPENAI_API_KEY.
            model: Modelo da OpenAI a ser utilizado (padrão: gpt-4).
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        
        if not self.api_key:
            logger.warning("Chave de API da OpenAI não fornecida. "
                          "Funcionalidades de IA não estarão disponíveis.")
        else:
            openai.api_key = self.api_key
        
        self.model = model
    
    def is_available(self) -> bool:
        """
        Verifica se a API da OpenAI está disponível.
        
        Returns:
            True se a API estiver disponível, False caso contrário.
        """
        return bool(self.api_key)
    
    def interpretar_solicitacao(self, texto: str) -> Dict[str, Any]:
        """
        Interpreta uma solicitação em linguagem natural.
        
        Args:
            texto: Texto da solicitação.
            
        Returns:
            Dicionário com interpretação estruturada da solicitação.
            
        Raises:
            Exception: Se ocorrer um erro na chamada à API.
        """
        if not self.is_available():
            raise ValueError("API da OpenAI não disponível. Verifique a chave de API.")
        
        try:
            prompt = f"""
            Analise a seguinte solicitação de análise de dados e extraia informações estruturadas:
            
            "{texto}"
            
            Retorne um JSON com os seguintes campos:
            - tipo_analise: o tipo principal de análise solicitada (descritiva, inferencial, serie_temporal, machine_learning, nlp)
            - variaveis: lista de variáveis/colunas mencionadas
            - filtros: quaisquer filtros ou condições mencionados
            - visualizacoes: tipos de visualizações solicitadas
            - metricas: métricas estatísticas solicitadas
            - outros_parametros: quaisquer outros parâmetros relevantes
            """
            
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Você é um assistente especializado em análise de dados que extrai informações estruturadas de solicitações em linguagem natural."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            # Extrair a resposta
            content = response.choices[0].message.content
            
            # Tentar extrair o JSON da resposta
            try:
                # Procurar por blocos de código JSON
                if "```json" in content:
                    json_str = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    json_str = content.split("```")[1].strip()
                else:
                    json_str = content.strip()
                
                return json.loads(json_str)
            except json.JSONDecodeError:
                logger.error(f"Erro ao decodificar JSON da resposta: {content}")
                return {
                    "tipo_analise": "desconhecido",
                    "erro": "Não foi possível interpretar a solicitação",
                    "resposta_original": content
                }
                
        except Exception as e:
            logger.error(f"Erro ao chamar API da OpenAI: {e}")
            raise
    
    def gerar_codigo_python(self, solicitacao: str, 
                           dados_info: Dict[str, Any],
                           bibliotecas_disponiveis: Optional[List[str]] = None) -> str:
        """
        Gera código Python para análise de dados com base em uma solicitação.
        
        Args:
            solicitacao: Texto da solicitação.
            dados_info: Informações sobre os dados disponíveis (colunas, tipos, etc).
            bibliotecas_disponiveis: Lista de bibliotecas disponíveis para uso.
            
        Returns:
            Código Python gerado.
            
        Raises:
            Exception: Se ocorrer um erro na chamada à API.
        """
        if not self.is_available():
            raise ValueError("API da OpenAI não disponível. Verifique a chave de API.")
        
        # Bibliotecas padrão se não especificadas
        if bibliotecas_disponiveis is None:
            bibliotecas_disponiveis = [
                "pandas", "numpy", "matplotlib", "seaborn", "plotly", 
                "scipy", "statsmodels", "sklearn", "prophet"
            ]
        
        try:
            # Converter informações dos dados para formato de texto
            dados_info_str = json.dumps(dados_info, indent=2)
            bibliotecas_str = ", ".join(bibliotecas_disponiveis)
            
            prompt = f"""
            Gere código Python para a seguinte solicitação de análise de dados:
            
            "{solicitacao}"
            
            Informações sobre os dados disponíveis:
            {dados_info_str}
            
            Bibliotecas disponíveis: {bibliotecas_str}
            
            O código deve:
            1. Ser completo e executável
            2. Incluir comentários explicativos
            3. Seguir boas práticas de programação
            4. Usar visualizações atraentes e informativas
            5. Incluir interpretações dos resultados em comentários
            
            Retorne apenas o código Python, sem explicações adicionais.
            """
            
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Você é um especialista em análise de dados e programação Python que gera código de alta qualidade."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=2000
            )
            
            # Extrair a resposta
            content = response.choices[0].message.content
            
            # Extrair apenas o código Python
            if "```python" in content:
                code = content.split("```python")[1].split("```")[0].strip()
            elif "```" in content:
                code = content.split("```")[1].strip()
            else:
                code = content.strip()
            
            return code
                
        except Exception as e:
            logger.error(f"Erro ao chamar API da OpenAI: {e}")
            raise
    
    def explicar_resultados(self, codigo: str, resultados: str) -> str:
        """
        Gera uma explicação em linguagem natural dos resultados de uma análise.
        
        Args:
            codigo: Código Python executado.
            resultados: Resultados da execução (texto ou representação JSON).
            
        Returns:
            Explicação em linguagem natural.
            
        Raises:
            Exception: Se ocorrer um erro na chamada à API.
        """
        if not self.is_available():
            raise ValueError("API da OpenAI não disponível. Verifique a chave de API.")
        
        try:
            prompt = f"""
            Explique os seguintes resultados de análise de dados em linguagem simples e acessível:
            
            Código executado:
            ```python
            {codigo}
            ```
            
            Resultados obtidos:
            ```
            {resultados}
            ```
            
            Forneça uma explicação clara e concisa, destacando os principais insights e conclusões.
            """
            
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Você é um especialista em análise de dados que explica resultados técnicos em linguagem acessível."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            # Extrair a resposta
            return response.choices[0].message.content
                
        except Exception as e:
            logger.error(f"Erro ao chamar API da OpenAI: {e}")
            raise
    
    def sugerir_analises(self, dados_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Sugere análises relevantes com base nas informações dos dados.
        
        Args:
            dados_info: Informações sobre os dados disponíveis (colunas, tipos, etc).
            
        Returns:
            Lista de sugestões de análises.
            
        Raises:
            Exception: Se ocorrer um erro na chamada à API.
        """
        if not self.is_available():
            raise ValueError("API da OpenAI não disponível. Verifique a chave de API.")
        
        try:
            # Converter informações dos dados para formato de texto
            dados_info_str = json.dumps(dados_info, indent=2)
            
            prompt = f"""
            Com base nas informações dos dados abaixo, sugira 5 análises relevantes que poderiam gerar insights valiosos:
            
            {dados_info_str}
            
            Para cada sugestão, forneça:
            1. Um título descritivo
            2. O tipo de análise (descritiva, inferencial, série temporal, etc.)
            3. As variáveis envolvidas
            4. Uma breve justificativa da relevância
            
            Retorne as sugestões em formato JSON, como uma lista de objetos com os campos: titulo, tipo, variaveis, justificativa.
            """
            
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Você é um cientista de dados especializado em identificar análises relevantes para diferentes conjuntos de dados."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            # Extrair a resposta
            content = response.choices[0].message.content
            
            # Tentar extrair o JSON da resposta
            try:
                # Procurar por blocos de código JSON
                if "```json" in content:
                    json_str = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    json_str = content.split("```")[1].strip()
                else:
                    json_str = content.strip()
                
                return json.loads(json_str)
            except json.JSONDecodeError:
                logger.error(f"Erro ao decodificar JSON da resposta: {content}")
                return [{"titulo": "Erro ao processar sugestões", "tipo": "erro", "variaveis": [], "justificativa": "Não foi possível processar as sugestões de análise."}]
                
        except Exception as e:
            logger.error(f"Erro ao chamar API da OpenAI: {e}")
            raise
