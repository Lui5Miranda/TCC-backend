# 🔍 Diagnóstico: Por que "Failed to fetch" mesmo com CORS configurado?

## Situação Atual

✅ **Backend no Render está rodando:**
- URL: https://tcc-backend-qjeb.onrender.com
- Status: Live
- CORS configurado: `*` (aceita qualquer origem)

❌ **Frontend ainda apresenta erro:**
```
TypeError: Failed to fetch
```

---

## 🧪 Teste Rápido

Vamos testar se o problema é CORS ou outra coisa.

### **No Console do navegador (F12):**

```javascript
// Teste 1: Health check simples
fetch('https://tcc-backend-qjeb.onrender.com/healthz')
  .then(r => r.json())
  .then(data => console.log('✅ Health OK:', data))
  .catch(err => console.error('❌ Erro:', err))

// Teste 2: POST como o frontend faz
fetch('https://tcc-backend-qjeb.onrender.com/api/process', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({image: 'test', gabarito: {questions: []}})
})
  .then(r => r.json())
  .then(data => console.log('✅ POST OK:', data))
  .catch(err => console.error('❌ Erro:', err))
```

---

## 📊 Possíveis Causas

### 1. ❌ **Render Free Tier Cold Start**
**Sintoma:** Primeira requisição demora muito (30-60s) e dá timeout

**Solução:** Aguarde 30-60 segundos e tente novamente

**Como detectar:** Nos logs do Render, verá:
```
==> Your service was sleeping and has been woken up
```

### 2. ❌ **Mixed Content (HTTP vs HTTPS)**
**Sintoma:** Frontend em HTTPS não pode acessar backend em HTTP

**Diagnóstico:**
- Frontend local: `http://localhost:3000` ✅ Pode acessar HTTPS
- Frontend em produção (HTTPS): Precisa backend HTTPS ✅ Render já usa HTTPS

### 3. ❌ **Request muito grande**
**Sintoma:** Imagem muito grande causa timeout

**Solução:** Testar com imagem pequena primeiro (~100KB)

### 4. ❌ **CORS não está realmente configurado**
**Como verificar:**

Nos logs do Render, procure por:
```
CORS restrito para: *
```

Se aparecer:
```
CORS restrito para: 
```
Ou outro valor, está errado!

---

## ✅ Solução se for Cold Start

O Render Free Tier **hiberna o serviço** após 15 minutos de inatividade. A primeira requisição pode demorar **30-60 segundos**.

### **Opções:**

**A) Aguardar e tentar novamente:**
1. Espere 30-60 segundos
2. Tente fazer upload novamente
3. Deve funcionar após "acordar"

**B) Manter o serviço "acordado" (hack):**

Configure um serviço externo para fazer ping a cada 10 minutos:
- Use: https://cron-job.org
- URL: `https://tcc-backend-qjeb.onrender.com/healthz`
- Intervalo: 10 minutos

---

## 🎯 Teste Definitivo

Execute este código no console do navegador para ver o erro EXATO:

```javascript
const API_URL = 'https://tcc-backend-qjeb.onrender.com';

async function testBackend() {
  console.log('🧪 Testando backend...');
  
  try {
    console.log('📍 Teste 1: Health check');
    const health = await fetch(`${API_URL}/healthz`);
    console.log('✅ Status:', health.status);
    const healthData = await health.json();
    console.log('✅ Data:', healthData);
    
    console.log('\n📍 Teste 2: CORS headers');
    console.log('CORS headers:', health.headers.get('access-control-allow-origin'));
    
    console.log('\n📍 Teste 3: POST /api/process');
    const process = await fetch(`${API_URL}/api/process`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        image: 'data:image/png;base64,test',
        gabarito: {questions: [{id: 1, correctAnswer: 'A'}]}
      })
    });
    console.log('✅ Status:', process.status);
    const processData = await process.json();
    console.log('✅ Response:', processData);
    
  } catch (error) {
    console.error('❌ ERRO CAPTURADO:');
    console.error('Tipo:', error.name);
    console.error('Mensagem:', error.message);
    console.error('Stack:', error.stack);
  }
}

testBackend();
```

---

## 📝 Me envie o resultado

Copie e cole a saída do console aqui para eu diagnosticar o problema exato!

---

**Última atualização:** 2025-11-27 12:08
