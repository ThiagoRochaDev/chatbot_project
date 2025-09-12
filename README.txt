# Projetos de TCC em NLP

Este diretório contém dois protótipos simples para TCC em NLP:

## 1. Chatbot RAG (simples)
Protótipo de chatbot baseado em Recuperação de Informações. Ele consulta uma base de conhecimento textual e retorna a resposta mais semelhante à pergunta do usuário.

- Arquivo: `rag_chatbot.py`
- Base de conhecimento: `knowledge_base/`

## 2. Classificador de Intenções
Protótipo de um sistema que classifica perguntas do usuário em categorias (intenções) pré-definidas.

- Arquivo: `intent_classifier.py`

## Como rodar

1) Chatbot RAG:
```
python rag_chatbot.py
```

2) Classificador de Intenções:
```
python intent_classifier.py
```

## Dependências opcionais
Ambos funcionam apenas com Python padrão. Para melhor desempenho:
```
pip install scikit-learn
```
