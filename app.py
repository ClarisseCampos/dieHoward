import re
from pathlib import Path
from rich.prompt import Prompt
from common.tui import DieHowardTUI, console
from common.normalizer import TextNormalizer
from common.parser import DocumentParser
from common.settings import SettingsManager
from engines.kokoro.kokoro_engine import KokoroCPUEngine
from engines.piper.piper_engine import PiperEngine


def limpar_nome_arquivo(texto: str) -> str:
    """Remove caracteres inválidos para nomes de arquivos e pastas."""
    texto_limpo = re.sub(r'[\\/*?:"<>|]', "", texto)
    texto_limpo = re.sub(r"\s+", "_", texto_limpo.strip())
    return texto_limpo[:60] or "capitulo"


def sintetizar_trecho(engine_tipo: str, engine, voz: str, texto: str, destino: Path, rotulo: str):
    """Executa a síntese de um bloco de texto (livro inteiro ou um capítulo)."""
    with DieHowardTUI.criar_barra_progresso() as progress:
        if engine_tipo == "kokoro":
            task = progress.add_task(f"[cyan]{rotulo}...", total=100)

            def atualizar_barra(porcentagem, atual, total):
                progress.update(
                    task,
                    completed=porcentagem,
                    description=f"[cyan]{rotulo}: bloco {atual}/{total} ({porcentagem}%)...",
                )

            engine.gerar_audio_com_progresso(
                texto=texto,
                output_path=str(destino),
                voice=voz,
                speed=0.83,
                progress_callback=atualizar_barra,
            )

        elif engine_tipo == "piper":
            task = progress.add_task(f"[magenta]{rotulo} (aguarde)...", total=100)

            def atualizar_barra(porcentagem, atual, total):
                if porcentagem == 100:
                    progress.update(
                        task,
                        completed=100,
                        description=f"[magenta]{rotulo}: concluído![/magenta]",
                    )
                else:
                    progress.update(
                        task,
                        completed=10,
                        description=f"[magenta]{rotulo}: processando no fundo...[/magenta]",
                    )

            engine.gerar_audio_com_progresso(
                texto=texto,
                output_path=str(destino),
                progress_callback=atualizar_barra,
            )


def executar_pipeline(settings: SettingsManager):
    input_dir = settings.get_input_path()
    output_dir = settings.get_output_path()

    # 1. Seleção Interativa usando a pasta configurada
    arquivo_nome = DieHowardTUI.listar_arquivos_input(input_dir)
    if not arquivo_nome:
        Prompt.ask("\nPressione Enter para voltar ao menu", default="")
        return

    engine_tipo, voz = DieHowardTUI.selecionar_engine()
    modo_saida = DieHowardTUI.selecionar_modo_saida()

    path_in = input_dir / arquivo_nome
    output_dir.mkdir(parents=True, exist_ok=True)
    normalizer = TextNormalizer()

    # Inicializa o motor escolhido uma única vez
    if engine_tipo == "kokoro":
        engine = KokoroCPUEngine(
            model_path="models/kokoro/kokoro-v1.0.onnx",
            voices_path="models/kokoro/voices-v1.0.bin",
        )
    else:
        engine = PiperEngine(
            model_path="models/piper/pt_BR-faber-medium.onnx",
            length_scale="1.4",
        )

    try:
        if modo_saida == "unico":
            console.print(f"\n[dim]Extraindo texto completo de {arquivo_nome}...[/dim]")
            texto_bruto = DocumentParser.extrair_texto(path_in)
            texto_tratado = normalizer.processar(texto_bruto)

            path_out = output_dir / f"{path_in.stem}_{engine_tipo}.wav"
            sintetizar_trecho(engine_tipo, engine, voz, texto_tratado, path_out, "Sintetizando livro")

            console.print("\n[bold green]✔ Processamento concluído a 100%![/bold green]")
            console.print(f"🔊 Áudio final disponível em: [bold yellow]{path_out}[/bold yellow]\n")

        else:
            console.print(f"\n[dim]Analisando capítulos de {arquivo_nome}...[/dim]")
            capitulos = DocumentParser.extrair_capitulos(path_in)
            console.print(f"[bold cyan]📚 {len(capitulos)} capítulo(s) identificado(s).[/bold cyan]\n")

            pasta_saida = output_dir / f"{limpar_nome_arquivo(path_in.stem)}_{engine_tipo}"
            pasta_saida.mkdir(parents=True, exist_ok=True)

            for idx, cap in enumerate(capitulos, 1):
                titulo = cap["titulo"]
                texto_tratado = normalizer.processar(cap["texto"])

                if not texto_tratado.strip():
                    continue

                nome_wav = f"{idx:02d}_{limpar_nome_arquivo(titulo)}.wav"
                destino_cap = pasta_saida / nome_wav

                sintetizar_trecho(
                    engine_tipo,
                    engine,
                    voz,
                    texto_tratado,
                    destino_cap,
                    f"Cap. {idx}/{len(capitulos)} ({titulo[:25]})",
                )

            console.print("\n[bold green]✔ Todos os capítulos foram processados![/bold green]")
            console.print(f"📁 Pasta com os áudios: [bold yellow]{pasta_saida}/[/bold yellow]\n")

    except Exception as e:
        console.print(f"\n[bold red]✖ Erro durante o processamento:[/bold red] {e}\n")


def main():
    settings = SettingsManager()

    while True:
        DieHowardTUI.exibir_cabecalho()
        acao = DieHowardTUI.menu_principal()

        if acao == "iniciar":
            executar_pipeline(settings)
            break
        elif acao == "configuracoes":
            DieHowardTUI.menu_configuracoes(settings)
        elif acao == "sair":
            console.print("[dim]Encerrando DieHoward. Até logo![/dim]")
            break


if __name__ == "__main__":
    main()