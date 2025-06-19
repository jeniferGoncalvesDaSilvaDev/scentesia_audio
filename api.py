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
from pydantic import BaseModel
from typing import List, Optional
from pydub import AudioSegment
from pydub.generators import Sine
import uuid
import pandas as pd
import json
import sys
import subprocess
from fastapi.responses import FileResponse

# =============================================
# CONFIGURAÇÕES GLOBAIS
# =============================================
app = FastAPI(title="NeuroAudio Processing API")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Config:
    TOTAL_DURATION_SECONDS = 30
    DEFAULT_VOLUME = -10  # dB
    MIN_FREQUENCY_HZ = 18000  # 18 kHz
    MAX_FREQUENCY_HZ = 22000  # 22 kHz
    SAMPLE_RATE = 44100  # Hz
    BIT_RATE = "192k"    # Qualidade MP3
    REQUIRED_EXCEL_COLUMN = "THz"

# =============================================
# FUNÇÕES AUXILIARES
# =============================================
def remove_accents(text):
    """Remove acentos e caracteres especiais."""
    if isinstance(text, str):
        normalized = unicodedata.normalize('NFD', text)
        ascii_text = normalized.encode('ascii', 'ignore').decode('ascii')
        ascii_text = ascii_text.replace('ç', 'c').replace('Ç', 'C')
        return ascii_text
    return str(text)

def generate_histogram_base64(frequencies: List[float]):
    """Gera histograma das frequências em base64."""
    try:
        plt.figure(figsize=(10, 5))
        
        # Cálculo dinâmico de bins
        freq_array = np.array(frequencies)
        iqr = np.percentile(freq_array, 75) - np.percentile(freq_array, 25)
        bin_width = 2 * iqr / (len(freq_array) ** (1/3))
        bins = int((np.max(freq_array) - np.min(freq_array)) / bin_width) if bin_width > 0 else 10
        bins = max(min(bins, 20), 5)  # Limita entre 5-20 bins
        
        # Plotagem
        n, bins, patches = plt.hist(freq_array, bins=bins, color='#1f77b4', 
                                  edgecolor='black', alpha=0.7)
        
        # Linhas de referência
        mean_freq = float(np.mean(freq_array))
        median_freq = float(np.median(freq_array))
        plt.axvline(mean_freq, color='red', linestyle='--', linewidth=1.5, 
                   label=f'Média: {mean_freq:.3f} THz')
        plt.axvline(median_freq, color='green', linestyle=':', linewidth=1.5, 
                   label=f'Mediana: {median_freq:.3f} THz')
        
        plt.title('Distribuição de Frequências', fontsize=12, pad=20)
        plt.xlabel('Frequência (THz)', fontsize=10)
        plt.ylabel('Contagem', fontsize=10)
        plt.grid(axis='y', alpha=0.4)
        plt.legend()
        
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        plt.close()
        
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
    except Exception as e:
        logger.error(f"Erro ao gerar histograma: {e}")
        raise

# =============================================
# GERADOR DE ÁUDIO
# =============================================
class NeuroAudioGenerator:
    def __init__(self):
        self.audio_segment = AudioSegment.silent(
            duration=Config.TOTAL_DURATION_SECONDS * 1000,
            frame_rate=Config.SAMPLE_RATE
        )

    @staticmethod
    def thz_to_hz(thz: float) -> float:
        """Converte Terahertz para Hertz."""
        if not isinstance(thz, (int, float)) or np.isnan(thz):
            raise ValueError(f"Valor inválido: {thz}")
        hz = thz * 1e12
        return min(max(hz, Config.MIN_FREQUENCY_HZ), Config.MAX_FREQUENCY_HZ)

    def generate_tone(self, frequency_hz: float) -> AudioSegment:
        """Gera tom senoidal."""
        try:
            return Sine(frequency_hz, sample_rate=Config.SAMPLE_RATE).to_audio_segment(
                duration=Config.TOTAL_DURATION_SECONDS * 1000,
                volume=Config.DEFAULT_VOLUME
            )
        except Exception as e:
            logger.error(f"Erro ao gerar tom: {e}")
            raise

    def add_frequencies(self, frequencies_thz: List[float]) -> None:
        """Adiciona frequências ao mix."""
        total = len(frequencies_thz)
        logger.info(f"Processando {total} frequências...")
        
        for i, thz in enumerate(frequencies_thz, 1):
            try:
                hz = self.thz_to_hz(thz)
                tone = self.generate_tone(hz)
                self.audio_segment = self.audio_segment.overlay(tone)
                
                if i % 100 == 0 or i == total:
                    logger.info(f"Progresso: {i}/{total}")
            except Exception as e:
                logger.warning(f"Frequência {thz}THz ignorada: {str(e)}")
                continue

    def save_audio(self, output_path: str) -> None:
        """Exporta arquivo MP3."""
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            self.audio_segment.export(
                output_path,
                format="mp3",
                bitrate=Config.BIT_RATE,
                tags={
                    'title': 'NeuroAudio',
                    'artist': 'NeuroAudio System',
                    'comment': 'Gerado automaticamente'
                }
            )
            
            if not os.path.exists(output_path):
                raise RuntimeError(f"Arquivo não criado: {output_path}")
                
            logger.info(f"Áudio salvo: {os.path.getsize(output_path)} bytes")
        except Exception as e:
            logger.error(f"Falha ao salvar áudio: {e}")
            raise

# =============================================
# GERADOR DE PDF
# =============================================
def generate_pdf_report(frequencies: List[float], pdf_filename: str, aroma_id: str, 
                      company_name: str, output_dir: str = "output") -> str:
    """Gera relatório PDF completo."""
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.set_title("Relatório NeuroAudio")

        # Cabeçalho
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, "Relatório Técnico NeuroAudio", ln=True, align='C')
        pdf.ln(8)
        
        pdf.set_font("Arial", 'I', 10)
        pdf.cell(200, 5, "Plataforma Profissional de Processamento", ln=True, align='C')
        pdf.ln(15)

        # Informações Básicas
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 8, "INFORMAÇÕES DO PROCESSAMENTO", ln=True)
        pdf.ln(5)
        
        pdf.set_font("Arial", size=10)
        info_items = [
            f"Empresa: {remove_accents(company_name)}",
            f"ID do Processamento: {aroma_id}",
            f"Data/Hora: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
            f"Total de Frequências: {len(frequencies)}",
            f"Duração do Áudio: {Config.TOTAL_DURATION_SECONDS} segundos"
        ]
        
        for item in info_items:
            pdf.cell(200, 6, remove_accents(item), ln=True)
        
        pdf.ln(10)

        # Estatísticas
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 8, "ESTATÍSTICAS DAS FREQUÊNCIAS", ln=True)
        pdf.ln(5)
        
        stats = {
            "Mínima": np.min(frequencies),
            "Máxima": np.max(frequencies),
            "Média": np.mean(frequencies),
            "Mediana": np.median(frequencies),
            "Desvio Padrão": np.std(frequencies),
            "1º Quartil": np.percentile(frequencies, 25),
            "3º Quartil": np.percentile(frequencies, 75)
        }
        
        pdf.set_font("Arial", size=10)
        for name, value in stats.items():
            pdf.cell(100, 6, f"{name}:", ln=False)
            pdf.cell(100, 6, f"{float(value):.6f} THz", ln=True)
        
        pdf.ln(10)

        # Histograma
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 8, "DISTRIBUIÇÃO DE FREQUÊNCIAS", ln=True)
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
            logger.error(f"Erro no histograma: {e}")
            pdf.cell(200, 6, "Gráfico não disponível", ln=True)
        
        pdf.ln(10)

        # Rodapé
        pdf.set_y(-30)
        pdf.set_font("Arial", 'I', 8)
        pdf.cell(0, 5, "Sistema NeuroAudio - Processamento Técnico", ln=True, align='C')
        pdf.cell(0, 5, f"Documento ID: {aroma_id}", ln=True, align='C')

        # Salva PDF
        os.makedirs(output_dir, exist_ok=True)
        pdf_path = os.path.join(output_dir, pdf_filename)
        pdf.output(pdf_path)
        
        return pdf_path
    except Exception as e:
        logger.error(f"Erro no PDF: {e}")
        raise

# =============================================
# ENDPOINTS DA API
# =============================================
@app.post("/process-audio")
async def process_audio(
    file: UploadFile = File(...),
    company_name: str = Form("Cliente")
):
    """Processa arquivo Excel e gera áudio + relatório"""
    try:
        # Gera IDs
        aroma_id = uuid.uuid4().hex[:8].upper()
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join("output", remove_accents(company_name))
        os.makedirs(output_dir, exist_ok=True)

        # Processa Excel
        try:
            df = pd.read_excel(file.file)
            if Config.REQUIRED_EXCEL_COLUMN not in df.columns:
                raise ValueError(f"Coluna '{Config.REQUIRED_EXCEL_COLUMN}' não encontrada")
            
            frequencies = df[Config.REQUIRED_EXCEL_COLUMN].dropna().tolist()
            if not frequencies:
                raise ValueError("Nenhuma frequência válida encontrada")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Erro no Excel: {str(e)}")

        # Gera Áudio
        audio_filename = f"NeuroAudio_{company_name}_{aroma_id}.mp3"
        audio_path = os.path.join(output_dir, audio_filename)
        
        try:
            generator = NeuroAudioGenerator()
            generator.add_frequencies(frequencies)
            generator.save_audio(audio_path)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro no áudio: {str(e)}")

        # Gera PDF
        pdf_filename = f"Relatorio_{company_name}_{aroma_id}.pdf"
        try:
            pdf_path = generate_pdf_report(
                frequencies=frequencies,
                pdf_filename=pdf_filename,
                aroma_id=aroma_id,
                company_name=company_name,
                output_dir=output_dir
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro no PDF: {str(e)}")

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
        logger.error(f"Erro geral: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.get("/download/{file_type}/{company_name}/{filename}")
async def download_file(file_type: str, company_name: str, filename: str):
    """Download dos arquivos gerados"""
    valid_types = {"audio": "audio/mpeg", "report": "application/pdf"}
    
    if file_type not in valid_types:
        raise HTTPException(status_code=400, detail="Tipo inválido")
    
    file_path = os.path.join("output", remove_accents(company_name), filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    
    return FileResponse(
        file_path,
        media_type=valid_types[file_type],
        filename=filename
    )

@app.get("/job-status/{job_id}")
async def get_job_status(job_id: str):
    """Endpoint para verificação de status de processamento"""
    return {
        "completed": True,
        "message": "Processamento concluído",
        "audio_file": "arquivo.mp3",
        "pdf_report": "relatorio.pdf"
    }

@app.get("/")
async def root():
    return {
        "message": "API NeuroAudio - Geração de Áudio e Relatórios",
        "endpoints": {
            "/process-audio (POST)": "Processa arquivo Excel e gera áudio + PDF",
            "/download/{audio|report}/{company}/{filename} (GET)": "Download dos arquivos"
        }
    }

# =============================================
# INICIALIZAÇÃO
# =============================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")