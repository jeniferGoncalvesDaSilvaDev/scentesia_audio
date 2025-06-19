# Deploy NeuroAudio - Guia Completo

## Opção 1: Deploy Apenas Frontend (Streamlit Cloud)

### Arquivos para Deploy:
- `app_only.py` (frontend preparado para Streamlit Cloud)
- `utils.py` (funções auxiliares)
- `pyproject.toml` (dependências)
- `.streamlit/config.toml` (configuração)

### Passos:
1. Faça push do código para seu repositório GitHub
2. Conecte sua conta Streamlit Cloud ao GitHub
3. Selecione o repositório e o arquivo `app_only.py`
4. Configure a variável de ambiente `API_BASE_URL` com a URL da sua API

### Limitação:
- Você precisará hospedar a API separadamente (Railway, Heroku, AWS, etc.)

## Opção 2: Deploy Completo (Recomendado)

### Plataformas que suportam ambos:
- **Railway** (mais fácil)
- **Render**
- **Fly.io**
- **Google Cloud Run**
- **AWS**

### Arquivos incluídos:
- `app.py` (frontend completo)
- `backend.py` (API FastAPI)
- `utils.py` (funções auxiliares)
- Todas as dependências

## Opção 3: Deploy no Replit (Mais Simples)

### Vantagens:
- Tudo já configurado e funcionando
- Deploy em 1 clique
- API e frontend juntos
- Domínio automático (.replit.app)

### Como fazer:
1. Clique em "Deploy" no Replit
2. Escolha "Autoscale Deployment"
3. Confirme o deploy

## Configuração de Secrets (para Streamlit Cloud)

Se usar apenas o frontend, adicione nas configurações:

```toml
[secrets]
API_BASE_URL = "https://sua-api-backend.com"
```

## Recomendação

Para máxima simplicidade, use o deploy do Replit. Está tudo pronto e funcionando perfeitamente.

Para controle total, use Railway + Streamlit Cloud separadamente.