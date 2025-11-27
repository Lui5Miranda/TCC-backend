# 🔧 Correção Urgente do CORS - Deploy Render

## ✅ Problema Corrigido

Foi identificado e corrigido um bug no arquivo `config.py` que estava causando o erro "TypeError: Failed to fetch".

### 🐛 O que estava errado?

O código não estava tratando corretamente a variável `CORS_ORIGINS` quando configurada como `*` no Render. A tentativa de fazer `.split(',')` em `*` estava causando problemas.

### ✨ O que foi corrigido?

Agora o código verifica explicitamente se `CORS_ORIGINS = *` e trata este caso especialmente.

```python
# ANTES (com bug):
CORS_ORIGINS = os.getenv('CORS_ORIGINS', '').split(',')

# DEPOIS (corrigido):
cors_env = os.getenv('CORS_ORIGINS', '').strip()
if cors_env == '*':
    CORS_ORIGINS = ['*']
elif cors_env:
    CORS_ORIGINS = [origin.strip() for origin in cors_env.split(',') if origin.strip()]
```

## 🚀 Próximos Passos

### 1. Fazer commit e push das alterações

```bash
cd c:\Users\Luis\Desktop\TCC\TCC-backend

# Adicionar alterações
git add src/config.py

# Commit
git commit -m "fix: corrigir parsing do CORS_ORIGINS para suportar wildcard"

# Push para o Render
git push origin main
```

### 2. Aguardar o redeploy no Render

- O Render detectará automaticamente o push
- Iniciará um novo build (~2-3 minutos)
- Aguarde o status mudar para "Live"

### 3. Testar novamente

Após o redeploy:
1. Acesse http://localhost:3000/upload
2. Tente fazer upload de uma imagem
3. Deve funcionar sem erros! ✅

## 📝 Configurações Atuais no Render

Suas variáveis de ambiente estão OK:

| Variável | Valor | Status |
|----------|-------|--------|
| `CORS_ORIGINS` | `*` | ✅ Funcionará após deploy |
| `FLASK_ENV` | `production` | ✅ OK |
| `FLASK_DEBUG` | `false` | ✅ OK |
| `PORT` | `5000` | ✅ OK |

## ⚠️ Recomendação de Segurança

Após testar e confirmar que funciona, **MUDE** o `CORS_ORIGINS` para ser mais restritivo:

```
# Em vez de:
CORS_ORIGINS=*

# Use (quando fizer deploy do frontend):
CORS_ORIGINS=https://seu-frontend.vercel.app,http://localhost:3000
```

O wildcard `*` permite que **qualquer site** acesse sua API, o que não é seguro em produção.

## 🧪 Como Verificar se Funcionou

### Teste 1: Health Check
```bash
curl https://tcc-backend-qjeb.onrender.com/healthz
```

### Teste 2: No Console do Navegador
```javascript
fetch('https://tcc-backend-qjeb.onrender.com/api/health')
  .then(r => r.json())
  .then(data => console.log('✅ Sucesso:', data))
  .catch(err => console.error('❌ Erro:', err))
```

Se retornar `{status: "ok", ...}` sem erro CORS, está funcionando! ✅

---

**Última atualização:** 2025-11-27 11:43
**Arquivo corrigido:** `src/config.py`
**Próxima ação:** Commit + Push
