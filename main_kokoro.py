from pathlib import Path
from rich.console import Console
from rich.status import Status
from engines.kokoro.kokoro_engine import KokoroCPUEngine

console = Console()

def executar_pipeline_kokoro(arquivo_entrada: str, arquivo_saida: str, voz: str = "pf_dora"):
    path_in = Path("data/input") / arquivo_entrada
    path_out = Path("data/output") / arquivo_saida

    # 1. Lê o texto bruto (SEM passar pelo normalizer)
    with open(path_in, "r", encoding="utf-8", errors="ignore") as f:
        texto_bruto = f.read()

    console.print(f"[bold cyan][DieHoward - Kokoro][/bold cyan] Lendo texto bruto ({len(texto_bruto)} caracteres)...")

    # 2. Inicialização e Síntese com Interface Visual de Loading
    with Status("[bold green]Sintetizando áudio na CPU com Kokoro-82M...[/bold green]", spinner="dots"):
        engine = KokoroCPUEngine(
            model_path="engines/kokoro/models/kokoro-v1.0.onnx",
            voices_path="engines/kokoro/models/voices-v1.0.bin"
        )
        engine.gerar_audio(texto_bruto, str(path_out), voice=voz)

    console.print(f"[bold green]✔ Áudio Kokoro concluído com sucesso![/bold green] Salvo em: [yellow]{path_out}[/yellow]")

if __name__ == "__main__":
    executar_pipeline_kokoro("teste.txt", "audio_kokoro.wav", voz="pf_dora")