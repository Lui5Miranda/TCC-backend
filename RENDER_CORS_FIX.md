# 🔴 SOLUÇÃO URGENTE: Erro "TypeError: Failed to fetch"

## ❌ Problema Identificado

Seu frontend em `http://localhost:3000` está tentando se conectar ao backend no Render (`https://tcc-backend-qjeb.onrender.com`), mas **o CORS está bloqueando as requisições**.

## ✅ Solução em 3 Passos

### **PASSO 1: Configure CORS no Render Dashboard**

1. Acesse: https://dashboard.render.com
2. Clique no serviço **tcc-backend**
3. No menu lateral, clique em **Environment**
4. Clique em **Add Environment Variable**

### **PASSO 2: Adicione a variável CORS_ORIGINS**

Configure exatamente assim:

```
Key: CORS_ORIGINS
Value: http://localhost:3000,http://127.0.0.1:3000
```

> ⚠️ **IMPORTANTE:** Use `http://` (sem S) para localhost!

### **PASSO 3: Salve e aguarde o redeploy**

1. Clique em **Save Changes**
2. O Render fará um redeploy automático (~2-3 minutos)
3. Aguarde até ver "Live" no status

## 🧪 Testando após configurar

### 1. Verifique se o backend está funcionando:

Abra esta URL no navegador:
```
https://tcc-backend-qjeb.onrender.com/healthz
```

Deve retornar:
```json
{
  "status": "ok",
  "message": "Servidor de processamento funcionando",
  "timestamp": "..."
}
```

### 2. Teste do frontend:

1. Certifique-se que o frontend está rodando: `npm run dev`
2. Acesse: http://localhost:3000
3. Tente fazer upload de uma imagem
4. Deve funcionar sem erros!

## 📊 Variáveis de Ambiente Necessárias no Render

| Variável | Valor | Status |
|----------|-------|--------|
| `CORS_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000` | ⚠️ **OBRIGATÓRIO** |
| `FLASK_ENV` | `production` | ✅ Recomendado |
| `FLASK_DEBUG` | `false` | ✅ Recomendado |
| `HOST` | `0.0.0.0` | ✅ Recomendado |

## 🚀 Para Deploy em Produção

Quando você fizer deploy do frontend (Vercel, Netlify, etc), adicione a URL dele ao CORS:

```
CORS_ORIGINS=https://seu-frontend.vercel.app,http://localhost:3000,http://127.0.0.1:3000
```

**Exemplo com Vercel:**
```
CORS_ORIGINS=https://tcc-frontend.vercel.app,http://localhost:3000,http://127.0.0.1:3000
```

## ⚠️ Erros Comuns

### ❌ "Mixed Content" Error
**Causa:** Frontend HTTPS tentando acessar backend HTTP
**Solução:** Ambos devem usar HTTPS em produção

### ❌ CORS ainda bloqueando
**Causas possíveis:**
1. Esqueceu de salvar as variáveis no Render
2. Redeploy ainda não terminou (aguarde 2-3 min)
3. Cache do navegador (Ctrl+Shift+R para hard refresh)
4. URL incorreta no CORS (verifique http vs https)

### ❌ 502 Bad Gateway
**Causa:** Backend não iniciou corretamente
**Solução:** Verifique os logs no Render (aba Logs)

## 🔍 Verificando os Logs no Render

Se ainda tiver problemas:

1. Dashboard do Render → tcc-backend
2. Clique em **Logs** no menu lateral
3. Procure por linhas como:
   ```
   CORS restrito para: http://localhost:3000, http://127.0.0.1:3000
   ```

4. Se não aparecer, o CORS não foi configurado corretamente

## 💡 Dica Rápida

Para testar se o CORS está funcionando:

1. Abra o Console do navegador (F12)
2. Cole este código:

```javascript
fetch('https://tcc-backend-qjeb.onrender.com/healthz')
  .then(r => r.json())
  .then(console.log)
  .catch(console.error)
```

Se funcionar, o CORS está OK! ✅
Se der erro CORS, ainda precisa configurar. ❌

## 🆘 Ainda com problemas?

### Checklist de Debug:

- [ ] CORS_ORIGINS configurado no Render
- [ ] Redeploy concluído (status "Live")
- [ ] Backend responde em /healthz
- [ ] Frontend rodando em localhost:3000
- [ ] Cache do navegador limpo (Ctrl+Shift+R)
- [ ] Console do navegador não mostra erros de CORS

### Comandos úteis:

```bash
# Testar backend
curl https://tcc-backend-qjeb.onrender.com/healthz

# Verificar variáveis no Render (via CLI, se tiver)
render env get CORS_ORIGINS
```

---

**Última atualização:** 2025-11-27
**Prioridade:** 🔴 CRÍTICA
**Tempo estimado:** 5 minutos
