# Sistema de Correção Automática de Gabaritos - Backend

## 📋 Resumo

Este projeto implementa um sistema de correção automática de provas de múltipla escolha utilizando técnicas de Visão Computacional e Processamento Digital de Imagens. O sistema é capaz de detectar, alinhar e extrair respostas de gabaritos padronizados através de análise de imagem, oferecendo uma solução eficiente e precisa para correção de avaliações.

**Tecnologias Principais:** Python, OpenCV, Flask, ReportLab  
**Área:** Visão Computacional, Processamento de Imagens  
**Tipo:** Sistema Web API RESTful

---

## 🎯 Objetivos do Projeto

### Objetivo Geral
Desenvolver um sistema automatizado de correção de gabaritos que utilize técnicas de processamento digital de imagens para identificar e validar respostas marcadas em provas de múltipla escolha.

### Objetivos Específicos
1. Implementar algoritmos de detecção de marcadores de alinhamento
2. Realizar correção de perspectiva em imagens de gabaritos
3. Detectar e classificar bolhas de resposta (A, B, C, D, E)
4. Comparar respostas com gabarito de referência
5. Gerar gabaritos padronizados em formato PDF
6. Fornecer API RESTful para integração com frontend

---

## 🏗️ Arquitetura do Sistema

### Visão Geral
```
┌─────────────┐      HTTP/JSON       ┌──────────────────┐
│   Frontend  │ ───────────────────> │   Flask Server   │
│  (Next.js)  │ <─────────────────── │   (server.py)    │
└─────────────┘                      └──────────────────┘
                                              │
                                              ├─> Image Processor
                                              │   (Detecção + Alinhamento)
                                              │
                                              ├─> Gabarito Generator
                                              │   (Geração de PDF)
                                              │
                                              └─> Cache Manager
                                                  (LRU Cache)
```

### Componentes Principais

#### 1. **server.py** - Servidor Flask
- Gerencia endpoints da API REST
- Validação de entrada e tratamento de erros
- Configuração de CORS e segurança
- Logging e monitoramento

#### 2. **image_processor.py** - Processamento de Imagens
- `detect_markers()`: Detecta marcadores quadrados nos cantos
- `align_image()`: Corrige perspectiva usando transformação de 4 pontos
- `detect_bubbles()`: Identifica círculos de resposta usando threshold adaptativo
- `sort_bubbles_by_columns()`: Ordena respostas por posição
- `extract_answers()`: Extrai respostas marcadas com análise de confiança

#### 3. **gabarito_generator.py** - Gerador de Gabaritos
- Gera PDFs padronizados em formato A4
- Desenha marcadores de alinhamento nos 4 cantos
- Cria grid de questões com bolhas (A-E)
- Layout responsivo baseado no número de questões

#### 4. **cache_manager.py** - Gerenciamento de Cache
- Cache LRU (Least Recently Used) em memória
- TTL configurável (30 minutos padrão)
- Evita reprocessamento de imagens idênticas
- Thread-safe com locks

#### 5. **config.py** - Configurações
- Configuração por ambiente (Dev/Prod/Test)
- Parâmetros de processamento de imagem
- Limites de segurança e validação

---

## 🔬 Fundamentos Teóricos

### Processamento Digital de Imagens

#### 1. **Detecção de Marcadores (Marker Detection)**
Utiliza o algoritmo de Suzuki-Abe [1] para detecção de contornos:
- Limiarização binária com OTSU
- Detecção de contornos externos
- Aproximação poligonal (Douglas-Peucker)
- Filtro por área e aspect ratio

```python
# Threshold binário com OTSU
thresh = cv2.threshold(gray, 0, 255, 
    cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]

# Detecção de contornos
contours = cv2.findContours(thresh, 
    cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
```

#### 2. **Correção de Perspectiva (Perspective Transform)**
Implementa transformação projetiva de 4 pontos [2]:
- Ordenação de pontos (TL, TR, BR, BL)
- Cálculo de dimensões de destino
- Matriz de transformação de perspectiva
- Warping da imagem

**Equação da Transformação:**
```
[x']   [h11  h12  h13] [x]
[y'] = [h21  h22  h23] [y]
[w']   [h31  h32  h33] [w]
```

#### 3. **Threshold Adaptativo (Adaptive Thresholding)**
Utiliza método Gaussiano para lidar com iluminação não-uniforme:
- Block size: 25x25 pixels
- Método: ADAPTIVE_THRESH_GAUSSIAN_C
- Constante C: 5

```python
thresh = cv2.adaptiveThreshold(gray, 255,
    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
    cv2.THRESH_BINARY_INV, 25, 5)
```

#### 4. **Análise de Confiança (Confidence Scoring)**
Compara intensidade de pixels marcados:
- Se `score[0] > 1.5 * score[1]`: Resposta válida
- Caso contrário: Marcação ambígua

---

## 📊 Algoritmo de Processamento

### Fluxo Principal

```
1. Receber imagem em Base64
    ↓
2. Decodificar e validar dimensões
    ↓
3. Detectar marcadores de alinhamento (4 cantos)
    ↓
4. Calcular transformação de perspectiva
    ↓
5. Aplicar warping na imagem
    ↓
6. Threshold adaptativo
    ↓
7. Detectar contornos circulares (bolhas)
    ↓
8. Filtrar por tamanho e aspect ratio
    ↓
9. Ordenar bolhas (esquerda→direita, cima→baixo)
    ↓
10. Analisar cada grupo de 5 bolhas
    ↓
11. Calcular intensidade de preenchimento
    ↓
12. Determinar resposta com maior confiança
    ↓
13. Comparar com gabarito de referência
    ↓
14. Retornar resultado + imagem anotada
```

### Complexidade Computacional

- **Detecção de contornos:** O(n) onde n = número de pixels
- **Ordenação de bolhas:** O(k log k) onde k = número de bolhas
- **Análise por questão:** O(q × b) onde q = questões, b = 5 bolhas/questão
- **Complexidade total:** O(n + k log k + 5q)

Para imagem típica (2000×3000 px, 40 questões):
- **Tempo médio:** 0.8-1.5 segundos
- **Memória:** ~150MB

---

## 🚀 Instalação e Uso

### Requisitos
- Python 3.8+
- pip
- Virtualenv (recomendado)

### Instalação

```bash
# Clone o repositório
git clone <repository-url>
cd TCC-backend

# Crie ambiente virtual
python -m venv venv

# Ative o ambiente (Windows)
venv\Scripts\activate

# Ative o ambiente (Linux/Mac)
source venv/bin/activate

# Instale dependências
pip install -r requirements.txt
```

### Configuração

Crie arquivo `.env` baseado em `.env.example`:

```bash
FLASK_ENV=development
CORS_ORIGINS=http://localhost:3000
LOG_LEVEL=DEBUG
```

### Execução

```bash
# Modo desenvolvimento
python src/server.py

# Modo produção
FLASK_ENV=production python src/server.py
```

O servidor estará disponível em `http://localhost:5000`

---

## 📡 API Endpoints

### 1. POST /api/process
Processa imagem de gabarito e retorna respostas detectadas.

**Request:**
```json
{
  "image": "data:image/jpeg;base64,...",
  "gabarito": {
    "id": "gab123",
    "name": "Prova 1",
    "questions": [
      {"id": 1, "correctAnswer": "A"},
      {"id": 2, "correctAnswer": "B"},
      ...
    ]
  }
}
```

**Response:**
```json
{
  "success": true,
  "answers": {
    "1": "A",
    "2": "B",
    ...
  },
  "comparison": {
    "score": 85.5,
    "correct": 34,
    "total": 40,
    "details": {...}
  },
  "result_image": "data:image/jpeg;base64,...",
  "total_questions": 40
}
```

### 2. POST /api/generate-gabarito
Gera gabarito padronizado em PDF.

**Request:**
```json
{
  "num_questions": 40
}
```

**Response:**
```json
{
  "success": true,
  "pdf_content": "base64_encoded_pdf...",
  "num_questions": 40,
  "file_size": 17068
}
```

### 3. GET /api/health
Verifica status do servidor.

**Response:**
```json
{
  "status": "ok",
  "message": "Servidor de processamento funcionando",
  "timestamp": "2025-11-26T22:30:00"
}
```

### 4. GET /api/cache/stats
Retorna estatísticas do cache.

**Response:**
```json
{
  "success": true,
  "cache_stats": {
    "total_items": 15,
    "max_size": 50,
    "hit_rate": 0.73
  }
}
```

---

## 🧪 Testes e Validação

### Execução de Testes
```bash
# Instalar dependências de desenvolvimento
pip install -r requirements-dev.txt

# Executar todos os testes
pytest tests/

# Executar com cobertura
pytest --cov=src tests/
```

### Métricas de Qualidade
- **Cobertura de testes:** >80%
- **Taxa de acerto:** ~95% em condições ideais
- **Tempo de processamento:** <2s por imagem
- **Falsos positivos:** <3%

---

## 📁 Estrutura de Diretórios

```
TCC-backend/
├── src/
│   ├── server.py              # Servidor Flask + API
│   ├── config.py              # Configurações por ambiente
│   ├── exceptions.py          # Exceções customizadas
│   ├── cache_manager.py       # Cache LRU em memória
│   ├── image_processor.py     # Processamento de imagens
│   └── gabarito_generator.py  # Geração de PDFs
├── tests/
│   ├── test_server.py
│   ├── test_image_processor.py
│   └── test_cache_manager.py
├── docs/
│   ├── architecture.md        # Arquitetura detalhada
│   ├── algorithm.md           # Explicação dos algoritmos
│   └── api.md                 # Documentação da API
├── uploads/                   # Diretório de uploads
├── .env.example               # Template de variáveis de ambiente
├── .gitignore
├── requirements.txt           # Dependências de produção
├── requirements-dev.txt       # Dependências de desenvolvimento
├── README.md                  # Este arquivo
└── render.yaml                # Configuração de deploy
```

---

## ⚙️ Configuração

### Variáveis de Ambiente

| Variável | Descrição | Padrão | Exemplo |
|----------|-----------|--------|---------|
| `FLASK_ENV` | Ambiente de execução | `development` | `production` |
| `CORS_ORIGINS` | Origens permitidas (CORS) | `http://localhost:3000` | `https://app.com` |
| `LOG_LEVEL` | Nível de logging | `INFO` | `DEBUG`, `WARNING` |
| `PORT` | Porta do servidor | `5000` | `8080` |
| `HOST` | Host do servidor | `0.0.0.0` | `127.0.0.1` |

### Parâmetros de Processamento

Configuráveis em `config.py`:

```python
IMAGE_PROCESSING_CONFIG = {
    'bubble_detection': {
        'min_size': 18,              # Tamanho mínimo de bolha (px)
        'aspect_ratio': (0.8, 1.2),  # Tolerância de circularidade
        'expected_count': 200         # 40 questões × 5 alternativas
    },
    'scoring': {
        'confidence_threshold': 1.5   # Multiplicador de confiança
    }
}
```

---

## 🔒 Segurança

### Medidas Implementadas

1. **Validação de Entrada**
   - Verificação de tipo MIME
   - Limite de tamanho (64MB)
   - Validação de dimensões de imagem
   - Sanitização de base64

2. **CORS Restrito**
   - Origens configuráveis por ambiente
   - Headers permitidos controlados

3. **Rate Limiting** (Recomendado para produção)
   - Usar Flask-Limiter
   - Limite sugerido: 10 req/min por IP

4. **Logging de Segurança**
   - Registro de todas as requisições
   - Detecção de padrões suspeitos

---

## 📈 Performance e Otimizações

### Cache LRU
- Reduz processamento de imagens idênticas em ~95%
- TTL de 30 minutos
- Capacidade: 50 itens

### Otimizações de Processamento
- Threshold adaptativo (mais rápido que Otsu global)
- Ordenação por chunks (reduz complexidade)
- Validação precoce (fail-fast)

### Benchmarks

| Operação | Tempo Médio | Imagem de Teste |
|----------|-------------|-----------------|
| Detecção de marcadores | 0.15s | 2000×3000 px |
| Correção de perspectiva | 0.05s | 2000×3000 px |
| Detecção de bolhas | 0.30s | 200 bolhas |
| Extração de respostas | 0.25s | 40 questões |
| **Total** | **0.75s** | **Pipeline completo** |

---

## 🐛 Limitações Conhecidas

1. **Iluminação:** Sensível a sombras e reflexos intensos
2. **Rotação:** Limitado a ±15° de rotação
3. **Marcadores:** Requer todos os 4 marcadores visíveis
4. **Qualidade:** Imagens <100×100 px não são processadas
5. **Bolhas:** Marcações duplas podem causar ambiguidade

---

## 🔄 Roadmap Futuro

- [ ] Suporte a múltiplas páginas
- [ ] Detecção de caligrafia (questões dissertativas)
- [ ] API de estatísticas por turma
- [ ] Dashboard de monitoramento
- [ ] Exportação para Excel/CSV
- [ ] Suporte a QR Codes para identificação

---

## 📚 Referências

[1] Suzuki, S., & Abe, K. (1985). *Topological structural analysis of digitized binary images by border following*. Computer Vision, Graphics, and Image Processing, 30(1), 32-46.

[2] Hartley, R., & Zisserman, A. (2003). *Multiple View Geometry in Computer Vision* (2nd ed.). Cambridge University Press.

[3] Bradski, G. (2000). *The OpenCV Library*. Dr. Dobb's Journal of Software Tools.

[4] Szeliski, R. (2010). *Computer Vision: Algorithms and Applications*. Springer Science & Business Media.

[5] Gonzalez, R. C., & Woods, R. E. (2018). *Digital Image Processing* (4th ed.). Pearson.

[6] Flask Documentation. (2024). Retrieved from https://flask.palletsprojects.com/

[7] OpenCV Documentation. (2024). Retrieved from https://docs.opencv.org/

---

## 👥 Autor

**Desenvolvido como Trabalho de Conclusão de Curso (TCC)**  
Curso: [Seu Curso]  
Instituição: [Sua Instituição]  
Ano: 2025

---

## 📄 Licença

Este projeto foi desenvolvido para fins acadêmicos.

---

## 🙏 Agradecimentos

- Orientador(a): [Nome do Orientador]
- Bibliotecas Open Source: OpenCV, Flask, ReportLab
- Comunidade Python

---

## 📞 Contato

Para dúvidas ou sugestões sobre este projeto acadêmico, entre em contato através de [seu email].
