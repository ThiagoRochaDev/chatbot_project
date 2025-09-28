import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk

# Baixar stopwords do NLTK (só precisa rodar uma vez)
nltk.download('stopwords')
from nltk.corpus import stopwords

# Stopwords em português
stop_words_pt = stopwords.words('portuguese')

# Caminho da base de conhecimento
BASE_DIR = os.path.join(os.path.dirname(__file__), "knowledge_base")

def load_documents():
    docs = {}
    for fname in os.listdir(BASE_DIR):
        path = os.path.join(BASE_DIR, fname)
        with open(path, "r", encoding="utf-8") as f:
            docs[fname] = f.read()
    return docs

def chatbot():
    docs = load_documents()
    filenames = list(docs.keys())
    corpus = list(docs.values())

    # Cria vetores TF-IDF para todos os documentos
    vectorizer = TfidfVectorizer(stop_words=stop_words_pt)
    doc_vectors = vectorizer.fit_transform(corpus)

    print("Chatbot RAG iniciado! Digite 'sair' para encerrar.")

    while True:
        query = input("Você: ").strip().lower()

        # Verifica se o usuário quer sair
        if query in ["sair", "exit", "quit"]:
            print("Encerrando o programa. Até logo!")
            break

        # Vetoriza a query
        query_vector = vectorizer.transform([query])

        # Calcula similaridade
        similarities = cosine_similarity(query_vector, doc_vectors).flatten()

        # Índice do documento mais similar
        best_idx = similarities.argmax()
        best_score = similarities[best_idx]

        if best_score > 0:
            print(f"\n[Documento: {filenames[best_idx]} | Score: {best_score:.2f}]")
            print("Chatbot:", corpus[best_idx][:300], "...\n")
        else:
            print("Chatbot: Desculpe, não encontrei uma resposta.\n")

if __name__ == "__main__":
    chatbot()
