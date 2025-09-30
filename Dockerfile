# Usar uma imagem oficial do Python como base
FROM python:3.9-slim

# Define variáveis de ambiente recomendadas
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Define o diretório de trabalho dentro do contêiner
WORKDIR /app

# Copia o arquivo de dependências
COPY requirements.txt .

# Instala TODAS as dependências, incluindo o gunicorn
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código do projeto para o diretório de trabalho
COPY . .

# Expõe a porta 8000, onde o Gunicorn vai rodar
EXPOSE 8000

# O comando para iniciar a aplicação (agora o gunicorn será encontrado)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "Digicoin.wsgi:application"]