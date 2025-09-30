# Usar uma imagem oficial do Python como base
FROM python:3.9-slim

# Define variáveis de ambiente recomendadas
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Define o diretório de trabalho dentro do contêiner
WORKDIR /app

# Copia e instala as dependências do requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código do projeto para dentro do contêiner
COPY . .

# Executa o comando 'collectstatic' do Django.
# Este passo é essencial e agora está incluído.
RUN python manage.py collectstatic --noinput

# Expõe a porta 8000, onde o Gunicorn estará rodando
EXPOSE 8000

# O comando final que inicia a aplicação com Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "Digicoin.wsgi:application"]