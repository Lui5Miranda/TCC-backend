# API Documentation - Servidor de Processamento de Gabaritos

## Visão Geral

Esta API fornece endpoints para processamento de imagens de gabaritos e comparação de respostas. O servidor utiliza OpenCV para análise de imagens e detecção de bolhas marcadas.

## Base URL

```
http://localhost:5000
```

## Autenticação

Atualmente não há autenticação implementada. Em produção, considere implementar autenticação JWT ou similar.

## Endpoints

### 1. Health Check

**GET** `/api/health`

Verifica se o servidor está funcionando.

#### Resposta de Sucesso (200)

```json
{
  "status": "ok",
  "message": "Servidor de processamento funcionando",
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

---

### 2. Processar Imagem

**POST** `/api/process`

Processa uma imagem de gabarito e extrai as respostas marcadas.

#### Headers

```
Content-Type: application/json
```

#### Corpo da Requisição

```json
{
  "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQ..."
}
```

#### Parâmetros

| Campo   | Tipo   | Obrigatório | Descrição                                             |
| ------- | ------ | ----------- | ----------------------------------------------------- |
| `image` | string | Sim         | Imagem codificada em base64 com prefixo `data:image/` |

#### Validações

- **Formato**: Deve ser uma string base64 válida com prefixo `data:image/`
- **Tipos suportados**: PNG, JPG, JPEG, GIF, BMP, TIFF
- **Tamanho máximo**: 16MB
- **Dimensões**: Mínimo 100x100px, máximo 4000x4000px

#### Resposta de Sucesso (200)

```json
{
  "success": true,
  "answers": {
    "1": "A",
    "2": "B",
    "3": "C",
    "4": "DUVIDA / NULA",
    "5": "D"
  },
  "result_image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQ...",
  "total_questions": 40
}
```

#### Resposta de Erro (400)

```json
{
  "success": false,
  "error": "Imagem inválida: Formato de imagem inválido"
}
```

#### Resposta de Erro (500)

```json
{
  "success": false,
  "error": "Erro interno do servidor"
}
```

---

### 3. Estatísticas do Cache

**GET** `/api/cache/stats`

Obtém estatísticas do cache de processamento de imagens.

#### Resposta de Sucesso (200)

```json
{
  "success": true,
  "cache_stats": {
    "total_items": 15,
    "active_items": 12,
    "max_size": 50,
    "ttl_seconds": 1800,
    "hit_rate": 0.75
  }
}
```

---

### 4. Gerar Gabarito Padronizado

**POST** `/api/generate-gabarito`

Gera um gabarito padronizado em PDF com o número de questões especificado.

#### Headers

```
Content-Type: application/json
```

#### Corpo da Requisição

```json
{
  "num_questions": 40
}
```

#### Parâmetros

| Campo           | Tipo | Obrigatório | Descrição                  |
| --------------- | ---- | ----------- | -------------------------- |
| `num_questions` | int  | Sim         | Número de questões (1-100) |

#### Validações

- Número de questões deve ser um inteiro entre 1 e 100
- O gabarito é gerado em formato A4 otimizado para leitura automática

#### Resposta de Sucesso (200)

```json
{
  "success": true,
  "pdf_content": "JVBERi0xLjQKJdPr6eEKMSAwIG9iago8PAovVHlwZSAvQ2F0YWxvZwovUGFnZXMgMiAwIFIKPj4KZW5kb2JqCjIgMCBvYmoKPDwKL1R5cGUgL1BhZ2VzCi9LaWRzIFszIDAgUl0KL0NvdW50IDEKL01lZGlhQm94IFswIDAgNTk1IDg0Ml0KPj4KZW5kb2JqCjMgMCBvYmoKPDwKL1R5cGUgL1BhZ2UKL1BhcmVudCAyIDAgUgovUmVzb3VyY2VzIDw8Ci9Gb250IDw8Ci9GMSA0IDAgUgo+Pgo+PgovQ29udGVudHMgNSAwIFIKPj4KZW5kb2JqCjQgMCBvYmoKPDwKL1R5cGUgL0ZvbnQKL1N1YnR5cGUgL1R5cGUxCi9CYXNlRm9udCAvSGVsdmV0aWNhCj4+CmVuZG9iago1IDAgb2JqCjw8Ci9MZW5ndGggNDQKPj4Kc3RyZWFtCkJUCi9GMSAxMiBUZgoyNTAgNzAwIFRkCihHQUJBUklUTyBQQURST05JWkFETykKVGQKRVQKZW5kc3RyZWFtCmVuZG9iagp4cmVmCjAgNgowMDAwMDAwMDAwIDY1NTM1IGYKMDAwMDAwMDAwOSAwMDAwMCBuCjAwMDAwMDAwNTggMDAwMDAgbgowMDAwMDAwMTE1IDAwMDAwIG4KMDAwMDAwMDI2OCAwMDAwMCBuCjAwMDAwMDAzNzQgMDAwMDAgbgp0cmFpbGVyCjw8Ci9TaXplIDYKL1Jvb3QgMSAwIFIKPj4Kc3RhcnR4cmVmCjQ4NQolJUVPRgo=",
  "num_questions": 40,
  "file_size": 12345,
  "message": "Gabarito gerado com 40 questões"
}
```

#### Resposta de Erro (400)

```json
{
  "success": false,
  "error": "Número de questões deve ser um inteiro entre 1 e 100"
}
```

#### Resposta de Erro (500)

```json
{
  "success": false,
  "error": "Erro ao gerar gabarito: [detalhes do erro]"
}
```

---

### 5. Comparar Respostas

**POST** `/api/compare`

Compara as respostas do aluno com o gabarito e calcula a pontuação.

#### Headers

```
Content-Type: application/json
```

#### Corpo da Requisição

```json
{
  "student_answers": {
    "1": "A",
    "2": "B",
    "3": "C",
    "4": "D",
    "5": "E"
  },
  "answer_key": {
    "1": "A",
    "2": "B",
    "3": "C",
    "4": "D",
    "5": "E"
  }
}
```

#### Parâmetros

| Campo             | Tipo   | Obrigatório | Descrição                                        |
| ----------------- | ------ | ----------- | ------------------------------------------------ |
| `student_answers` | object | Sim         | Respostas do aluno (número da questão: resposta) |
| `answer_key`      | object | Sim         | Gabarito com as respostas corretas               |

#### Validações

- Ambos os campos devem ser objetos JSON
- O gabarito não pode estar vazio
- Números das questões devem ser inteiros ou strings

#### Resposta de Sucesso (200)

```json
{
  "success": true,
  "score": 80.0,
  "correct": 4,
  "total": 5,
  "details": {
    "1": {
      "student": "A",
      "correct": "A",
      "is_correct": true
    },
    "2": {
      "student": "B",
      "correct": "B",
      "is_correct": true
    },
    "3": {
      "student": "C",
      "correct": "C",
      "is_correct": true
    },
    "4": {
      "student": "D",
      "correct": "D",
      "is_correct": true
    },
    "5": {
      "student": "E",
      "correct": "A",
      "is_correct": false
    }
  }
}
```

#### Resposta de Erro (400)

```json
{
  "success": false,
  "error": "Campo obrigatório ausente: student_answers"
}
```

---

## Códigos de Status HTTP

| Código | Descrição                           |
| ------ | ----------------------------------- |
| 200    | Sucesso                             |
| 400    | Erro de validação (dados inválidos) |
| 500    | Erro interno do servidor            |

## Limitações e Considerações

### Segurança

- **CORS**: Configurado para aceitar apenas requisições de `localhost:3000` e `127.0.0.1:3000`
- **Tamanho de upload**: Limitado a 16MB
- **Tipos de arquivo**: Apenas imagens são aceitas
- **Validação de entrada**: Todas as entradas são validadas antes do processamento

### Performance

- **Processamento síncrono**: O processamento de imagens pode demorar alguns segundos
- **Sem cache**: Cada requisição processa a imagem do zero
- **Limite de dimensões**: Imagens muito grandes podem ser rejeitadas

### Processamento de Imagem

- **Algoritmo**: Utiliza OpenCV para detecção de contornos e bolhas
- **Marcadores**: Espera encontrar 3-4 marcadores para alinhamento
- **Bolhas**: Espera encontrar exatamente 200 bolhas (40 questões × 5 alternativas)
- **Confiança**: Usa um multiplicador de 1.5x para determinar respostas válidas

## Exemplos de Uso

### JavaScript (Frontend)

```javascript
// Processar imagem
const processImage = async (imageBase64) => {
  const response = await fetch("http://localhost:5000/api/process", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      image: imageBase64,
    }),
  });

  const result = await response.json();
  return result;
};

// Gerar gabarito padronizado
const generateGabarito = async (numQuestions) => {
  const response = await fetch("http://localhost:5000/api/generate-gabarito", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      num_questions: numQuestions,
    }),
  });

  const result = await response.json();
  return result;
};

// Comparar respostas
const compareAnswers = async (studentAnswers, answerKey) => {
  const response = await fetch("http://localhost:5000/api/compare", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      student_answers: studentAnswers,
      answer_key: answerKey,
    }),
  });

  const result = await response.json();
  return result;
};
```

### Python (Cliente)

```python
import requests
import base64

# Processar imagem
def process_image(image_path):
    with open(image_path, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')
        image_base64 = f"data:image/jpeg;base64,{image_data}"

    response = requests.post(
        'http://localhost:5000/api/process',
        json={'image': image_base64}
    )

    return response.json()

# Comparar respostas
def compare_answers(student_answers, answer_key):
    response = requests.post(
        'http://localhost:5000/api/compare',
        json={
            'student_answers': student_answers,
            'answer_key': answer_key
        }
    )

    return response.json()
```

## Configuração do Ambiente

### Variáveis de Ambiente

| Variável       | Padrão        | Descrição                                             |
| -------------- | ------------- | ----------------------------------------------------- |
| `FLASK_ENV`    | `development` | Ambiente de execução (development/production/testing) |
| `FLASK_DEBUG`  | `False`       | Modo debug (True/False)                               |
| `PORT`         | `5000`        | Porta do servidor                                     |
| `HOST`         | `0.0.0.0`     | Host do servidor                                      |
| `CORS_ORIGINS` | -             | Origens permitidas para CORS (separadas por vírgula)  |

### Exemplo de Configuração

```bash
# Desenvolvimento
export FLASK_ENV=development
export FLASK_DEBUG=True
export PORT=5000

# Produção
export FLASK_ENV=production
export FLASK_DEBUG=False
export PORT=8080
export CORS_ORIGINS=https://meusite.com,https://app.meusite.com
```

## Troubleshooting

### Problemas Comuns

1. **"Imagem inválida"**: Verifique se a imagem está em base64 válido com prefixo `data:image/`
2. **"Imagem muito pequena/grande"**: Ajuste as dimensões da imagem (mín: 100x100, máx: 4000x4000)
3. **"Não foi possível isolar as 200 bolhas"**: A imagem pode não ter a qualidade necessária ou não ser um gabarito válido
4. **"Encontrados apenas X marcadores"**: A imagem pode não ter os marcadores de alinhamento necessários

### Logs

O servidor gera logs detalhados que podem ajudar no diagnóstico:

```
2024-01-15 10:30:00,123 - __main__ - INFO - Iniciando processamento de imagem
2024-01-15 10:30:01,456 - __main__ - INFO - Imagem decodificada: 1920x1080 pixels
2024-01-15 10:30:02,789 - __main__ - INFO - Processamento concluído: 40 questões detectadas
```
