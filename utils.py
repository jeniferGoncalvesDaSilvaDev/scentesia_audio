import pandas as pd
import os
from io import BytesIO

def validate_excel_file(uploaded_file):
    """Validate the uploaded Excel file"""
    try:
        # Reset file pointer
        uploaded_file.seek(0)
        
        # Read Excel file
        df = pd.read_excel(uploaded_file)
        
        # Check if THz column exists
        if 'THz' not in df.columns:
            return {
                "valid": False,
                "error": "Excel file must contain a column named 'THz'"
            }
        
        # Check for valid frequency data
        thz_column = df['THz'].dropna()
        if len(thz_column) == 0:
            return {
                "valid": False,
                "error": "Nenhuma frequência válida encontrada na coluna THz"
            }
        
        # Check for numeric data and positive values
        try:
            pd.to_numeric(thz_column, errors='raise')
            positive_count = len(thz_column)
        except ValueError:
            return {
                "valid": False,
                "error": "Coluna THz contém valores não numéricos"
            }
        
        # Reset file pointer for later use
        uploaded_file.seek(0)
        
        return {
            "valid": True,
            "row_count": len(df),
            "frequency_count": positive_count
        }
        
    except Exception as e:
        return {
            "valid": False,
            "error": f"Error reading Excel file: {str(e)}"
        }

def format_file_size(size_bytes):
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 bytes"
    
    size_names = ["bytes", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes = size_bytes / 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def get_api_base_url():
    """Get the API base URL with fallback support"""
    import streamlit as st
    import requests
    
    # List of API URLs to try (in priority order)
    api_urls = []
    
    # Try Streamlit secrets first (for Streamlit Cloud)
    try:
        api_urls.append(st.secrets["general"]["API_BASE_URL"])
    except:
        pass
    
    # Add environment variable
    env_url = os.getenv("API_BASE_URL")
    if env_url:
        api_urls.append(env_url)
    
    # Add default URLs
    api_urls.extend([
        "https://scentesia-audio.onrender.com",
        "http://localhost:8000"  # Local fallback
    ])
    
    # Test each URL and return the first working one
    for url in api_urls:
        try:
            response = requests.get(f"{url}/", timeout=10)
            if response.status_code == 200:
                return url
        except:
            continue
    
    # Return first URL as last resort
    return api_urls[0] if api_urls else "http://localhost:8000"

def sanitize_company_name(company_name):
    """Sanitize company name for use in file paths"""
    # Remove special characters and spaces
    import re
    sanitized = re.sub(r'[^\w\s-]', '', company_name)
    sanitized = re.sub(r'[-\s]+', '_', sanitized)
    return sanitized.strip('_')

def get_file_extension(filename):
    """Get file extension from filename"""
    return os.path.splitext(filename)[1].lower()

def is_valid_excel_extension(filename):
    """Check if file has valid Excel extension"""
    valid_extensions = ['.xlsx', '.xls']
    return get_file_extension(filename) in valid_extensions
