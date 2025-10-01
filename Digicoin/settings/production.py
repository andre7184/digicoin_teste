import os
from .base import *

DEBUG = False

# --- Configurações para Proxy Reverso (Nginx) ---
# Informa ao Django para confiar nos cabeçalhos enviados pelo proxy.
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

# Ajuda o Django a montar os URLs corretamente quando está em um subdiretório.
# Ele usará o valor da variável de ambiente DJANGO_SCRIPT_NAME que já configuramos.
FORCE_SCRIPT_NAME = os.getenv('DJANGO_SCRIPT_NAME')

# Informa ao Django que a conexão é segura (HTTPS) através do proxy.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

print(">>> Usando configurações de PRODUÇÃO <<<")