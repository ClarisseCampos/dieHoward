import os
import sys
import subprocess
from pathlib import Path


class PiperEngine:
    def __init__(self, model_path: str, length_scale: str = "1.4"):
        self.model_path = model_path
        self.length_scale = length_scale

    @staticmethod
    def _resolver_executavel_piper() -> str:
        pasta_python = Path(sys.executable).parent
        nome_bin = "piper.exe" if sys.platform == "win32" else "piper"
        candidato = pasta_python / nome_bin
        return str(candidato) if candidato.exists() else "piper"

    def gerar_audio_com_progresso(self, texto: str, output_path: str, progress_callback=None):
        path_modelo = Path(self.model_path)
        if not path_modelo.exists():
            raise FileNotFoundError(f"Modelo ONNX não encontrado em: {path_modelo.resolve()}")

        # Remove caracteres surrogates inválidos que às vezes vêm na extração de PDFs
        texto_seguro = texto.encode("utf-8", errors="ignore").decode("utf-8")

        comando = [
            self._resolver_executavel_piper(),
            "--model", str(path_modelo),
            "--output_file", output_path,
            "--length_scale", self.length_scale,
        ]

        # Obriga o piper.exe no Windows a ler sys.stdin em UTF-8 (evita fallback cp1252)
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"

        processo = subprocess.Popen(
            comando,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
        )

        if progress_callback:
            progress_callback(0, 0, 1)

        stdout, stderr = processo.communicate(input=texto_seguro)

        if processo.returncode != 0:
            raise RuntimeError(
                f"Erro ao executar o Piper (código {processo.returncode}):\n{stderr.strip()}"
            )

        if progress_callback:
            progress_callback(100, 1, 1)