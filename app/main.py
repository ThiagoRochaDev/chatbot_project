import os
import logging
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
import fitz
import json
import pandas as pd
import docx

# OpenTelemetry Imports
from opentelemetry import trace, metrics
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter

nltk.download('stopwords')
from nltk.corpus import stopwords

stop_words_pt = stopwords.words('portuguese')

# Diretório base
BASE_DIR = os.path.dirname(__file__)
KNOWLEDGE_BASE = os.path.join(BASE_DIR, "knowledge_base")

# Configurações do Flask
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = KNOWLEDGE_BASE

# ---------------------------
# OpenTelemetry Configuration
# ---------------------------
# Definir o nome do serviço
resource = Resource.create({
    SERVICE_NAME: "chatbot-app"
})

# Configurar logs
logger_provider = LoggerProvider(resource=resource)
logger_provider.add_log_record_processor(BatchLogRecordProcessor(OTLPLogExporter(endpoint="http://otel-collector:4317")))
handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)
logging.basicConfig(level=logging.INFO, handlers=[handler])

# Configurar traces
provider = TracerProvider(resource=resource)
processor = BatchSpanProcessor(OTLPSpanExporter(endpoint="http://otel-collector:4317"))
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)

# Configurar métricas
reader = PeriodicExportingMetricReader(
    OTLPMetricExporter(endpoint="http://otel-collector:4317")
)
meter_provider = MeterProvider(resource=resource, metric_readers=[reader])
metrics.set_meter_provider(meter_provider)
meter = metrics.get_meter(__name__)
requests_counter = meter.create_counter("requests_total", description="Total number of requests")

# Instrumentar a aplicação Flask
FlaskInstrumentor().instrument_app(app)


# ---------------------------
# Funções para carregar arquivos
# ---------------------------
@tracer.start_as_current_span("load_pdf")
def load_pdf(path):
    text = ""
    try:
        with fitz.open(path) as pdf:
            for page in pdf:
                text += page.get_text()
        logging.info(f"PDF loaded successfully from {path}")
    except Exception as e:
        logging.error(f"Error loading PDF from {path}: {e}")
        text = ""
    return text


@tracer.start_as_current_span("load_json")
def load_json(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logging.info(f"JSON loaded successfully from {path}")
        return json.dumps(data, ensure_ascii=False)
    except Exception as e:
        logging.error(f"Error loading JSON from {path}: {e}")
        return ""


@tracer.start_as_current_span("load_md")
def load_md(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        logging.info(f"Markdown loaded successfully from {path}")
        return content
    except Exception as e:
        logging.error(f"Error loading Markdown from {path}: {e}")
        return ""


@tracer.start_as_current_span("load_excel")
def load_excel(path):
    try:
        df = pd.read_excel(path)
        logging.info(f"Excel loaded successfully from {path}")
        return df.to_string()
    except Exception as e:
        logging.error(f"Error loading Excel from {path}: {e}")
        return ""


@tracer.start_as_current_span("load_docx")
def load_docx(path):
    try:
        document = docx.Document(path)
        content = "\n".join([p.text for p in document.paragraphs])
        logging.info(f"Docx loaded successfully from {path}")
        return content
    except Exception as e:
        logging.error(f"Error loading Docx from {path}: {e}")
        return ""


@tracer.start_as_current_span("load_documents")
def load_documents():
    docs = {}
    for root, _, files in os.walk(KNOWLEDGE_BASE):
        for fname in files:
            path = os.path.join(root, fname)
            ext = fname.lower().split('.')[-1]
            try:
                if ext == "pdf":
                    docs[fname] = load_pdf(path)
                elif ext == "json":
                    docs[fname] = load_json(path)
                elif ext == "md":
                    docs[fname] = load_md(path)
                elif ext in ["xlsx", "xls"]:
                    docs[fname] = load_excel(path)
                elif ext == "docx":
                    docs[fname] = load_docx(path)
                elif ext == "txt":
                    with open(path, 'r', encoding='utf-8') as f:
                        docs[fname] = f.read()
            except Exception as e:
                logging.error(f"Error processing {fname}: {e}")
    return docs


# ---------------------------
# Chatbot usando TF-IDF + Cosine Similarity
# ---------------------------
@tracer.start_as_current_span("get_response")
def get_response(user_input, docs):
    filenames = list(docs.keys())
    corpus = list(docs.values())

    if not corpus:
        return "Base de conhecimento vazia. Por favor, adicione documentos."

    vectorizer = TfidfVectorizer(stop_words=stop_words_pt)
    doc_vectors = vectorizer.fit_transform(corpus)
    query_vector = vectorizer.transform([user_input])

    similarities = cosine_similarity(query_vector, doc_vectors).flatten()
    best_idx = similarities.argmax()
    best_score = similarities[best_idx]

    if best_score > 0.1:
        return f"[{filenames[best_idx]}] {corpus[best_idx][:500]}..."
    else:
        return "Desculpe, não encontrei uma resposta relevante."


# ---------------------------
# Rotas
# ---------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    requests_counter.add(1, {"route": "/"})
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    requests_counter.add(1, {"route": "/chat"})
    user_input = request.json.get("message", "").strip()
    if not user_input:
        logging.warning("Received empty message from user.")
        return jsonify({"response": "Por favor, digite uma mensagem."})

    docs = load_documents()
    response = get_response(user_input, docs)
    logging.info(f"Generated response for user input: '{user_input}'")
    return jsonify({"response": response})


@app.route("/upload", methods=["POST"])
def upload_file():
    requests_counter.add(1, {"route": "/upload"})
    file = request.files.get('file')
    if file:
        filename = secure_filename(file.filename)
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(save_path)
        logging.info(f"File {filename} uploaded successfully.")
        return jsonify({"message": f"Arquivo {filename} enviado com sucesso!"})
    logging.warning("No file received for upload.")
    return jsonify({"message": "Nenhum arquivo recebido."})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)