# Como Configurar a API URL no Render

## Passo a Passo:

### 1. Após o Deploy da API
- Anote a URL da sua API (ex: `https://neuroaudio-api-xyz.onrender.com`)

### 2. Configurar no Frontend
1. No painel do Render, clique no serviço **neuroaudio-app** (frontend)
2. Vá na aba **Environment**
3. Clique em **Add Environment Variable**
4. Preencha:
   - **Key**: `API_BASE_URL`
   - **Value**: `https://neuroaudio-api-xyz.onrender.com` (sua URL da API)
5. Clique em **Save Changes**

### 3. Redeploy Automático
- O Render automaticamente irá fazer redeploy do frontend com a nova variável

## Como Encontrar a URL da API:
1. No painel do Render
2. Clique no serviço **neuroaudio-api**
3. A URL estará no topo da página (ex: `https://neuroaudio-api-xyz.onrender.com`)

## Verificar se Funcionou:
1. Acesse seu app frontend
2. Se aparecer "✅ Conectado à API NeuroAudio" = configurado corretamente
3. Se aparecer "⚠️ API Backend não está disponível" = verificar URL ou API offline

## Exemplo Visual:
```
Frontend URL: https://neuroaudio-app-abc.onrender.com
API URL: https://neuroaudio-api-xyz.onrender.com

Variável de Ambiente:
API_BASE_URL = https://neuroaudio-api-xyz.onrender.com
```

## Dica:
- Aguarde alguns minutos após configurar para o redeploy completar
- A primeira requisição pode demorar se os serviços estiverem hibernando