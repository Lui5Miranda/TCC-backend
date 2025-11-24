# Backend - Sistema de Correção de Provas

Este diretório contém o backend do sistema de correção automática de provas.

## Estrutura

```
backend/
├── src/                    # Código fonte
│   ├── tcc.py             # Lógica principal de processamento
│   └── server.py          # Servidor Flask
├── requirements.txt       # Dependências Python
└── README.md             # Este arquivo
```

## Como executar

1. Instale as dependências:

```bash
pip install -r requirements.txt
```

2. Execute o servidor:

```bash
python src/server.py
```

O servidor estará disponível em `http://localhost:5000`

## API Endpoints

- `POST /api/process` - Processa uma imagem de prova
- `GET /api/health` - Verifica status do servidor
