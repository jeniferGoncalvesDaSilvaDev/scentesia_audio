import os
import logging
import unicodedata
from typing import List
from io import BytesIO
import base64
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
import numpy as np
import io
import wave
import uuid
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        self.audio_data = None
        
    @staticmethod
    def thz_to_hz(thz):
        """Convert Terahertz to Hertz."""
        if not isinstance(thz, (int, float)) or np.isnan(thz):
            raise ValueError(f"Invalid value: {thz}")
        hz = thz * 1e12
        return min(max(hz, Config.MIN_FREQUENCY_HZ), Config.MAX_FREQUENCY_HZ)
    
    def generate_tone(self, frequency_hz, duration_seconds):
        """Generate sine wave tone using numpy."""
        t = np.linspace(0, duration_seconds, int(Config.SAMPLE_RATE * duration_seconds), False)
        sine_wave = np.sin(2 * np.pi * frequency_hz * t)
        
        # Apply volume (convert from dB to linear scale)
        volume_linear = 10 ** (Config.DEFAULT_VOLUME / 20)
        sine_wave = sine_wave * volume_linear
        
        # Convert to 16-bit PCM
        audio_data = (sine_wave * 32767).astype(np.int16)
        return audio_data
    
    def add_frequencies(self, frequencies_thz):
        """Add frequencies to audio mix."""
        total = len(frequencies_thz)
        logger.info(f"Processing {total} frequencies...")
        
        combined_audio = None
        
        for i, thz in enumerate(frequencies_thz, 1):
            try:
                hz = self.thz_to_hz(thz)
                # Map to audible range
                mapped_hz = ((hz - Config.MIN_FREQUENCY_HZ) % (Config.MAX_FREQUENCY_HZ - Config.MIN_FREQUENCY_HZ)) + Config.MIN_FREQUENCY_HZ
                
                tone = self.generate_tone(mapped_hz, Config.TOTAL_DURATION_SECONDS)
                
                if combined_audio is None:
                    combined_audio = tone.astype(np.float32)
                else:
                    combined_audio = combined_audio + tone.astype(np.float32)
                
                if i % 100 == 0 or i == total:
                    logger.info(f"Progress: {i}/{total}")
            except Exception as e:
                logger.warning(f"Skipping frequency {thz}: {e}")
        
        # Normalize to prevent clipping
        if combined_audio is not None:
            max_val = np.max(np.abs(combined_audio))
            if max_val > 32767:
                combined_audio = (combined_audio / max_val * 32767)
            
            self.audio_data = combined_audio.astype(np.int16)
        
        logger.info("Audio generation completed!")
    
    def save_audio(self, output_path):
        """Export WAV file."""
        if self.audio_data is not None:
            with wave.open(output_path, 'w') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(Config.SAMPLE_RATE)
                wav_file.writeframes(self.audio_data.tobytes())

# Initialize FastAPI
app = FastAPI(title="NeuroAudio API", version="1.0.0")

# Storage for processed files
processed_files = {}

@app.post("/process")
async def process_audio(
    file: UploadFile = File(...),
    company_name: str = Form("Client")
):
    """Process Excel file and generate audio"""
    try:
        job_id = str(uuid.uuid4())
        
        # Read Excel file
        content = await file.read()
        df = pd.read_excel(BytesIO(content))
        
        # Validate required column
        if Config.REQUIRED_EXCEL_COLUMN not in df.columns:
            raise HTTPException(
                status_code=400, 
                detail=f"Column '{Config.REQUIRED_EXCEL_COLUMN}' not found"
            )
        
        # Extract and validate frequencies
        frequencies = df[Config.REQUIRED_EXCEL_COLUMN].dropna().tolist()
        
        if not frequencies:
            raise HTTPException(
                status_code=400,
                detail="No valid frequency data found"
            )
        
        # Generate audio
        logger.info(f"Starting audio generation for {len(frequencies)} frequencies")
        generator = NeuroAudioGenerator()
        generator.add_frequencies(frequencies)
        
        # Create output directory
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filenames
        safe_company = remove_accents(company_name).replace(' ', '_')
        audio_filename = f"{safe_company}_neuroaudio_{job_id[:8]}.wav"
        audio_path = os.path.join(output_dir, audio_filename)
        
        # Save audio
        generator.save_audio(audio_path)
        
        # Store job result
        processed_files[job_id] = {
            "audio_file": audio_filename,
            "company_name": company_name,
            "status": "completed",
            "frequencies_count": len(frequencies)
        }
        
        logger.info(f"Job {job_id} completed successfully")
        
        return {
            "job_id": job_id,
            "status": "completed",
            "audio_file": audio_filename,
            "frequencies_processed": len(frequencies),
            "message": "Audio gerado com sucesso!"
        }
        
    except Exception as e:
        logger.error(f"Processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download/{file_type}/{company_name}/{filename}")
async def download_file(file_type: str, company_name: str, filename: str):
    """Download generated files"""
    try:
        file_path = os.path.join("output", filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        media_type = "audio/wav" if file_type == "audio" else "application/octet-stream"
        
        return FileResponse(
            file_path,
            media_type=media_type,
            filename=filename
        )
        
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status/{job_id}")
async def get_job_status(job_id: str):
    """Job status endpoint"""
    if job_id in processed_files:
        return processed_files[job_id]
    else:
        raise HTTPException(status_code=404, detail="Job not found")

@app.get("/")
async def root():
    return {
        "message": "NeuroAudio API",
        "version": "1.0.0",
        "status": "running"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)