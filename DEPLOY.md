# Guia de Deploy no Render

## 📋 Configuração Atual

Seu backend TCC está configurado para deploy no Render com as seguintes especificações:

- **Nome do Serviço:** tcc-backend
- **URL:** https://tcc-backend-qjeb.onrender.com
- **Região:** Virginia (US East)
- **Instância:** Free (0.1 CPU, 512 MB RAM)
- **Repositório:** https://github.com/Lui5Miranda/TCC-backend
- **Branch:** main

## ✅ O que já está configurado

1. ✅ **Health Check Endpoint** (`/healthz`) - Implementado
2. ✅ **Porta dinâmica** - Server usa `PORT` do ambiente
3. ✅ **Host correto** - Server bind em `0.0.0.0`
4. ✅ **Gunicorn** - Servidor WSGI para produção
5. ✅ **Dependências** - `requirements.txt` completo

## 🔧 Variáveis de Ambiente no Render

Configure as seguintes variáveis no painel do Render:

### Obrigatórias

| Variável | Valor | Descrição |
|----------|-------|-----------|
| `FLASK_ENV` | `production` | Ambiente de execução |
| `FLASK_DEBUG` | `false` | Desativa debug em produção |
| `HOST` | `0.0.0.0` | Aceita conexões externas |
| `CORS_ORIGINS` | **SEU_FRONTEND_URL** | ⚠️ **IMPORTANTE!** |

### CORS_ORIGINS - ATENÇÃO!

Esta é a variável mais importante! Adicione a URL do seu frontend:

```bash
# Exemplo se seu frontend está em Vercel:
CORS_ORIGINS=https://seu-app.vercel.app,http://localhost:3000

# Exemplo se está em Netlify:
CORS_ORIGINS=https://seu-app.netlify.app,http://localhost:3000

# Múltiplos domínios (separados por vírgula):
CORS_ORIGINS=https://prod.com,https://staging.com,http://localhost:3000
```

### Opcionais (já com valores padrão)

| Variável | Valor Padrão |
|----------|--------------|
| `LOG_LEVEL` | `INFO` |
| `MAX_CONTENT_LENGTH` | `67108864` (64MB) |
| `CACHE_MAX_SIZE` | `50` |
| `CACHE_TTL_SECONDS` | `1800` (30 min) |

## 🚀 Como configurar no Render

### 1. Acesse as Environment Variables

1. Vá para https://dashboard.render.com
2. Selecione seu serviço **tcc-backend**
3. Clique em **Environment** no menu lateral
4. Clique em **Add Environment Variable**

### 2. Adicione as variáveis

Para cada variável da lista acima:
- **Key:** Nome da variável (ex: `FLASK_ENV`)
- **Value:** Valor correspondente
- Clique em **Add**

### 3. Configure CORS

⚠️ **MUITO IMPORTANTE:**

```bash
# ❌ ERRADO (não use a URL do backend):
CORS_ORIGINS=https://tcc-backend-qjeb.onrender.com

# ✅ CORRETO (use a URL do frontend):
CORS_ORIGINS=https://seu-frontend.vercel.app,http://localhost:3000
```

### 4. Salve e Deploy

Após adicionar todas as variáveis, clique em **Save Changes**.
O Render fará um novo deploy automaticamente.

## 📝 Checklist Pré-Deploy

- [ ] Todas as variáveis de ambiente configuradas
- [ ] `CORS_ORIGINS` aponta para o frontend (não backend!)
- [ ] `FLASK_DEBUG=false` em produção
- [ ] Health check path está como `/healthz`
- [ ] Build command: `pip install -r requirements.txt`
- [ ] Start command: `python src/server.py`

## 🧪 Testando o Deploy

### 1. Health Check

```bash
curl https://tcc-backend-qjeb.onrender.com/healthz
```

Resposta esperada:
```json
{
  "status": "ok",
  "message": "Servidor de processamento funcionando",
  "timestamp": "2025-11-27T..."
}
```

### 2. Teste do Frontend

No seu frontend, configure a URL da API:

```javascript
// config.js ou similar
const API_URL = process.env.NODE_ENV === 'production'
  ? 'https://tcc-backend-qjeb.onrender.com'
  : 'http://localhost:5000';
```

### 3. Monitoramento

Acesse os logs no Render:
1. Dashboard do Render
2. Seu serviço **tcc-backend**
3. Aba **Logs**

## ⚠️ Problemas Comuns

### 1. CORS Error

**Sintoma:** `Access to fetch has been blocked by CORS policy`

**Solução:**
- Verifique se `CORS_ORIGINS` inclui a URL exata do frontend
- Certifique-se de usar `https://` (não `http://`) em produção
- Não esqueça de incluir o protocolo (`https://`)

### 2. 502 Bad Gateway

**Possíveis causas:**
- Aplicação não iniciou corretamente
- Porta não configurada (Render define automaticamente)
- Timeout no health check

**Solução:**
- Verifique os logs no Render
- Certifique-se que o server usa `PORT` do ambiente

### 3. Timeout no Deploy

**Causa:** Instância free do Render tem recursos limitados

**Solução:**
- Aguarde alguns minutos
- Verifique se todas as dependências estão em `requirements.txt`

### 4. Imagens muito grandes

**Sintoma:** Erro 413 (Payload Too Large)

**Solução:**
- Verifique `MAX_CONTENT_LENGTH` (padrão: 64MB)
- Comprima imagens no frontend antes do upload

## 🔄 Deploy Manual

Se o auto-deploy não funcionar:

1. Acesse o dashboard do Render
2. Vá até o serviço **tcc-backend**
3. Clique em **Manual Deploy**
4. Selecione a branch `main`
5. Clique em **Deploy**

## 📊 Monitoramento

### Métricas Importantes

- **Response Time:** < 5s para processamento de imagens
- **Memory Usage:** Fique abaixo de 512MB
- **Cache Hit Rate:** Veja em `/api/cache/stats`

### Endpoints de Monitoramento

```bash
# Health check
GET /healthz

# Status do cache
GET /api/cache/stats
```

## 🔐 Segurança

✅ **Já implementado:**
- Validação de tipo de arquivo
- Limite de tamanho de upload
- CORS restrito
- Validação de imagens base64
- Error handling robusto

## 📚 Endpoints Disponíveis

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/process` | Processar gabarito |
| POST | `/api/compare` | Comparar respostas |
| POST | `/api/generate-gabarito` | Gerar PDF |
| GET | `/api/health` | Status do servidor |
| GET | `/healthz` | Health check (Render) |
| GET | `/api/cache/stats` | Estatísticas do cache |

## 🎯 Próximos Passos

Após o deploy:

1. Configure a URL do backend no frontend
2. Teste todos os fluxos da aplicação
3. Monitore os logs por 24h
4. Configure alertas de erro (opcional)
5. Considere upgrade para instância paga se necessário

## 💡 Dicas de Performance

### Free Tier Limitations

- **Sleep após 15 min:** Primeira requisição pode demorar ~30s
- **750 horas/mês:** Suficiente para desenvolvimento
- **512MB RAM:** Limite de processamento simultâneo

### Otimizações

1. **Cache:** Já implementado - reutiliza resultados
2. **Compressão:** Comprima imagens no frontend
3. **Timeout:** Aumentado para 120s no gunicorn
4. **Workers:** 1 worker (limite do free tier)

## 🆘 Suporte

Se encontrar problemas:

1. Verifique os logs no Render
2. Teste o endpoint `/healthz`
3. Valide as variáveis de ambiente
4. Verifique se o CORS está correto
5. Teste localmente primeiro com as mesmas variáveis

---

**Última atualização:** 2025-11-27
**Versão do Python:** 3.9+
**Framework:** Flask 2.3+
