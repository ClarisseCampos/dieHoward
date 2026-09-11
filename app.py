import re
from pathlib import Path
from common.tui import DieHowardTUI, console
from common.normalizer import TextNormalizer
from engines.kokoro.kokoro_engine import KokoroCPUEngine
import subprocess

def main():
    DieHowardTUI.exibir_cabecalho()
    
    # 1. Seleção Interativa do Arquivo
    arquivo_nome = DieHowardTUI.listar_arquivos_input()
    if not arquivo_nome:
        return

    # 2. Seleção Interativa do Motor e Voz
    engine_tipo, voz = DieHowardTUI.selecionar_engine()
    
    path_in = Path("data/input") / arquivo_nome
    path_out = Path("data/output") / f"{Path(arquivo_nome).stem}_{engine_tipo}.wav"

    if engine_tipo == "kokoro":
        with open(path_in, "r", encoding="utf-8", errors="ignore") as f:
            texto = f.read()

        engine = KokoroCPUEngine(
            model_path="engines/kokoro/models/kokoro-v1.0.onnx",
            voices_path="engines/kokoro/models/voices-v1.0.bin"
        )

        with DieHowardTUI.criar_barra_progresso() as progress:
            task = progress.add_task(f"[cyan]Sintetizando Kokoro ({voz})...", total=100)

            def atualizar_barra(porcentagem, atual, total):
                progress.update(task, completed=porcentagem, description=f"[cyan]Kokoro: bloco {atual}/{total} ({porcentagem}%)...")

            engine.gerar_audio_com_progresso(
                texto=texto, 
                output_path=str(path_out), 
                voice=voz, 
                progress_callback=atualizar_barra
            )

    elif engine_tipo == "piper":
        with open(path_in, "r", encoding="utf-8", errors="ignore") as f:
            texto_bruto = f.read()

        normalizer = TextNormalizer()
        texto_tratado = normalizer.processar(texto_bruto)

        # Divide por frases para mensurar progresso do Piper
        sentencas = [s.strip() for s in re.split(r'(?<=[.!?])\s+', texto_tratado) if s.strip()]
        total_sentencas = len(sentencas) or 1

        with DieHowardTUI.criar_barra_progresso() as progress:
            task = progress.add_task("[magenta]Sintetizando com Piper (Faber)...", total=100)

            comando = [
                "piper",
                "--model", "engines/piper/models/pt_BR-faber-medium.onnx",
                "--output_file", str(path_out),
                "--length_scale", "1.4"
            ]

            processo = subprocess.Popen(comando, stdin=subprocess.PIPE, text=True)
            
            for i, sentenca in enumerate(sentencas, 1):
                porcentagem = int((i / total_sentencas) * 100)
                progress.update(task, completed=porcentagem, description=f"[magenta]Piper: frase {i}/{total_sentencas} ({porcentagem}%)...")
                processo.stdin.write(sentenca + "\n")
                processo.stdin.flush()

            processo.stdin.close()
            processo.wait()

    console.print(f"\n[bold green]✔ Processamento concluído a 100%![/bold green]")
    console.print(f"🔊 Áudio final disponível em: [bold yellow]{path_out}[/bold yellow]\n")

if __name__ == "__main__":
    main()