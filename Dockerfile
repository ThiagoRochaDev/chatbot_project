# Imagem base
FROM python:3.10-slim

# Diretório de trabalho
WORKDIR /app

# Copia arquivos
COPY requirements.txt .

# Instala dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copia a aplicação
COPY . .

# Expõe a porta
EXPOSE 5000

# Comando padrão
CMD ["python", "app/main.py"]
