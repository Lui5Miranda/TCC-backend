#!/bin/bash
# Script de deploy para o Render

# Atualiza pip
pip install --upgrade pip

# Instala dependências
pip install -r requirements.txt

# Verifica se está em produção
if [ "$FLASK_ENV" = "production" ]; then
    echo "Iniciando em modo de produção com Gunicorn..."
    # Gunicorn com 4 workers, timeout de 120s para processamento de imagem
    gunicorn --bind 0.0.0.0:$PORT --workers 4 --timeout 120 --access-logfile - --error-logfile - src.server:app
else
    echo "Iniciando em modo de desenvolvimento..."
    python src/server.py
fi
