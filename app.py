from pathlib import Path
from common.tui import DieHowardTUI, console
from common.normalizer import TextNormalizer
from common.parser import DocumentParser  # <-- Importação adicionada para suportar PDF/EPUB
from engines.kokoro.kokoro_engine import KokoroCPUEngine
from engines.piper.piper_engine import PiperEngine

def main():
    DieHowardTUI.exibir_cabecalho()
    
    # 1. Seleção Interativa
    arquivo_nome = DieHowardTUI.listar_arquivos_input()
    if not arquivo_nome:
        return

    engine_tipo, voz = DieHowardTUI.selecionar_engine()
    
    path_in = Path("data/input") / arquivo_nome
    path_out = Path("data/output") / f"{path_in.stem}_{engine_tipo}.wav"

    # 2. Leitura e Normalização Única
    console.print(f"\n[cyan]Extraindo texto de {arquivo_nome}...[/cyan]")
    
    # Diferencia txt de formatos binários (PDF/EPUB) usando o seu parser
    if path_in.suffix.lower() == ".txt":
        with open(path_in, "r", encoding="utf-8", errors="ignore") as f:
            texto_bruto = f.read()
    else:
        # Chama o seu parser para extrair o texto de PDFs ou EPUBs
        # (Se o seu método chamar diferente de 'extrair_texto', basta ajustar abaixo)
        parser = DocumentParser()
        texto_bruto = parser.extrair_texto(str(path_in))

    normalizer = TextNormalizer()
    texto_tratado = normalizer.processar(texto_bruto)

    # 3. Execução dos Motores TTS
    if engine_tipo == "kokoro":
        engine = KokoroCPUEngine(
            model_path="models/kokoro/kokoro-v1.0.onnx", # <-- Caminho corrigido
            voices_path="models/kokoro/voices-v1.0.bin"  # <-- Caminho corrigido
        )
        
        with DieHowardTUI.criar_barra_progresso() as progress:
            task = progress.add_task(f"[cyan]Sintetizando com Kokoro ({voz})...", total=100)

            def atualizar_barra(porcentagem, atual, total):
                progress.update(task, completed=porcentagem, description=f"[cyan]Kokoro: bloco {atual}/{total} ({porcentagem}%)...")

            engine.gerar_audio_com_progresso(
                texto=texto_tratado, 
                output_path=str(path_out), 
                voice=voz, 
                speed=0.83,
                progress_callback=atualizar_barra
            )

    elif engine_tipo == "piper":
        engine = PiperEngine(
            model_path="models/pt_BR-faber-medium.onnx", # <-- Caminho corrigido
            length_scale="1.4"
        )

        with DieHowardTUI.criar_barra_progresso() as progress:
            task = progress.add_task("[magenta]Sintetizando com Piper (Faber)...", total=100)

            def atualizar_barra(porcentagem, atual, total):
                progress.update(task, completed=porcentagem, description=f"[magenta]Piper: frase {atual}/{total} ({porcentagem}%)...")

            engine.gerar_audio_com_progresso(
                texto=texto_tratado,
                output_path=str(path_out),
                progress_callback=atualizar_barra
            )

    # 4. Finalização
    console.print(f"\n[bold green]✔ Processamento concluído a 100%![/bold green]")
    console.print(f"🔊 Áudio final disponível em: [bold yellow]{path_out}[/bold yellow]\n")

if __name__ == "__main__":
    main()