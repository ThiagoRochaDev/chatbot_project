import os
import re
import math

# Caminho da base de conhecimento
BASE_DIR = os.path.join(os.path.dirname(__file__), "knowledge_base")

def load_documents():
    docs = {}
    for fname in os.listdir(BASE_DIR):
        with open(os.path.join(BASE_DIR, fname), "r", encoding="utf-8") as f:
            docs[fname] = f.read()
    return docs

def simple_tokenize(text):
    return re.findall(r'\w+', text.lower())

def cosine_similarity(vec1, vec2):
    intersection = set(vec1.keys()) & set(vec2.keys())
    numerator = sum([vec1[x] * vec2[x] for x in intersection])

    sum1 = sum([v**2 for v in vec1.values()])
    sum2 = sum([v**2 for v in vec2.values()])
    denominator = math.sqrt(sum1) * math.sqrt(sum2)

    if not denominator:
        return 0.0
    return float(numerator) / denominator

def text_to_vector(text):
    words = simple_tokenize(text)
    vec = {}
    for word in words:
        vec[word] = vec.get(word, 0) + 1
    return vec

def chatbot():
    docs = load_documents()
    print("Chatbot RAG iniciado! Digite 'sair' para encerrar.")

    while True:
        query = input("Você: ")
        if query.lower() in ["sair", "exit", "quit"]:
            break

        query_vec = text_to_vector(query)
        best_score = 0
        best_doc = None

        for name, content in docs.items():
            doc_vec = text_to_vector(content)
            score = cosine_similarity(query_vec, doc_vec)
            if score > best_score:
                best_score = score
                best_doc = content

        if best_doc:
            print("Chatbot:", best_doc[:300], "...")
        else:
            print("Chatbot: Desculpe, não encontrei uma resposta.")

if __name__ == "__main__":
    chatbot()
