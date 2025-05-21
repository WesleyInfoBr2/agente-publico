# Documentação da Aplicação Piloto - Dados Abertos Gov

## Visão Geral

Esta aplicação piloto permite o acesso, visualização e análise de dados abertos do governo brasileiro, com foco inicial no Portal da Transparência e dados.gov.br. A aplicação utiliza Python, Streamlit e OpenAI para processamento de linguagem natural, oferecendo uma interface intuitiva para pesquisadores e agentes públicos.

## Funcionalidades Implementadas

1. **Acesso a Dados**
   - Navegação hierárquica por origem, categoria e base de dados
   - Carregamento sob demanda de dados do Portal da Transparência e dados.gov.br
   - Visualização de metadados e estrutura dos conjuntos de dados

2. **Cruzamento de Dados**
   - Identificação automática de chaves potenciais para cruzamento
   - Suporte a diferentes métodos de junção (inner, left, right, outer)
   - Avaliação de qualidade do cruzamento realizado

3. **Visualização de Dados**
   - Sugestão automática de visualizações adequadas para cada tipo de dado
   - Múltiplos tipos de gráficos (histogramas, boxplots, gráficos de barras, etc.)
   - Exportação de visualizações em diferentes formatos

4. **Assistente com IA**
   - Interpretação de solicitações em linguagem natural
   - Geração de código Python para análises específicas
   - Sugestão de análises relevantes com base nos dados disponíveis

5. **Validação com Usuários**
   - Coleta de feedback sobre usabilidade, desempenho e funcionalidades
   - Identificação de problemas e sugestões de melhorias
   - Métricas de satisfação e intenção de uso futuro

## Estrutura do Projeto

```
app_dados_gov/
├── .streamlit/                # Configurações do Streamlit
├── src/                      # Código fonte da aplicação
│   ├── api/                  # Conectores para APIs
│   │   ├── transparencia.py  # Conector para Portal da Transparência
│   │   └── dados_gov.py      # Conector para dados.gov.br
│   ├── analysis/             # Módulos de análise
│   ├── utils/                # Utilitários
│   │   ├── data_crosser.py   # Funcionalidades de cruzamento
│   │   └── data_visualizer.py # Funcionalidades de visualização
│   └── ai/                   # Integração com IA
│       └── openai_assistant.py # Integração com OpenAI
├── pages/                    # Páginas da aplicação Streamlit
│   ├── 02_Cruzamento_Dados.py # Página de cruzamento de dados
│   └── 07_Validacao_Aplicacao.py # Página de validação com usuários
├── app.py                    # Arquivo principal da aplicação
└── requirements.txt          # Dependências do projeto
```

## Tecnologias Utilizadas

- **Python**: Linguagem principal de desenvolvimento
- **Streamlit**: Framework para interface de usuário
- **Pandas**: Manipulação e análise de dados
- **Plotly**: Visualizações interativas
- **OpenAI API**: Processamento de linguagem natural e geração de código
- **Requests**: Comunicação com APIs externas

## Fontes de Dados Integradas

1. **Portal da Transparência**
   - Bolsa Família e Benefícios Sociais
   - Servidores Públicos
   - Despesas e Orçamento
   - Contratos e Licitações
   - Cadastros (CEIS, CNEP, CEPIM, CEAF)

2. **dados.gov.br**
   - Saúde
   - Educação
   - Economia e Finanças
   - Infraestrutura e Meio Ambiente
   - Agricultura
   - Segurança Pública
   - Cultura e Esporte
   - Administração Pública

## Guia de Instalação e Execução

### Pré-requisitos

- Python 3.8 ou superior
- Pip (gerenciador de pacotes Python)
- Chave de API da OpenAI (opcional, para funcionalidades de IA)
- Chave de API do Portal da Transparência (opcional, para algumas consultas)

### Instalação

1. Clone o repositório:
   ```
   git clone https://github.com/seu-usuario/app-dados-gov.git
   cd app-dados-gov
   ```

2. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```

3. Configure as variáveis de ambiente (opcional):
   ```
   export OPENAI_API_KEY="sua-chave-api-openai"
   export TRANSPARENCIA_API_TOKEN="sua-chave-api-transparencia"
   ```

### Execução

1. Inicie a aplicação Streamlit:
   ```
   streamlit run app.py
   ```

2. Acesse a aplicação no navegador:
   ```
   http://localhost:8501
   ```

## Próximos Passos

1. **Validação com Usuários**
   - Coletar feedback de usuários reais
   - Identificar problemas e priorizar melhorias
   - Ajustar a interface com base nas sugestões recebidas

2. **Expansão de Funcionalidades**
   - Integrar mais fontes de dados governamentais
   - Implementar análises estatísticas mais avançadas
   - Melhorar a integração com IA para sugestões mais precisas

3. **Otimizações de Desempenho**
   - Implementar cache inteligente para consultas frequentes
   - Otimizar processamento de grandes volumes de dados
   - Melhorar tempo de resposta para visualizações complexas

4. **Implantação em Produção**
   - Configurar deploy no Streamlit Cloud
   - Implementar autenticação de usuários (se necessário)
   - Estabelecer monitoramento e logging

## Limitações Atuais

1. **Volume de Dados**
   - Processamento limitado para conjuntos muito grandes
   - Algumas consultas podem ser lentas dependendo da fonte

2. **Cobertura de APIs**
   - Nem todos os endpoints das APIs estão implementados
   - Algumas fontes podem requerer parâmetros específicos

3. **Funcionalidades de IA**
   - Requer chave de API da OpenAI
   - Geração de código pode requerer ajustes manuais em casos complexos

## Contribuição

Para contribuir com o projeto:

1. Faça um fork do repositório
2. Crie uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo LICENSE para detalhes.

## Contato

Para dúvidas ou sugestões, entre em contato através do e-mail: seu-email@exemplo.com
