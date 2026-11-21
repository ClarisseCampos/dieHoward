from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.progress import (
    Progress,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
    SpinnerColumn,
)
from common.settings import SettingsManager

console = Console()


class DieHowardTUI:
    @staticmethod
    def exibir_cabecalho():
        console.clear()
        console.print(
            Panel.fit(
                "[bold cyan]🎙️ DIEHOWARD AUDIOBOOK PIPELINE[/bold cyan]\n"
                "[dim]Local-First Audio Synthesis | CPU-Optimized[/dim]",
                border_style="magenta",
            )
        )

    @staticmethod
    def menu_principal() -> str:
        console.print("\n[bold yellow]📌 Menu Principal:[/bold yellow]")
        console.print("1. [bold green]Iniciar Síntese de Áudio[/bold green]")
        console.print("2. [bold cyan]Configurações[/bold cyan]")
        console.print("3. [dim]Sair[/dim]")

        opcao = Prompt.ask("Escolha uma opção", choices=["1", "2", "3"], default="1")
        mapa = {"1": "iniciar", "2": "configuracoes", "3": "sair"}
        return mapa[opcao]

    @staticmethod
    def _exibir_resumo_configuracoes(settings: SettingsManager) -> None:
        auto_open_status = (
            "[bold green]Ativado[/bold green]"
            if settings.get_auto_open_output()
            else "[dim red]Desativado[/dim red]"
        )
        motor_atual = (
            "[bold cyan]Kokoro-82M[/bold cyan]"
            if settings.get_default_engine() == "kokoro"
            else "[bold magenta]Piper TTS[/bold magenta]"
        )

        tabela = Table(title="⚙️ Resumo das Configurações", border_style="cyan")
        tabela.add_column("Categoria", style="dim")
        tabela.add_column("Parâmetro", style="bold yellow")
        tabela.add_column("Valor Atual", style="green")

        tabela.add_row("Diretórios", "Pasta de Entrada", str(settings.get_input_path()))
        tabela.add_row("Diretórios", "Pasta de Saída", str(settings.get_output_path()))
        tabela.add_row("Diretórios", "Abrir pasta ao concluir", auto_open_status)
        tabela.add_row("Síntese (TTS)", "Motor Padrão", motor_atual)
        tabela.add_row("Síntese (TTS)", "Voz Padrão (Kokoro)", settings.get_kokoro_voice_label())
        console.print(tabela)

    @staticmethod
    def _submenu_diretorios(settings: SettingsManager) -> None:
        while True:
            DieHowardTUI.exibir_cabecalho()

            auto_open_status = (
                "[bold green]Ativado[/bold green]"
                if settings.get_auto_open_output()
                else "[dim red]Desativado[/dim red]"
            )

            tabela = Table(title="📁 Configurações > Diretórios e Arquivos", border_style="green")
            tabela.add_column("Parâmetro", style="bold yellow")
            tabela.add_column("Valor Atual", style="green")
            tabela.add_row("Pasta de Entrada (Livros)", str(settings.get_input_path()))
            tabela.add_row("Pasta de Saída (Áudios)", str(settings.get_output_path()))
            tabela.add_row("Abrir pasta ao concluir", auto_open_status)
            console.print(tabela)

            console.print("\n[bold yellow]Opções de Diretórios:[/bold yellow]")
            console.print("1. Alterar pasta padrão de [bold green]entrada[/bold green]")
            console.print("2. Alterar pasta padrão de [bold cyan]saída[/bold cyan]")
            console.print("3. Alternar abertura automática da pasta ao concluir")
            console.print("4. [bold magenta]Voltar[/bold magenta]")

            opcao = Prompt.ask("Escolha uma opção", choices=["1", "2", "3", "4"], default="4")

            if opcao == "1":
                novo = Prompt.ask(
                    "\nDigite o caminho completo da nova pasta de entrada (ex: ~/Livros)"
                )
                sucesso, msg = settings.set_input_dir(novo)
                cor = "green" if sucesso else "red"
                console.print(f"[bold {cor}]{msg}[/bold {cor}]")
                Prompt.ask("\nPressione Enter para continuar", default="")

            elif opcao == "2":
                novo = Prompt.ask(
                    "\nDigite o caminho completo da nova pasta de saída (ex: ~/Audiobooks)"
                )
                sucesso, msg = settings.set_output_dir(novo)
                cor = "green" if sucesso else "red"
                console.print(f"[bold {cor}]{msg}[/bold {cor}]")
                Prompt.ask("\nPressione Enter para continuar", default="")

            elif opcao == "3":
                ativo = settings.toggle_auto_open_output()
                estado = "ativada" if ativo else "desativada"
                console.print(f"[bold green]✔ Abertura automática {estado}![/bold green]")
                Prompt.ask("\nPressione Enter para continuar", default="")

            elif opcao == "4":
                break

    @staticmethod
    def _submenu_motor(settings: SettingsManager) -> None:
        while True:
            DieHowardTUI.exibir_cabecalho()

            motor_atual = (
                "[bold cyan]Kokoro-82M[/bold cyan]"
                if settings.get_default_engine() == "kokoro"
                else "[bold magenta]Piper TTS[/bold magenta]"
            )

            tabela = Table(title="🤖 Configurações > Motor de Síntese (TTS)", border_style="cyan")
            tabela.add_column("Parâmetro", style="bold yellow")
            tabela.add_column("Valor Atual", style="green")
            tabela.add_row("Motor Padrão", motor_atual)
            tabela.add_row("Voz Padrão (Kokoro)", settings.get_kokoro_voice_label())
            console.print(tabela)

            console.print("\n[bold yellow]Opções de Síntese:[/bold yellow]")
            console.print("1. Alterar motor padrão ([bold cyan]Kokoro-82M[/bold cyan] / [bold magenta]Piper TTS[/bold magenta])")
            console.print("2. Alterar voz padrão do [bold cyan]Kokoro PT-BR[/bold cyan]")
            console.print("3. [bold magenta]Voltar[/bold magenta]")

            opcao = Prompt.ask("Escolha uma opção", choices=["1", "2", "3"], default="3")

            if opcao == "1":
                console.print("\n[bold yellow]Selecione o Motor de Síntese Padrão:[/bold yellow]")
                console.print("1. [bold cyan]Kokoro-82M[/bold cyan] (Recomendado)")
                console.print("2. [bold magenta]Piper TTS[/bold magenta] (Modelo mais leve)")
                escolha_motor = Prompt.ask("Escolha o motor", choices=["1", "2"], default="1")
                novo_motor = "kokoro" if escolha_motor == "1" else "piper"
                sucesso, msg = settings.set_default_engine(novo_motor)
                cor = "green" if sucesso else "red"
                console.print(f"[bold {cor}]{msg}[/bold {cor}]")
                Prompt.ask("\nPressione Enter para continuar", default="")

            elif opcao == "2":
                console.print("\n[bold yellow]🗣️ Selecione a Voz Padrão do Kokoro PT-BR:[/bold yellow]")
                console.print("1. pf_dora (Feminino) [dim]- Padrão[/dim]")
                console.print("2. pm_alex (Masculino)")
                console.print("3. pm_santa (Masculino - Grave)")
                voz_idx = Prompt.ask("Escolha a voz", choices=["1", "2", "3"], default="1")
                voz_map = {"1": "pf_dora", "2": "pm_alex", "3": "pm_santa"}
                sucesso, msg = settings.set_kokoro_voice(voz_map[voz_idx])
                cor = "green" if sucesso else "red"
                console.print(f"[bold {cor}]{msg}[/bold {cor}]")
                Prompt.ask("\nPressione Enter para continuar", default="")

            elif opcao == "3":
                break

    @staticmethod
    def menu_configuracoes(settings: SettingsManager) -> None:
        while True:
            DieHowardTUI.exibir_cabecalho()
            DieHowardTUI._exibir_resumo_configuracoes(settings)

            console.print("\n[bold yellow]Categorias de Configuração:[/bold yellow]")
            console.print("1. 📁 [bold green]Diretórios e Arquivos[/bold green]")
            console.print("2. 🤖 [bold cyan]Motor de Síntese (TTS)[/bold cyan]")
            console.print("3. 🔄 [dim]Restaurar todas as configurações padrão[/dim]")
            console.print("4. [bold magenta]Voltar ao Menu Principal[/bold magenta]")

            opcao = Prompt.ask("Escolha uma categoria", choices=["1", "2", "3", "4"], default="4")

            if opcao == "1":
                DieHowardTUI._submenu_diretorios(settings)
            elif opcao == "2":
                DieHowardTUI._submenu_motor(settings)
            elif opcao == "3":
                settings.restaurar_padrao()
                console.print("[bold green]✔ Todas as configurações padrão foram restauradas![/bold green]")
                Prompt.ask("\nPressione Enter para continuar", default="")
            elif opcao == "4":
                break

    @staticmethod
    def listar_arquivos_input(input_dir: Path) -> str | None:
        if not input_dir.exists() or not input_dir.is_dir():
            console.print(
                f"[bold red]❌ A pasta de entrada configurada não existe: {input_dir}[/bold red]"
            )
            console.print(
                "[yellow]Acesse 'Configurações' no menu inicial para corrigir o caminho.[/yellow]"
            )
            return None

        extensoes_permitidas = ("*.txt", "*.pdf", "*.epub")
        arquivos = []
        for ext in extensoes_permitidas:
            arquivos.extend(input_dir.glob(ext))

        arquivos.sort(key=lambda x: x.name.lower())

        if not arquivos:
            console.print(
                f"[bold red]❌ Nenhum arquivo (.txt, .pdf, .epub) encontrado em {input_dir}/[/bold red]"
            )
            return None

        table = Table(
            title=f"📄 Livros Disponíveis ({input_dir})",
            border_style="dim",
        )
        table.add_column("Nº", justify="center", style="cyan", no_wrap=True)
        table.add_column("Nome do Arquivo", style="green")
        table.add_column("Formato", justify="center", style="yellow")
        table.add_column("Tamanho", justify="right")

        for idx, arq in enumerate(arquivos, 1):
            tamanho = f"{arq.stat().st_size / 1024:.1f} KB"
            formato = arq.suffix.upper().replace(".", "")
            table.add_row(str(idx), arq.name, formato, tamanho)

        console.print(table)

        escolha = Prompt.ask(
            "Selecione o número do arquivo",
            choices=[str(i) for i in range(1, len(arquivos) + 1)],
        )
        return arquivos[int(escolha) - 1].name

    @staticmethod
    def selecionar_modo_saida() -> str:
        console.print("\n[bold yellow]📂 Modo de Exportação do Áudio:[/bold yellow]")
        console.print("1. [bold green]Arquivo único[/bold green] (Livro completo em um só .wav)")
        console.print(
            "2. [bold cyan]Separado por capítulos[/bold cyan] (Gera uma pasta com um .wav por capítulo)"
        )

        opcao = Prompt.ask("Escolha o modo", choices=["1", "2"])
        return "unico" if opcao == "1" else "capitulos"

    @staticmethod
    def criar_barra_progresso():
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=None, complete_style="green", finished_style="bold green"),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=console,
        )