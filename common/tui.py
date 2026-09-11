import os
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
    SpinnerColumn
)

console = Console()

class DieHowardTUI:
    @staticmethod
    def exibir_cabecalho():
        console.clear()
        console.print(
            Panel.fit(
                "[bold cyan]🎙️ DIEHOWARD AUDIOBOOK PIPELINE[/bold cyan]\n"
                "[dim]Local-First Audio Synthesis | CPU-Optimized[/dim]",
                border_style="magenta"
            )
        )

    @staticmethod
    def listar_arquivos_input() -> str:
        input_dir = Path("data/input")
        arquivos = list(input_dir.glob("*.txt"))

        if not arquivos:
            console.print("[bold red]❌ Nenhum arquivo .txt encontrado em data/input/[/bold red]")
            return None

        table = Table(title="📄 Arquivos de Texto Disponíveis", border_style="dim")
        table.add_column("Nº", justify="center", style="cyan", no_wrap=True)
        table.add_column("Nome do Arquivo", style="green")
        table.add_column("Tamanho", justify="right")

        for idx, arq in enumerate(arquivos, 1):
            tamanho = f"{arq.stat().st_size / 1024:.1f} KB"
            table.add_row(str(idx), arq.name, tamanho)

        console.print(table)
        
        escolha = Prompt.ask("Selecione o número do arquivo", choices=[str(i) for i in range(1, len(arquivos) + 1)])
        return arquivos[int(escolha) - 1].name

    @staticmethod
    def selecionar_engine() -> tuple[str, str]:
        console.print("\n[bold yellow]🤖 Selecione o Motor de Síntese:[/bold yellow]")
        console.print("1. [bold cyan]Kokoro-82M[/bold cyan] (Recomendado)")
        console.print("2. [bold magenta]Piper TTS[/bold magenta] (Modelo mais leve)")
        
        opcao = Prompt.ask("Escolha o motor", choices=["1", "2"])

        if opcao == "1":
            console.print("\n[bold yellow]🗣️ Vozes do Kokoro PT-BR:[/bold yellow]")
            console.print("1. pf_dora (Feminino)")
            console.print("2. pm_alex (Masculino)")
            console.print("3. pm_santa (Masculino - Grave)")
            voz_idx = Prompt.ask("Escolha a voz", choices=["1", "2", "3"])
            voz_map = {"1": "pf_dora", "2": "pm_alex", "3": "pm_santa"}
            return "kokoro", voz_map[voz_idx]
        else:
            return "piper", "faber"

    @staticmethod
    def criar_barra_progresso():
        """Cria uma barra de progresso do Rich altamente estilizada e com porcentagem."""
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=None, complete_style="green", finished_style="bold green"),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=console
        )