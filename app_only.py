import streamlit as st
import requests
import pandas as pd
import time
import os
from io import BytesIO
from utils import validate_excel_file, format_file_size

# Configure page
st.set_page_config(
    page_title="NeuroAudio Processing System",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'processing_status' not in st.session_state:
    st.session_state.processing_status = None
if 'results' not in st.session_state:
    st.session_state.results = None
if 'company_name' not in st.session_state:
    st.session_state.company_name = ""

# API Configuration - User needs to configure this
API_BASE_URL = st.secrets.get("API_BASE_URL", "https://neuro-audio-generator.onrender.com")

def check_api_connection():
    """Check if the FastAPI backend is accessible"""
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def upload_and_process_file(file, company_name):
    """Upload Excel file and process it through the API"""
    try:
        files = {"file": (file.name, file.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        data = {"company_name": company_name}
        
        response = requests.post(
            f"{API_BASE_URL}/process-audio",
            files=files,
            data=data,
            timeout=300
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            error_detail = response.json().get("detail", "Unknown error")
            st.error(f"Falha no processamento: {error_detail}")
            return None
            
    except requests.exceptions.Timeout:
        st.error("Timeout no processamento. O arquivo pode ser muito grande.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Erro de conexão: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Erro inesperado: {str(e)}")
        return None

def download_file(file_type, company_name, filename):
    """Download generated files from the API"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/download/{file_type}/{company_name}/{filename}",
            timeout=30
        )
        
        if response.status_code == 200:
            return response.content
        else:
            st.error(f"Falha no download: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        st.error(f"Erro no download: {str(e)}")
        return None

# Main UI
st.title("🎵 NeuroAudio Processing System")
st.markdown("---")

# Check API connection
if not check_api_connection():
    st.error("⚠️ API Backend não está disponível. Verifique a configuração da API_BASE_URL.")
    st.info("Configure a variável API_BASE_URL nas configurações do Streamlit Cloud.")
    st.stop()

st.success("✅ Conectado à API NeuroAudio")

# Sidebar for file upload and configuration
with st.sidebar:
    st.header("📁 Upload de Arquivo")
    
    # Company name input
    company_name = st.text_input(
        "Nome da Empresa",
        value=st.session_state.company_name,
        placeholder="Digite o nome da sua empresa",
        help="Será usado nos nomes dos arquivos gerados"
    )
    
    if company_name:
        st.session_state.company_name = company_name
    
    # File upload
    uploaded_file = st.file_uploader(
        "Escolha o arquivo Excel",
        type=['xlsx', 'xls'],
        help="Faça upload de um arquivo Excel contendo dados de frequência na coluna THz"
    )
    
    if uploaded_file is not None:
        st.success(f"📄 Arquivo carregado: {uploaded_file.name}")
        st.info(f"Tamanho: {format_file_size(len(uploaded_file.getvalue()))}")
        
        # Validate file
        validation_result = validate_excel_file(uploaded_file)
        if validation_result["valid"]:
            st.success(f"✅ Arquivo Excel válido com {validation_result['row_count']} linhas")
            st.success(f"✅ Encontrada coluna 'THz' com {validation_result['frequency_count']} frequências")
        else:
            st.error(f"❌ {validation_result['error']}")
            uploaded_file = None

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.header("📊 Centro de Processamento")
    
    # File preview
    if uploaded_file is not None and company_name:
        st.subheader("📋 Prévia do Arquivo")
        try:
            df = pd.read_excel(uploaded_file)
            if 'THz' in df.columns:
                # Show first few rows
                st.dataframe(df.head(10), use_container_width=True)
                
                # Show statistics
                thz_data = df['THz'].dropna()
                st.markdown("**Estatísticas das Frequências:**")
                col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
                with col_stat1:
                    st.metric("Total de Frequências", len(thz_data))
                with col_stat2:
                    st.metric("Mín (THz)", f"{thz_data.min():.6f}")
                with col_stat3:
                    st.metric("Máx (THz)", f"{thz_data.max():.6f}")
                with col_stat4:
                    st.metric("Média (THz)", f"{thz_data.mean():.6f}")
                
        except Exception as e:
            st.error(f"Erro ao ler arquivo: {str(e)}")
    
    # Processing section
    st.subheader("🎯 Processamento de Áudio")
    
    # Process button
    if st.button(
        "🚀 Gerar Áudio",
        disabled=not (uploaded_file and company_name),
        use_container_width=True
    ):
        if uploaded_file and company_name:
            st.session_state.processing_status = "processing"
            st.session_state.results = None
            
            with st.spinner("Processando seu arquivo... Isso pode levar alguns minutos."):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Update progress
                for i in range(100):
                    progress_bar.progress(i + 1)
                    if i < 20:
                        status_text.text("📁 Lendo arquivo Excel...")
                    elif i < 40:
                        status_text.text("🔢 Processando frequências...")
                    elif i < 70:
                        status_text.text("🎵 Gerando áudio...")
                    else:
                        status_text.text("✅ Finalizando...")
                    time.sleep(0.1)
                
                # Process the file
                results = upload_and_process_file(uploaded_file, company_name)
                
                if results:
                    st.session_state.results = results
                    st.session_state.processing_status = "completed"
                    st.success("🎉 Processamento concluído com sucesso!")
                    st.rerun()
                else:
                    st.session_state.processing_status = "failed"
    
    # Results section
    if st.session_state.processing_status == "completed" and st.session_state.results:
        st.subheader("📥 Resultados do Processamento")
        
        results = st.session_state.results
        
        # Display results info
        st.info(f"🆔 ID do Processamento: {results.get('aroma_id', 'N/A')}")
        
        # Automatic audio download
        st.markdown("**🎵 Arquivo de Áudio Gerado**")
        audio_filename = results.get('audio_file')
        frequencies_count = results.get('frequencies_processed', 0)
        
        st.success(f"✅ Processamento concluído! {frequencies_count} frequências convertidas em áudio.")
        
        if audio_filename:
            audio_data = download_file("audio", company_name, audio_filename)
            if audio_data:
                st.download_button(
                    label="📥 Baixar Arquivo de Áudio (MP3)",
                    data=audio_data,
                    file_name=audio_filename,
                    mime="audio/mpeg",
                    use_container_width=True
                )
                st.info(f"📄 Arquivo: {audio_filename} | Duração: 30 segundos")
        
        # Clear results button
        if st.button("🔄 Processar Novo Arquivo", use_container_width=True):
            st.session_state.processing_status = None
            st.session_state.results = None
            st.rerun()

with col2:
    st.header("ℹ️ Informações")
    
    # System info
    st.subheader("🔧 Requisitos do Sistema")
    st.markdown("""
    **Formato do Arquivo Excel:**
    - Deve conter uma coluna chamada 'THz'
    - Frequências em unidades Terahertz
    - Formatos suportados: .xlsx, .xls
    
    **Saída:**
    - 🎵 Arquivo de áudio MP3 (30 segundos)
    - 📊 Conversão automática THz para Hz
    - 🎧 Pronto para download automático
    """)
    
    # Processing info
    st.subheader("⚙️ Detalhes do Processamento")
    st.markdown("""
    **Geração de Áudio:**
    - Duração: 30 segundos
    - Taxa de Amostragem: 44.1 kHz
    - Taxa de Bits: 192 kbps
    - Formato: MP3
    
    **Faixa de Frequência:**
    - Mínimo: 18 kHz
    - Máximo: 22 kHz
    - Conversão: THz → Hz
    """)
    
    # Status indicator
    if st.session_state.processing_status:
        st.subheader("📊 Status")
        if st.session_state.processing_status == "processing":
            st.warning("🔄 Processamento em andamento...")
        elif st.session_state.processing_status == "completed":
            st.success("✅ Processamento concluído")
        elif st.session_state.processing_status == "failed":
            st.error("❌ Falha no processamento")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        <p>Copyright Cycor Cibernética 2025 - Todos os direitos reservados</p>
    </div>
    """,
    unsafe_allow_html=True
)
