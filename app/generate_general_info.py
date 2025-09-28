import os
import json
import logging
import fitz  # PyMuPDF
import pandas as pd
import docx
import pytesseract
from PIL import Image


# Comentários de configuração alternativa (Windows global)
# import pytesseract
#
# # Caminho do executável
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
#
# # Define a pasta tessdata
# import os
# os.environ['TESSDATA_PREFIX'] = r"C:\Program Files\Tesseract-OCR\tessdata"


# ---------------------------
# Configurações Iniciais
# ---------------------------
BASE_DIR = os.path.dirname(__file__)
KNOWLEDGE_BASE = os.path.join(BASE_DIR, "knowledge_base")
BASE_OUTPUT = os.path.join(KNOWLEDGE_BASE, "base")  # Pasta para arquivos separados

# Configuração de logs
logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")

# ---------------------------
# Configuração do Tesseract local
# ---------------------------
TESSERACT_PATH = os.path.join(BASE_DIR, "Tesseract-OCR", "tesseract.exe")
TESSDATA_PATH = os.path.join(BASE_DIR, "Tesseract-OCR", "tessdata")
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
os.environ["TESSDATA_PREFIX"] = TESSDATA_PATH

# ---------------------------
# Funções de conversão
# ---------------------------
def convert_pdf_to_txt(path):
    try:
        text = ""
        with fitz.open(path) as pdf:
            for page_number, page in enumerate(pdf, start=1):
                page_text = page.get_text().strip()
                if not page_text:
                    logging.info(f"Página {page_number} sem texto detectado. Usando OCR...")
                    pix = page.get_pixmap()
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    page_text = pytesseract.image_to_string(img, lang="por")
                text += f"\n{page_text}\n"
        return text
    except Exception as e:
        logging.error(f"Erro ao processar PDF {path}: {e}")
        return ""

def convert_docx_to_txt(path):
    try:
        doc = docx.Document(path)
        return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
    except Exception as e:
        logging.error(f"Erro ao converter DOCX {path}: {e}")
        return ""

def convert_excel_to_txt(path):
    try:
        df = pd.read_excel(path)
        return "\n".join(df.astype(str).agg(' '.join, axis=1))
    except Exception as e:
        logging.error(f"Erro ao converter Excel {path}: {e}")
        return ""

def convert_csv_to_txt(path):
    try:
        df = pd.read_csv(path)
        return "\n".join(df.astype(str).agg(' '.join, axis=1))
    except Exception as e:
        logging.error(f"Erro ao converter CSV {path}: {e}")
        return ""

def convert_json_to_txt(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return json.dumps(data, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"Erro ao converter JSON {path}: {e}")
        return ""

def convert_md_to_txt(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logging.error(f"Erro ao converter Markdown {path}: {e}")
        return ""

def read_txt_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logging.error(f"Erro ao ler TXT {path}: {e}")
        return ""

# ---------------------------
# Função para salvar arquivos em chunks de 500 caracteres
# ---------------------------
def save_chunks_to_base(filename, content, chunk_size=500):
    content = content.strip()
    if not content:
        return
    base_name = os.path.splitext(filename)[0]
    for idx in range(0, len(content), chunk_size):
        chunk = content[idx:idx+chunk_size]
        safe_name = f"{base_name}_part{idx//chunk_size + 1}.txt"
        out_path = os.path.join(BASE_OUTPUT, safe_name)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(chunk)

# ---------------------------
# Função Principal
# ---------------------------
def generate_base():
    if not os.path.exists(BASE_OUTPUT):
        os.makedirs(BASE_OUTPUT)
        logging.info(f"Pasta {BASE_OUTPUT} criada.")

    logging.info("Iniciando conversão de arquivos...")

    file_count = 0

    for root, _, files in os.walk(KNOWLEDGE_BASE):
        for fname in files:
            path = os.path.join(root, fname)
            ext = fname.lower().split('.')[-1]

            # Ignorar a pasta base
            if os.path.basename(root) == "base":
                continue

            logging.info(f"Processando arquivo: {fname}")
            content = ""

            if ext == "pdf":
                content = convert_pdf_to_txt(path)
            elif ext == "docx":
                content = convert_docx_to_txt(path)
            elif ext in ["xls", "xlsx"]:
                content = convert_excel_to_txt(path)
            elif ext == "csv":
                content = convert_csv_to_txt(path)
            elif ext == "json":
                content = convert_json_to_txt(path)
            elif ext == "md":
                content = convert_md_to_txt(path)
            elif ext == "txt":
                content = read_txt_file(path)
            else:
                logging.warning(f"Formato não suportado: {fname}")
                continue

            if content.strip():
                save_chunks_to_base(fname, content, chunk_size=500)
                file_count += 1
            else:
                logging.warning(f"Nenhum texto extraído do arquivo: {fname}")

    logging.info(f"Processamento concluído. {file_count} arquivos processados e salvos em chunks de 500 caracteres.")

# ---------------------------
# Execução
# ---------------------------
if __name__ == "__main__":
    generate_base()
