from pathlib import Path
from common.tui import DieHowardTUI, console
from common.normalizer import TextNormalizer
from common.parser import DocumentParser
from engines.kokoro.kokoro_engine import KokoroCPUEngine
from engines.piper.piper_engine import PiperEngine


def main():
    DieHowardTUI.exibir_cabecalho()

    # 1. Seleção Interativa
    arquivo_nome = DieHowardTUI.listar_arquivos_input()
    if not arquivo_nome:
        console.print("[yellow]Nenhum arquivo selecionado. Encerrando.[/yellow]")
        return

    engine_tipo, voz = DieHowardTUI.selecionar_engine()

    path_in = Path("data/input") / arquivo_nome
    path_out = Path("data/output") / f"{Path(arquivo_nome).stem}_{engine_tipo}.wav"

    # 2. Extração de Texto via DocumentParser (TXT, PDF, EPUB)
    try:
        console.print(f"[dim]Extraindo texto de {arquivo_nome}...[/dim]")
        texto_bruto = DocumentParser.extrair_texto(path_in)
    except Exception as e:
        console.print(f"\n[bold red]✖ Erro ao tentar ler o arquivo {path_in.name}:[/bold red] {e}\n")
        return

    # 3. Normalização
    normalizer = TextNormalizer()
    texto_tratado = normalizer.processar(texto_bruto)

    # 4. Execução dos Motores TTS
    try:
        if engine_tipo == "kokoro":
            engine = KokoroCPUEngine(
                model_path="models/kokoro/kokoro-v1.0.onnx",
                voices_path="models/kokoro/voices-v1.0.bin",
            )

            with DieHowardTUI.criar_barra_progresso() as progress:
                task = progress.add_task(
                    f"[cyan]Sintetizando com Kokoro ({voz})...", total=100
                )

                def atualizar_barra(porcentagem, atual, total):
                    progress.update(
                        task,
                        completed=porcentagem,
                        description=f"[cyan]Kokoro: bloco {atual}/{total} ({porcentagem}%)...",
                    )

                engine.gerar_audio_com_progresso(
                    texto=texto_tratado,
                    output_path=str(path_out),
                    voice=voz,
                    speed=0.83,
                    progress_callback=atualizar_barra,
                )

        elif engine_tipo == "piper":
            engine = PiperEngine(
                model_path="models/piper/pt_BR-faber-medium.onnx",
                length_scale="1.4",
            )

            with DieHowardTUI.criar_barra_progresso() as progress:
                task = progress.add_task(
                    "[magenta]Sintetizando áudio com Piper (aguarde)...", total=100
                )

                def atualizar_barra(porcentagem, atual, total):
                    if porcentagem == 100:
                        progress.update(
                            task,
                            completed=100,
                            description="[magenta]Piper: síntese concluída![/magenta]",
                        )
                    else:
                        progress.update(
                            task,
                            completed=10,
                            description="[magenta]Piper: processando o áudio no fundo...[/magenta]",
                        )

                engine.gerar_audio_com_progresso(
                    texto=texto_tratado,
                    output_path=str(path_out),
                    progress_callback=atualizar_barra,
                )

        # 5. Finalização com Sucesso
        console.print(f"\n[bold green]✔ Processamento concluído a 100%![/bold green]")
        console.print(f"🔊 Áudio final disponível em: [bold yellow]{path_out}[/bold yellow]\n")

    except Exception as e:
        console.print(f"\n[bold red]✖ Erro durante o processamento TTS:[/bold red] {e}\n")


if __name__ == "__main__":
    main()