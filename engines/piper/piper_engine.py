import re
import subprocess
from pathlib import Path

class PiperEngine:
    def __init__(self, model_path: str, length_scale: str = "1.4"):
        self.model_path = model_path
        self.length_scale = length_scale

    def gerar_audio_com_progresso(self, texto: str, output_path: str, progress_callback=None):
        # 1. Segmenta o texto em frases com base na pontuação
        sentencas = [s.strip() for s in re.split(r'(?<=[.!?])\s+', texto) if s.strip()]
        total_sentencas = len(sentencas) or 1

        comando = [
            "piper",
            "--model", self.model_path,
            "--output_file", output_path,
            "--length_scale", self.length_scale
        ]

        # 2. Inicia o subprocesso do Piper
        processo = subprocess.Popen(comando, stdin=subprocess.PIPE, text=True)

        # 3. Envia frase por frase via stdin
        for i, sentenca in enumerate(sentencas, 1):
            porcentagem = int((i / total_sentencas) * 100)
            
            if progress_callback:
                progress_callback(porcentagem, i, total_sentencas)
                
            processo.stdin.write(sentenca + "\n")
            processo.stdin.flush()

        processo.stdin.close()
        processo.wait()