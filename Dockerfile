# --- ESTÁGIO 1: BUILDER ---
# Este estágio serve para instalar as dependências e preparar a aplicação.
# Usamos uma imagem completa do Python para ter as ferramentas de build.
FROM python:3.9-slim as builder

# Define variáveis de ambiente recomendadas para rodar Python no Docker
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Define o diretório de trabalho dentro do contêiner
WORKDIR /app

# Instala as dependências do projeto
# Copiamos o requirements.txt primeiro para aproveitar o cache do Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código do projeto para dentro do contêiner
COPY . .

# Executa o comando 'collectstatic' do Django.
# Isso junta todos os arquivos estáticos (CSS, JS, imagens) em uma única pasta.
# O '--noinput' garante que o comando não fará perguntas interativas.
RUN python manage.py collectstatic --noinput

# --- ESTÁGIO 2: PRODUÇÃO ---
# Este estágio cria a imagem final, que será muito menor e mais segura.
# Usamos a mesma imagem base leve.
FROM python:3.9-slim

# Define o diretório de trabalho
WORKDIR /app

# Copia apenas os arquivos necessários do estágio 'builder', não o código-fonte todo.
# 1. Copia as dependências já instaladas
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
# 2. Copia a pasta de arquivos estáticos que foi gerada pelo 'collectstatic'
COPY --from=builder /app/staticfiles /app/staticfiles
# 3. Copia a pasta de mídia (para uploads de usuários)
COPY --from=builder /app/midia /app/midia
# 4. Copia o código da aplicação
COPY . .

# Expõe a porta 8000, onde o Gunicorn estará rodando.
# O Nginx vai se conectar a esta porta.
EXPOSE 8000

# O comando final que inicia a aplicação em modo de produção usando o Gunicorn.
# Ele aponta para o arquivo 'wsgi.py' do seu projeto 'Digicoin'.
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "Digicoin.wsgi:application"]