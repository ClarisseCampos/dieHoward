import subprocess
from pathlib import Path


class PiperEngine:
    def __init__(self, model_path: str, length_scale: str = "1.4"):
        self.model_path = model_path
        self.length_scale = length_scale

    def gerar_audio_com_progresso(self, texto: str, output_path: str, progress_callback=None):
        path_modelo = Path(self.model_path)
        if not path_modelo.exists():
            raise FileNotFoundError(f"Modelo ONNX não encontrado em: {path_modelo.resolve()}")

        comando = [
            "piper",
            "--model", str(path_modelo),
            "--output_file", output_path,
            "--length_scale", self.length_scale,
        ]

        processo = subprocess.Popen(
            comando,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        if progress_callback:
            progress_callback(0, 0, 1)

        stdout, stderr = processo.communicate(input=texto)

        if processo.returncode != 0:
            raise RuntimeError(
                f"Erro ao executar o Piper (código {processo.returncode}):\n{stderr.strip()}"
            )

        if progress_callback:
            progress_callback(100, 1, 1)