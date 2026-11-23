import sys
from pathlib import Path

# Adiciona a pasta raiz (dieHoward/) ao caminho de busca do Python ANTES dos imports locais
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from rich.prompt import Prompt
from common.tui import DieHowardTUI, console
from common.settings import SettingsManager
from common.pipeline import AudioPipeline

# Adiciona a pasta raiz (dieHoward/) ao caminho de busca do Python
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def executar_fluxo(settings: SettingsManager):
    input_dir = settings.get_input_path()
    output_dir = settings.get_output_path()

    arquivo_nome = DieHowardTUI.listar_arquivos_input(input_dir)
    if not arquivo_nome:
        Prompt.ask("\nPressione Enter para voltar ao menu", default="")
        return

    path_in = input_dir / arquivo_nome
    modo_saida = "unico" if path_in.suffix.lower() == ".txt" else DieHowardTUI.selecionar_modo_saida()
    output_dir.mkdir(parents=True, exist_ok=True)

    # Inicia o pipeline de processamento (os caminhos agora são absolutos lá dentro)
    pipeline = AudioPipeline(settings)

    info_motor = f"Kokoro-82M ({settings.get_kokoro_voice_label()})" if pipeline.engine_tipo == "kokoro" else "Piper TTS (faber)"
    console.print(
        f"\n[dim]🤖 Motor: [bold]{info_motor}[/bold] | "
        f"Velocidade: [bold]{settings.get_speech_speed_label()}[/bold][/dim]"
    )

    # Callback de Print Simples
    def log_msg(msg: str):
        console.print(msg)

    try:
        # Contexto Visual da Barra de Progresso
        with DieHowardTUI.criar_barra_progresso() as progress:
            
            # Fábrica (callback) de barras de progresso que o pipeline chamará para cada novo áudio
            def progress_adapter(engine_tipo: str, rotulo: str):
                if engine_tipo == "kokoro":
                    task = progress.add_task(f"[cyan]{rotulo}...", total=100)
                    def update(porcentagem, atual, total):
                        progress.update(task, completed=porcentagem, description=f"[cyan]{rotulo}: bloco {atual}/{total} ({porcentagem}%)...")
                    return update
                else:
                    task = progress.add_task(f"[magenta]{rotulo} (aguarde)...", total=100)
                    def update(porcentagem, atual, total):
                        if porcentagem == 100:
                            progress.update(task, completed=100, description=f"[magenta]{rotulo}: concluído![/magenta]")
                        else:
                            progress.update(task, completed=10, description=f"[magenta]{rotulo}: processando no fundo...[/magenta]")
                    return update

            # Delega a orquestração inteira para o core (pipeline.py)
            if modo_saida == "unico":
                path_out = pipeline.processar_unico(path_in, output_dir, log_msg, progress_adapter)
                console.print("\n[bold green]✔ Processamento concluído a 100%![/bold green]")
                console.print(f"🔊 Áudio final: [bold yellow]{path_out}[/bold yellow]\n")
            else:
                pasta_saida = pipeline.processar_capitulos(path_in, output_dir, log_msg, progress_adapter)
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
            executar_fluxo(settings)
            break
        elif acao == "configuracoes":
            DieHowardTUI.menu_configuracoes(settings)
        elif acao == "sair":
            console.print("[dim]Encerrando DieHoward. Até logo![/dim]")
            break


if __name__ == "__main__":
    main()