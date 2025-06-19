import os
import datetime
import numpy as np
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

@app.post("/process-audio")
async def process_audio(
    file: UploadFile = File(...),
    company_name: str = Form("Client")
):
    """Process Excel file and generate audio"""
    try:
        # Generate IDs
        aroma_id = uuid.uuid4().hex[:8].upper()
        output_dir = os.path.join("output", remove_accents(company_name))
        os.makedirs(output_dir, exist_ok=True)

        # Process Excel
        try:
            df = pd.read_excel(file.file)
            
            # Check if file is empty
            if df.empty:
                raise ValueError("Arquivo Excel está vazio")
            
            # Check if THz column exists
            if Config.REQUIRED_EXCEL_COLUMN not in df.columns:
                raise ValueError(f"Coluna '{Config.REQUIRED_EXCEL_COLUMN}' não encontrada no arquivo")
            
            # Get frequencies and validate
            frequencies = df[Config.REQUIRED_EXCEL_COLUMN].dropna().tolist()
            
            # Check if there are any frequencies
            if not frequencies:
                raise ValueError("Nenhuma frequência válida encontrada na coluna THz")
            
            # Validate that frequencies are numeric
            numeric_frequencies = []
            for freq in frequencies:
                try:
                    numeric_freq = float(freq)
                    if numeric_freq <= 0:
                        continue  # Skip zero or negative frequencies
                    numeric_frequencies.append(numeric_freq)
                except (ValueError, TypeError):
                    continue  # Skip non-numeric values
            
            if not numeric_frequencies:
                raise ValueError("Nenhuma frequência numérica válida encontrada (valores devem ser positivos)")
            
            frequencies = numeric_frequencies
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Erro no arquivo Excel: {str(e)}")

        # Generate Audio
        audio_filename = f"NeuroAudio_{company_name}_{aroma_id}.mp3"
        audio_path = os.path.join(output_dir, audio_filename)
        
        try:
            generator = NeuroAudioGenerator()
            generator.add_frequencies(frequencies)
            generator.save_audio(audio_path)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Audio error: {str(e)}")

        return {
            "status": "success",
            "audio_file": audio_filename,
            "aroma_id": aroma_id,
            "output_dir": output_dir,
            "frequencies_processed": len(frequencies)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"General error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@app.get("/download/{file_type}/{company_name}/{filename}")
async def download_file(file_type: str, company_name: str, filename: str):
    """Download generated files"""
    valid_types = {"audio": "audio/mpeg"}
    
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

@app.get("/")
async def root():
    return {
        "message": "NeuroAudio API - Audio Generation",
        "endpoints": {
            "/process-audio (POST)": "Process Excel file and generate audio",
            "/download/audio/{company}/{filename} (GET)": "Download files"
        }
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)