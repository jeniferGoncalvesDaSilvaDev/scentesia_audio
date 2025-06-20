# Setup Completo para Streamlit Cloud

## 1. Configuração de Arquivos

### Arquivo: `.streamlit/config.toml`
```toml
[server]
headless = true
address = "0.0.0.0"
port = 8501
enableCORS = false
enableXsrfProtection = false

[theme]
base = "light"
```

### Arquivo: `packages.txt` (vazio, mas necessário)
```
# System packages for Streamlit Cloud
```

## 2. Secrets no Streamlit Cloud

No painel do Streamlit Cloud, adicione em **Settings > Secrets**:

```toml
[general]
API_BASE_URL = "https://scentesia-audio.onrender.com"
```

## 3. Arquivos para Commit

Certifique-se de que estes arquivos estão no GitHub:
- `app.py`
- `utils.py`
- `requirements.txt`
- `.streamlit/config.toml` (com porta 8501)
- `packages.txt`

## 4. Deploy

1. Acesse [share.streamlit.io](https://share.streamlit.io)
2. Conecte GitHub
3. Selecione repositório
4. Main file: `app.py`
5. Branch: `main`

## 5. Verificação

Após deploy:
- Verificar se aparece "Conectado à API NeuroAudio"
- Testar upload de arquivo Excel
- Confirmar download automático

## Solução de Problemas

Se ainda der erro de porta 8501:
1. Verificar se config.toml tem porta 8501
2. Aguardar alguns minutos para redeploy
3. Verificar logs no painel Streamlit Cloud