# Deploy no Streamlit Cloud

## Passo a Passo:

### 1. Fazer Deploy no Streamlit Cloud
1. Acesse [share.streamlit.io](https://share.streamlit.io)
2. Conecte sua conta GitHub
3. Clique em "New app"
4. Selecione seu repositório: `neuro_audio_generator`
5. Branch: `main`
6. Main file: `app.py`

### 2. Configurar Secrets (IMPORTANTE)
1. No painel do Streamlit Cloud, vá em **Settings**
2. Clique na aba **Secrets**
3. Cole este conteúdo:

```toml
[general]
API_BASE_URL = "https://neuro-audio-generator.onrender.com"
```

4. Clique em **Save**

### 3. Aguardar Deploy
- O deploy demora alguns minutos
- Se der erro, verifique os logs
- O app ficará disponível em: `https://your-app-name.streamlit.app`

## Arquivos Necessários no GitHub:
- `app.py` - Frontend principal
- `.streamlit/config.toml` - Configuração (porta 8501)
- `utils.py` - Funções auxiliares
- `requirements.txt` - Dependências Python

## Estrutura Final:
```
Frontend (Streamlit Cloud): your-app.streamlit.app
↓ conecta via API ↓
Backend (Render): neuro-audio-generator.onrender.com
```

## Teste:
1. Acesse seu app no Streamlit Cloud
2. Verifique se aparece "✅ Conectado à API NeuroAudio"
3. Faça upload de arquivo Excel com coluna THz
4. Download do arquivo WAV deve funcionar automaticamente

## Solução de Problemas:
- Se aparecer "API Backend não disponível": verifique secrets
- Se der erro no upload: API pode estar hibernando (aguarde 30s)
- Se der timeout: arquivo muito grande ou muitas frequências