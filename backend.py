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
                   label=f'Média: {mean_freq:.3f} THz')
        plt.axvline(median_freq, color='green', linestyle=':', linewidth=1.5, 
                   label=f'Mediana: {median_freq:.3f} THz')
        
        plt.title('Distribuição de Frequências', fontsize=14, fontweight='bold')
        plt.xlabel('Frequência (THz)', fontsize=12)
        plt.ylabel('Contagem', fontsize=12)
        plt.grid(axis='y', alpha=0.4)
        plt.legend(fontsize=10)
        
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
        pdf.cell(200, 10, "Relatorio Tecnico NeuroAudio", ln=True, align='C')
        pdf.ln(8)
        
        pdf.set_font("Arial", 'I', 10)
        pdf.cell(200, 5, "Plataforma Profissional de Processamento", ln=True, align='C')
        pdf.ln(15)

        # Basic Information
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 8, "INFORMACOES DO PROCESSAMENTO", ln=True)
        pdf.ln(5)
        
        pdf.set_font("Arial", size=10)
        info_items = [
            f"Empresa: {remove_accents(company_name)}",
            f"ID do Processamento: {aroma_id}",
            f"Data/Hora: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
            f"Total de Frequencias: {len(frequencies)}",
            f"Duracao do Audio: {Config.TOTAL_DURATION_SECONDS} segundos"
        ]
        
        for item in info_items:
            pdf.cell(200, 6, remove_accents(item), ln=True)
        
        pdf.ln(10)

        # Statistics with educational explanations
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 8, "ESTATISTICAS DAS FREQUENCIAS", ln=True)
        pdf.ln(5)
        
        stats = {
            "Minima": np.min(frequencies),
            "Maxima": np.max(frequencies),
            "Media": np.mean(frequencies),
            "Mediana": np.median(frequencies),
            "Desvio Padrao": np.std(frequencies),
            "1º Quartil (Q1)": np.percentile(frequencies, 25),
            "3º Quartil (Q3)": np.percentile(frequencies, 75)
        }
        
        pdf.set_font("Arial", size=10)
        for name, value in stats.items():
            pdf.cell(100, 6, f"{name}:", ln=False)
            pdf.cell(100, 6, f"{float(value):.6f} THz", ln=True)
        
        pdf.ln(8)
        
        # Educational explanations
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(200, 8, "EXPLICACAO DAS ESTATISTICAS", ln=True)
        pdf.ln(3)
        
        pdf.set_font("Arial", size=9)
        explanations = [
            "- MEDIA: Valor central das frequencias. Representa a frequencia 'tipica' do conjunto.",
            "- MEDIANA: Valor que divide os dados ao meio. 50% das frequencias estao abaixo dela.",
            "- DESVIO PADRAO: Mede o quanto as frequencias variam em relacao a media.",
            "  Valores baixos = frequencias concentradas perto da media",
            "  Valores altos = frequencias mais espalhadas",
            "- QUARTIS: Dividem os dados em 4 partes iguais:",
            "  Q1: 25% das frequencias estao abaixo deste valor",
            "  Q3: 75% das frequencias estao abaixo deste valor",
            "- AMPLITUDE: Diferenca entre o maior e menor valor (Max - Min)",
            f"  Sua amplitude: {float(np.max(frequencies) - np.min(frequencies)):.6f} THz"
        ]
        
        for explanation in explanations:
            pdf.cell(200, 4, remove_accents(explanation), ln=True)
        
        pdf.ln(8)

        # Histogram with enhanced explanation
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 8, "DISTRIBUICAO DE FREQUENCIAS (HISTOGRAMA)", ln=True)
        pdf.ln(5)
        
        pdf.set_font("Arial", size=9)
        pdf.cell(200, 4, "O histograma abaixo mostra como as frequencias estao distribuidas:", ln=True)
        pdf.cell(200, 4, "- Barras altas = muitas frequencias naquela faixa", ln=True)
        pdf.cell(200, 4, "- Barras baixas = poucas frequencias naquela faixa", ln=True)
        pdf.cell(200, 4, "- Linha vermelha tracejada = media das frequencias", ln=True)
        pdf.cell(200, 4, "- Linha verde pontilhada = mediana das frequencias", ln=True)
        pdf.ln(5)
        
        try:
            hist_img = generate_histogram_base64(frequencies)
            temp_img = "temp_hist.png"
            with open(temp_img, "wb") as img_file:
                img_file.write(base64.b64decode(hist_img))
            
            pdf.image(temp_img, x=10, y=pdf.get_y(), w=180)
            pdf.ln(85)
            os.remove(temp_img)
            
            # Analysis of distribution
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(200, 6, "ANALISE DA DISTRIBUICAO:", ln=True)
            pdf.set_font("Arial", size=9)
            
            freq_array = np.array(frequencies)
            skewness = float(np.mean(((freq_array - np.mean(freq_array)) / np.std(freq_array)) ** 3))
            
            if abs(skewness) < 0.5:
                distribution_type = "aproximadamente simetrica"
            elif skewness > 0:
                distribution_type = "assimetrica positiva (cauda para a direita)"
            else:
                distribution_type = "assimetrica negativa (cauda para a esquerda)"
            
            pdf.cell(200, 4, f"- Tipo de distribuicao: {distribution_type}", ln=True)
            pdf.cell(200, 4, f"- Concentracao: {len(freq_array)} frequencias em {len(set(freq_array))} valores unicos", ln=True)
            
            # Range analysis
            q1, q3 = np.percentile(freq_array, [25, 75])
            iqr = q3 - q1
            pdf.cell(200, 4, f"- Amplitude interquartil (IQR): {float(iqr):.6f} THz", ln=True)
            pdf.cell(200, 4, "  (50% dos dados estao dentro desta faixa)", ln=True)
            
        except Exception as e:
            logger.error(f"Histogram error: {e}")
            pdf.cell(200, 6, "Grafico nao disponivel", ln=True)
        
        pdf.ln(8)

        # Footer
        pdf.set_y(-30)
        pdf.set_font("Arial", 'I', 8)
        pdf.cell(0, 5, "Sistema NeuroAudio - Processamento Tecnico", ln=True, align='C')
        pdf.cell(0, 5, f"ID do Documento: {aroma_id}", ln=True, align='C')

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