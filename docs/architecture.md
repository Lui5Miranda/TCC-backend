# Arquitetura do Sistema de Correção de Gabaritos

## Visão Geral

O sistema é composto por uma arquitetura cliente-servidor com processamento backend em Python e interface frontend em Next.js.

```
┌──────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js)                     │
│  ┌────────────┐  ┌─────────────┐  ┌──────────────────────┐   │
│  │  Upload    │  │  Gabarito   │  │  Resultados          │   │
│  │  Imagem    │  │  Cadastro   │  │  Visualização        │   │
│  └────────────┘  └─────────────┘  └──────────────────────┘   │
└─────────────────────────┬────────────────────────────────────┘
                          │ HTTP/JSON (REST API)
                          │
┌─────────────────────────▼────────────────────────────────────┐
│                     BACKEND (Python/Flask)                   │
│  ┌──────────────────────────────────────────────────────┐    │
│  │              API Gateway (server.py)                 │    │
│  │  • Validação de entrada                              │    │
│  │  • Roteamento de requisições                         │    │
│  │  • Tratamento de erros                               │    │
│  │  • Logging e monitoramento                           │    │
│  └──────────────────────────────────────────────────────┘    │
│                          │                                   │
│         ┌────────────────┼────────────────┬─────────────┐    │
│         │                │                │             │    │
│  ┌──────▼─────┐  ┌───────▼───────┐  ┌───▼────────┐  ┌─▼────┐ │
│  │   Image    │  │   Gabarito    │  │   Cache    │  │Config│ │
│  │ Processor  │  │   Generator   │  │  Manager   │  │      │ │
│  └────────────┘  └───────────────┘  └────────────┘  └──────┘ │
│        │                                    │                │
│  [ OpenCV ]                           [ LRU Cache ]          │
└──────────────────────────────────────────────────────────────┘
```

## Componentes Principais

### 1. API Gateway (server.py)

**Responsabilidades:**
- Gerenciar rotas HTTP
- Validar requisições
- Coordenar componentes
- Retornar respostas estruturadas
- Logging centralizado

**Endpoints:**
- `POST /api/process` - Processamento de imagens
- `POST /api/generate-gabarito` - Geração de PDFs
- `GET /api/health` - Health check
- `GET /api/cache/stats` - Estatísticas do cache
- `POST /api/compare` - Comparação de respostas

### 2. Image Processor (image_processor.py)

**Responsabilidades:**
- Detectar marcadores de alinhamento
- Corrigir perspectiva da imagem
- Identificar bolhas de resposta
- Extrair respostas marcadas
- Calcular confiança das marcações

**Pipeline de Processamento:**
```
Imagem Original
  ↓
[Detect Markers] → Encontra marcadores nos 4 cantos
  ↓
[Align Image] → Corrige perspectiva usando 4-point transform
  ↓
[Detect Bubbles] → Identifica círculos de resposta
  ↓
[Sort Bubbles] → Ordena por posição (coluna → linha)
  ↓
[Extract Answers] → Analisa preenchimento e extrai respostas
  ↓
Respostas + Imagem Anotada
```

### 3. Gabarito Generator (gabarito_generator.py)

**Responsabilidades:**
- Gerar PDFs padronizados em A4
- Desenhar marcadores de alinhamento
- Criar grid de questões com bolhas
- Adaptar layout ao número de questões

**Layout:**
```
┌─────────────────────────────┐
│ ▪                         ▪ │  Marcadores de alinhamento
│                             │
│  01 - Ⓐ Ⓑ Ⓒ Ⓓ Ⓔ         │
│  02 - Ⓐ Ⓑ Ⓒ Ⓓ Ⓔ         │  Grid de questões (3 colunas)
│  ...                        │
│                             │
│ ▪                         ▪ │
└─────────────────────────────┘
```

### 4. Cache Manager (cache_manager.py)

**Responsabilidades:**
- Armazenar resultados processados
- Implementar política LRU
- Gerenciar TTL dos itens
- Fornecer estatísticas

**Estratégia LRU:**
```
Cache (Max: 50 itens, TTL: 30min)
  │
  ├─> [Hash Imagem] → Resultado 1  (timestamp: t1)
  ├─> [Hash Imagem] → Resultado 2  (timestamp: t2)
  └─> [Hash Imagem] → Resultado 3  (timestamp: t3)
        ▲
        │ Acesso atualiza timestamp
        │ Item mais antigo é removido quando cheio
```

### 5. Configuration (config.py)

**Responsabilidades:**
- Configuração por ambiente (Dev/Prod/Test)
- Parâmetros de processamento
- Limites de segurança
- Validações

**Ambientes:**
```python
Development:
  - DEBUG = True
  - LOG_LEVEL = DEBUG
  - CORS aberto para localhost

Production:
  - DEBUG = False
  - LOG_LEVEL = WARNING
  - CORS restrito a domínio específico
```

## Fluxo de Dados Completo

### 1. Upload e Processamento
```
[Frontend]
    │ Usuário faz upload de imagem
    ▼
POST /api/process {image, gabarito}
    │
    ▼
[Server: Validação]
    │ • Valida base64
    │ • Verifica dimensões
    │ • Valida gabarito
    ▼
[Cache: Verifica]
    │ Imagem já processada?
    ├─ SIM → Retorna resultado do cache
    │
    └─ NÃO ▼
[Image Processor]
    │ • Alinha imagem
    │ • Detecta bolhas
    │ • Extrai respostas
    ▼
[Server: Comparação]
    │ Compara com gabarito
    ▼
[Cache: Armazena]
    │ Salva resultado
    ▼
[Response]
    │ {answers, score, image}
    ▼
[Frontend]
    Exibe resultados
```

### 2. Geração de Gabarito
```
[Frontend]
    │ Usuário solicita PDF
    ▼
POST /api/generate-gabarito {num_questions}
    │
    ▼
[Server: Validação]
    │ 1 ≤ num_questions ≤ 100?
    ▼
[Gabarito Generator]
    │ • Cria canvas PDF
    │ • Desenha marcadores
    │ • Desenha questões
    │ • Gera buffer
    ▼
[Response]
    │ {pdf_content (base64)}
    ▼
[Frontend]
    Faz download do PDF
```

## Padrões Arquiteturais

### 1. Separation of Concerns
- Cada módulo tem responsabilidade única
- Baixo acoplamento entre componentes
- Alta coesão dentro dos módulos

### 2. Dependency Injection
- Configurações injetadas via config.py
- Facilita testes e substituição

### 3. Error Handling
- Exceções customizadas (exceptions.py)
- Tratamento em camadas
- Mensagens de erro claras

### 4. Caching Strategy
- Cache transparente ao usuário
- Invalidação automática (TTL)
- Thread-safe com locks

## Decisões Técnicas

### Por que Flask?
- Leve e flexível
- Fácil integração com OpenCV
- Ótimo para APIs REST
- Grande ecossistema

### Por que Cache em Memória?
- Latência mínima (<1ms)
- Simples de implementar
- Suficiente para escala esperada
- Evita dependência externa (Redis)

### Por que OpenCV?
- Padrão da indústria para visão computacional
- Excelente performance
- Algoritmos otimizados em C++
- Documentação extensa

### Por que ReportLab para PDF?
- Controle pixel-perfect do layout
- Geração programática
- Suporte a formas geométricas
- Open source e estável

## Escalabilidade

### Horizontal Scaling
```
Load Balancer
  ├─> Backend Instance 1  (Cache local)
  ├─> Backend Instance 2  (Cache local)
  └─> Backend Instance 3  (Cache local)
        ↓
    [Redis Cache] (Opcional - cache compartilhado)
```

### Otimizações Futuras
1. **Cache Distribuído:** Migrar para Redis
2. **Processamento Assíncrono:** Celery + RabbitMQ
3. **CDN:** Servir PDFs gerados
4. **Database:** Persistir histórico de correções
5. **Queue:** Fila de processamento para múltiplas imagens

## Segurança

### Camadas de Proteção
```
┌────────────────────────┐
│  1. HTTPS (TLS)        │  Criptografia em trânsito
├────────────────────────┤
│  2. CORS               │  Proteção cross-origin
├────────────────────────┤
│  3. Input Validation   │  Sanitização de dados
├────────────────────────┤
│  4. Rate Limiting      │  Proteção contra DDoS
├────────────────────────┤
│  5. Error Handling     │  Não vazar informações
└────────────────────────┘
```

### Validações Implementadas
- Tamanho máximo de upload: 64MB
- Tipos de arquivo permitidos
- Dimensões de imagem
- Formato base64
- JSON schema validation

## Monitoramento

### Métricas Rastreadas
- Tempo de processamento por etapa
- Taxa de sucesso/falha
- Hit rate do cache
- Uso de memória
- Erros por tipo

### Logging Estruturado
```python
logger.info(
    f"Processamento concluído: "
    f"{result['total_questions']} questões em {duration}s"
)
```

## Deployment

### Ambiente de Produção (Render)
```yaml
services:
  - type: web
    name: gabarito-backend
    env: python
    buildCommand: "pip install -r requirements.txt"
    startCommand: "python src/server.py"
    envVars:
      - key: FLASK_ENV
        value: production
```

### Configuração Recomendada
- **CPU:** 2 vCPUs
- **RAM:** 2GB
- **Disco:** 10GB
- **Concorrência:** 4 workers (gunicorn)

## Manutenção

### Atualizações de Dependências
```bash
# Verificar vulnerabilidades
pip-audit

# Atualizar pacotes
pip install -U <package>

# Testar regressão
pytest tests/
```

### Backup e Recovery
- **Logs:** Rotação diária, retenção 30 dias
- **Cache:** Rebuild automático após restart
- **Config:** Versionado no git
