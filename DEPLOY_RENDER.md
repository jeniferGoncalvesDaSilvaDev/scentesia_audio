# Deploy NeuroAudio no Render - Guia Completo

## Pré-requisitos
1. Conta no GitHub
2. Conta no Render (gratuita)
3. Código do projeto no GitHub

## Passo 1: Preparar o Repositório

### Arquivos necessários:
- `backend_render.py` (API otimizada para Render)
- `app.py` (frontend Streamlit)
- `utils.py` (funções auxiliares)
- `render.yaml` (configuração automática)
- `.streamlit/config.toml` (configuração Streamlit)

### Dependências (extrair do pyproject.toml):
```
streamlit>=1.46.0
fastapi>=0.115.13
uvicorn[standard]>=0.34.3
pandas>=2.3.0
requests>=2.32.4
openpyxl>=3.1.5
xlrd>=2.0.2
pydub>=0.25.1
matplotlib>=3.10.3
fpdf2>=2.8.3
numpy>=2.3.0
python-multipart>=0.0.20
```

## Passo 2: Deploy no Render

### Opção A: Deploy Automático (Recomendado)
1. Faça push do código para GitHub
2. Acesse render.com
3. Clique em "New" → "Blueprint"
4. Conecte seu repositório GitHub
5. O Render detectará o arquivo `render.yaml` automaticamente
6. Clique em "Apply"

### Opção B: Deploy Manual

#### Para a API:
1. No Render: "New" → "Web Service"
2. Conecte o repositório GitHub
3. Configurações:
   - **Name**: neuroaudio-api
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python backend_render.py`
   - **Plan**: Free

#### Para o Frontend:
1. No Render: "New" → "Web Service" 
2. Conecte o mesmo repositório
3. Configurações:
   - **Name**: neuroaudio-app
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
   - **Plan**: Free

## Passo 3: Configurar Variáveis de Ambiente

### No serviço Frontend (neuroaudio-app):
- **Variável**: `API_BASE_URL`
- **Valor**: URL da sua API (ex: `https://neuroaudio-api-xxx.onrender.com`)

## Passo 4: Testar o Deploy

1. Aguarde o build completar (5-10 minutos)
2. Acesse a URL do frontend
3. Teste upload de arquivo Excel
4. Verifique download do MP3

## URLs Finais
- **API**: `https://neuroaudio-api-xxx.onrender.com`
- **App**: `https://neuroaudio-app-xxx.onrender.com`

## Características do Plano Gratuito
- 512MB RAM
- Hiberna após 15 minutos de inatividade
- 750 horas/mês de uso
- Builds ilimitados

## Limitações
- Primeira requisição após hibernação pode demorar 30-60 segundos
- Arquivos gerados são temporários (deletados na hibernação)

## Alternativas para Arquivos Permanentes
- Use AWS S3, Google Cloud Storage, ou Cloudinary
- Implemente upload direto para storage externo

## Troubleshooting

### Erro de Build:
- Verifique se todas as dependências estão no requirements.txt
- Confira se os nomes dos arquivos estão corretos

### Erro de Conexão API:
- Verifique se a variável API_BASE_URL está configurada
- Confirme se ambos os serviços estão rodando

### Timeout:
- Normal no primeiro acesso após hibernação
- Aguarde alguns segundos e tente novamente