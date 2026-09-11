import subprocess
from pathlib import Path
from common.normalizer import TextNormalizer

def executar_pipeline_piper(arquivo_entrada: str, arquivo_saida: str):
    path_in = Path("data/input") / arquivo_entrada
    path_out = Path("data/output") / arquivo_saida

    # Lê o mesmo texto compartilhado
    with open(path_in, "r", encoding="utf-8") as f:
        texto_original = f.read()

    normalizer = TextNormalizer()
    texto_tratado = normalizer.processar(texto_original)

    print(f"[DieHoward - Piper] Texto normalizado: {texto_tratado}")

    # Chamada via Subprocess do Piper
    modelo_piper = "engines/piper/models/pt_BR-faber-medium.onnx"
    
    comando = [
        "piper",
        "--model", modelo_piper,
        "--output_file", str(path_out),
        "--length_scale", "1.4"
    ]

    processo = subprocess.Popen(comando, stdin=subprocess.PIPE, text=True)
    processo.communicate(input=texto_tratado)
    print(f"[DieHoward - Piper] Áudio salvo em: {path_out}")

if __name__ == "__main__":
    executar_pipeline_piper("teste.txt", "audio_piper.wav")