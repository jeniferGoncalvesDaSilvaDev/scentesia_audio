import streamlit as st
import requests
import pandas as pd
import time
import os
from io import BytesIO
from utils import validate_excel_file, format_file_size, get_api_base_url

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
if 'job_id' not in st.session_state:
    st.session_state.job_id = None
if 'results' not in st.session_state:
    st.session_state.results = None
if 'company_name' not in st.session_state:
    st.session_state.company_name = ""

# API Configuration
API_BASE_URL = get_api_base_url()

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
            timeout=300  # 5 minutes timeout for processing
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            error_detail = response.json().get("detail", "Unknown error")
            st.error(f"Processing failed: {error_detail}")
            return None
            
    except requests.exceptions.Timeout:
        st.error("Processing timeout. The file might be too large or the server is busy.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Network error: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
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
            st.error(f"Download failed: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        st.error(f"Download error: {str(e)}")
        return None

# Main UI
st.title("🎵 NeuroAudio Processing System")
st.markdown("---")

# Check API connection
if not check_api_connection():
    st.error("⚠️ Backend API is not available. Please ensure the FastAPI server is running on port 8000.")
    st.info("To start the backend server, run: `python main.py` in the backend directory")
    st.stop()

st.success("✅ Connected to NeuroAudio API")

# Sidebar for file upload and configuration
with st.sidebar:
    st.header("📁 File Upload")
    
    # Company name input
    company_name = st.text_input(
        "Company Name",
        value=st.session_state.company_name,
        placeholder="Enter your company name",
        help="This will be used in the generated file names and reports"
    )
    
    if company_name:
        st.session_state.company_name = company_name
    
    # File upload
    uploaded_file = st.file_uploader(
        "Choose Excel file",
        type=['xlsx', 'xls'],
        help="Upload an Excel file containing frequency data in THz column"
    )
    
    if uploaded_file is not None:
        st.success(f"📄 File uploaded: {uploaded_file.name}")
        st.info(f"Size: {format_file_size(len(uploaded_file.getvalue()))}")
        
        # Validate file
        validation_result = validate_excel_file(uploaded_file)
        if validation_result["valid"]:
            st.success(f"✅ Valid Excel file with {validation_result['row_count']} rows")
            st.success(f"✅ Found required 'THz' column with {validation_result['frequency_count']} frequencies")
        else:
            st.error(f"❌ {validation_result['error']}")
            uploaded_file = None

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.header("📊 Processing Center")
    
    # File preview
    if uploaded_file is not None and company_name:
        st.subheader("📋 File Preview")
        try:
            df = pd.read_excel(uploaded_file)
            if 'THz' in df.columns:
                # Show first few rows
                st.dataframe(df.head(10), use_container_width=True)
                
                # Show statistics
                thz_data = df['THz'].dropna()
                st.markdown("**Frequency Statistics:**")
                col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
                with col_stat1:
                    st.metric("Total Frequencies", len(thz_data))
                with col_stat2:
                    st.metric("Min (THz)", f"{thz_data.min():.6f}")
                with col_stat3:
                    st.metric("Max (THz)", f"{thz_data.max():.6f}")
                with col_stat4:
                    st.metric("Mean (THz)", f"{thz_data.mean():.6f}")
                
        except Exception as e:
            st.error(f"Error reading file: {str(e)}")
    
    # Processing section
    st.subheader("🎯 Audio Processing")
    
    # Process button
    if st.button(
        "🚀 Generate Audio & Report",
        disabled=not (uploaded_file and company_name),
        use_container_width=True
    ):
        if uploaded_file and company_name:
            st.session_state.processing_status = "processing"
            st.session_state.results = None
            
            with st.spinner("Processing your file... This may take a few minutes."):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Update progress
                for i in range(100):
                    progress_bar.progress(i + 1)
                    if i < 20:
                        status_text.text("📁 Reading Excel file...")
                    elif i < 40:
                        status_text.text("🔢 Processing frequencies...")
                    elif i < 70:
                        status_text.text("🎵 Generating audio...")
                    elif i < 90:
                        status_text.text("📄 Creating PDF report...")
                    else:
                        status_text.text("✅ Finalizing...")
                    time.sleep(0.1)
                
                # Process the file
                results = upload_and_process_file(uploaded_file, company_name)
                
                if results:
                    st.session_state.results = results
                    st.session_state.processing_status = "completed"
                    st.success("🎉 Processing completed successfully!")
                    st.rerun()
                else:
                    st.session_state.processing_status = "failed"
    
    # Results section
    if st.session_state.processing_status == "completed" and st.session_state.results:
        st.subheader("📥 Download Results")
        
        results = st.session_state.results
        
        # Display results info
        st.info(f"🆔 Processing ID: {results.get('aroma_id', 'N/A')}")
        
        # Download buttons
        col_download1, col_download2 = st.columns(2)
        
        with col_download1:
            st.markdown("**🎵 Audio File**")
            audio_filename = results.get('audio_file')
            if audio_filename:
                if st.button("📥 Download Audio (MP3)", use_container_width=True):
                    audio_data = download_file("audio", company_name, audio_filename)
                    if audio_data:
                        st.download_button(
                            label="💾 Save Audio File",
                            data=audio_data,
                            file_name=audio_filename,
                            mime="audio/mpeg",
                            use_container_width=True
                        )
        
        with col_download2:
            st.markdown("**📄 PDF Report**")
            pdf_filename = results.get('pdf_report')
            if pdf_filename:
                if st.button("📥 Download Report (PDF)", use_container_width=True):
                    pdf_data = download_file("report", company_name, pdf_filename)
                    if pdf_data:
                        st.download_button(
                            label="💾 Save PDF Report",
                            data=pdf_data,
                            file_name=pdf_filename,
                            mime="application/pdf",
                            use_container_width=True
                        )
        
        # Clear results button
        if st.button("🔄 Process New File", use_container_width=True):
            st.session_state.processing_status = None
            st.session_state.results = None
            st.session_state.job_id = None
            st.rerun()

with col2:
    st.header("ℹ️ Information")
    
    # System info
    st.subheader("🔧 System Requirements")
    st.markdown("""
    **Excel File Format:**
    - Must contain a column named 'THz'
    - Frequencies should be in Terahertz units
    - Supported formats: .xlsx, .xls
    
    **Output:**
    - 🎵 MP3 audio file (30 seconds)
    - 📄 Detailed PDF report with statistics
    - 📊 Frequency distribution analysis
    """)
    
    # Processing info
    st.subheader("⚙️ Processing Details")
    st.markdown("""
    **Audio Generation:**
    - Duration: 30 seconds
    - Sample Rate: 44.1 kHz
    - Bit Rate: 192 kbps
    - Format: MP3
    
    **Frequency Range:**
    - Minimum: 18 kHz
    - Maximum: 22 kHz
    - Conversion: THz → Hz
    """)
    
    # Status indicator
    if st.session_state.processing_status:
        st.subheader("📊 Status")
        if st.session_state.processing_status == "processing":
            st.warning("🔄 Processing in progress...")
        elif st.session_state.processing_status == "completed":
            st.success("✅ Processing completed")
        elif st.session_state.processing_status == "failed":
            st.error("❌ Processing failed")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        <p>NeuroAudio Processing System v1.0 | Powered by Streamlit & FastAPI</p>
    </div>
    """,
    unsafe_allow_html=True
)
