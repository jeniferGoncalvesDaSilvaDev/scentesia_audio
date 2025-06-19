import os
import datetime
import numpy as np
from fpdf import FPDF
import logging
import unicodedata
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydub import AudioSegment
from pydub.generators import Sine
import uuid
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="NeuroAudio Processing API")

class Config:
    TOTAL_DURATION_SECONDS = 30
    DEFAULT_VOLUME = -10
    MIN_FREQUENCY_HZ = 18000
    MAX_FREQUENCY_HZ = 22000
    SAMPLE_RATE = 44100
    BIT_RATE = "192k"
    REQUIRED_EXCEL_COLUMN = "THz"

def remove_accents(text):
    """Remove accents and special characters."""
    if isinstance(text, str):
        normalized = unicodedata.normalize('NFD', text)
        ascii_text = normalized.encode('ascii', 'ignore').decode('ascii')
        return ascii_text.replace('ç', 'c').replace('Ç', 'C')
    return str(text)

def generate_histogram_base64(frequencies):
    """Generate frequency histogram as base64."""
    try:
        plt.figure(figsize=(10, 5))
        freq_array = np.array(frequencies)
        
        # Calculate dynamic bins
        iqr = np.percentile(freq_array, 75) - np.percentile(freq_array, 25)
        bin_width = 2 * iqr / (len(freq_array) ** (1/3))
        bins = int((np.max(freq_array) - np.min(freq_array)) / bin_width) if bin_width > 0 else 10
        bins = max(min(bins, 20), 5)
        
        # Plot histogram
        plt.hist(freq_array, bins=bins, color='#1f77b4', edgecolor='black', alpha=0.7)
        
        # Add reference lines
        mean_freq = float(np.mean(freq_array))
        median_freq = float(np.median(freq_array))
        plt.axvline(mean_freq, color='red', linestyle='--', linewidth=1.5, 
                   label=f'Mean: {mean_freq:.3f} THz')
        plt.axvline(median_freq, color='green', linestyle=':', linewidth=1.5, 
                   label=f'Median: {median_freq:.3f} THz')
        
        plt.title('Frequency Distribution')
        plt.xlabel('Frequency (THz)')
        plt.ylabel('Count')
        plt.grid(axis='y', alpha=0.4)
        plt.legend()
        
        # Save to base64
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        plt.close()
        
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
    except Exception as e:
        logger.error(f"Error generating histogram: {e}")
        raise

class NeuroAudioGenerator:
    def __init__(self):
        self.audio_segment = AudioSegment.silent(
            duration=Config.TOTAL_DURATION_SECONDS * 1000,
            frame_rate=Config.SAMPLE_RATE
        )

    @staticmethod
    def thz_to_hz(thz):
        """Convert Terahertz to Hertz."""
        if not isinstance(thz, (int, float)) or np.isnan(thz):
            raise ValueError(f"Invalid value: {thz}")
        hz = thz * 1e12
        return min(max(hz, Config.MIN_FREQUENCY_HZ), Config.MAX_FREQUENCY_HZ)

    def generate_tone(self, frequency_hz):
        """Generate sine wave tone."""
        try:
            return Sine(frequency_hz, sample_rate=Config.SAMPLE_RATE).to_audio_segment(
                duration=Config.TOTAL_DURATION_SECONDS * 1000,
                volume=Config.DEFAULT_VOLUME
            )
        except Exception as e:
            logger.error(f"Error generating tone: {e}")
            raise

    def add_frequencies(self, frequencies_thz):
        """Add frequencies to audio mix."""
        total = len(frequencies_thz)
        logger.info(f"Processing {total} frequencies...")
        
        for i, thz in enumerate(frequencies_thz, 1):
            try:
                hz = self.thz_to_hz(thz)
                tone = self.generate_tone(hz)
                self.audio_segment = self.audio_segment.overlay(tone)
                
                if i % 100 == 0 or i == total:
                    logger.info(f"Progress: {i}/{total}")
            except Exception as e:
                logger.warning(f"Frequency {thz}THz ignored: {str(e)}")
                continue

    def save_audio(self, output_path):
        """Export MP3 file."""
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            self.audio_segment.export(
                output_path,
                format="mp3",
                bitrate=Config.BIT_RATE,
                tags={
                    'title': 'NeuroAudio',
                    'artist': 'NeuroAudio System',
                    'comment': 'Auto generated'
                }
            )
            
            if not os.path.exists(output_path):
                raise RuntimeError(f"File not created: {output_path}")
                
            logger.info(f"Audio saved: {os.path.getsize(output_path)} bytes")
        except Exception as e:
            logger.error(f"Failed to save audio: {e}")
            raise

def generate_pdf_report(frequencies, pdf_filename, aroma_id, company_name, output_dir="output"):
    """Generate complete PDF report."""
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        # Header
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, "NeuroAudio Technical Report", ln=True, align='C')
        pdf.ln(8)
        
        pdf.set_font("Arial", 'I', 10)
        pdf.cell(200, 5, "Professional Processing Platform", ln=True, align='C')
        pdf.ln(15)

        # Basic Information
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 8, "PROCESSING INFORMATION", ln=True)
        pdf.ln(5)
        
        pdf.set_font("Arial", size=10)
        info_items = [
            f"Company: {remove_accents(company_name)}",
            f"Processing ID: {aroma_id}",
            f"Date/Time: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
            f"Total Frequencies: {len(frequencies)}",
            f"Audio Duration: {Config.TOTAL_DURATION_SECONDS} seconds"
        ]
        
        for item in info_items:
            pdf.cell(200, 6, remove_accents(item), ln=True)
        
        pdf.ln(10)

        # Statistics
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 8, "FREQUENCY STATISTICS", ln=True)
        pdf.ln(5)
        
        stats = {
            "Minimum": np.min(frequencies),
            "Maximum": np.max(frequencies),
            "Mean": np.mean(frequencies),
            "Median": np.median(frequencies),
            "Std Dev": np.std(frequencies),
            "1st Quartile": np.percentile(frequencies, 25),
            "3rd Quartile": np.percentile(frequencies, 75)
        }
        
        pdf.set_font("Arial", size=10)
        for name, value in stats.items():
            pdf.cell(100, 6, f"{name}:", ln=False)
            pdf.cell(100, 6, f"{float(value):.6f} THz", ln=True)
        
        pdf.ln(10)

        # Histogram
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 8, "FREQUENCY DISTRIBUTION", ln=True)
        pdf.ln(5)
        
        try:
            hist_img = generate_histogram_base64(frequencies)
            temp_img = "temp_hist.png"
            with open(temp_img, "wb") as img_file:
                img_file.write(base64.b64decode(hist_img))
            
            pdf.image(temp_img, x=10, y=pdf.get_y(), w=180)
            pdf.ln(90)
            os.remove(temp_img)
        except Exception as e:
            logger.error(f"Histogram error: {e}")
            pdf.cell(200, 6, "Chart not available", ln=True)
        
        pdf.ln(10)

        # Footer
        pdf.set_y(-30)
        pdf.set_font("Arial", 'I', 8)
        pdf.cell(0, 5, "NeuroAudio System - Technical Processing", ln=True, align='C')
        pdf.cell(0, 5, f"Document ID: {aroma_id}", ln=True, align='C')

        # Save PDF
        os.makedirs(output_dir, exist_ok=True)
        pdf_path = os.path.join(output_dir, pdf_filename)
        pdf.output(pdf_path)
        
        return pdf_path
    except Exception as e:
        logger.error(f"PDF error: {e}")
        raise

@app.post("/process-audio")
async def process_audio(
    file: UploadFile = File(...),
    company_name: str = Form("Client")
):
    """Process Excel file and generate audio + report"""
    try:
        # Generate IDs
        aroma_id = uuid.uuid4().hex[:8].upper()
        output_dir = os.path.join("output", remove_accents(company_name))
        os.makedirs(output_dir, exist_ok=True)

        # Process Excel
        try:
            df = pd.read_excel(file.file)
            if Config.REQUIRED_EXCEL_COLUMN not in df.columns:
                raise ValueError(f"Column '{Config.REQUIRED_EXCEL_COLUMN}' not found")
            
            frequencies = df[Config.REQUIRED_EXCEL_COLUMN].dropna().tolist()
            if not frequencies:
                raise ValueError("No valid frequencies found")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Excel error: {str(e)}")

        # Generate Audio
        audio_filename = f"NeuroAudio_{company_name}_{aroma_id}.mp3"
        audio_path = os.path.join(output_dir, audio_filename)
        
        try:
            generator = NeuroAudioGenerator()
            generator.add_frequencies(frequencies)
            generator.save_audio(audio_path)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Audio error: {str(e)}")

        # Generate PDF
        pdf_filename = f"Report_{company_name}_{aroma_id}.pdf"
        try:
            pdf_path = generate_pdf_report(
                frequencies=frequencies,
                pdf_filename=pdf_filename,
                aroma_id=aroma_id,
                company_name=company_name,
                output_dir=output_dir
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"PDF error: {str(e)}")

        return {
            "status": "success",
            "audio_file": audio_filename,
            "pdf_report": pdf_filename,
            "aroma_id": aroma_id,
            "output_dir": output_dir
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"General error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@app.get("/download/{file_type}/{company_name}/{filename}")
async def download_file(file_type: str, company_name: str, filename: str):
    """Download generated files"""
    valid_types = {"audio": "audio/mpeg", "report": "application/pdf"}
    
    if file_type not in valid_types:
        raise HTTPException(status_code=400, detail="Invalid type")
    
    file_path = os.path.join("output", remove_accents(company_name), filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        file_path,
        media_type=valid_types[file_type],
        filename=filename
    )

@app.get("/job-status/{job_id}")
async def get_job_status(job_id: str):
    """Job status endpoint"""
    return {
        "completed": True,
        "message": "Processing completed",
        "audio_file": "file.mp3",
        "pdf_report": "report.pdf"
    }

@app.get("/")
async def root():
    return {
        "message": "NeuroAudio API - Audio and Report Generation",
        "endpoints": {
            "/process-audio (POST)": "Process Excel file and generate audio + PDF",
            "/download/{audio|report}/{company}/{filename} (GET)": "Download files"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)