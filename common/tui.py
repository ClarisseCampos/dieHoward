from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeElapsedColumn,
)

console = Console()


class DieHowardTUI:
    @staticmethod
    def exibir_cabecalho():
        console.print(
            Panel.fit(
                "🎙️ DIEHOWARD AUDIOBOOK PIPELINE\nLocal-First Audio Synthesis | CPU-Optimized",
                border_style="cyan",
            )
        )

    @staticmethod
    def listar_arquivos_input():
        pasta_input = Path("data/input")

        if not pasta_input.exists():
            console.print("[red]Pasta data/input não encontrada.[/red]")
            return None

        arquivos = [
            f
            for f in pasta_input.iterdir()
            if f.is_file() and f.suffix.lower() in [".txt", ".pdf", ".epub"]
        ]

        if not arquivos:
            console.print(
                "[yellow]Nenhum arquivo (.txt, .pdf, .epub) encontrado na pasta data/input.[/yellow]"
            )
            return None

        console.print("\n 📄 Arquivos Disponíveis ")
        tabela = Table(show_header=True, header_style="bold magenta")
        tabela.add_column("Nº", style="dim", width=4)
        tabela.add_column("Nome do Arquivo")
        tabela.add_column("Tamanho", justify="right")

        arquivos.sort(key=lambda x: x.name.lower())

        for i, arq in enumerate(arquivos, 1):
            tamanho_kb = arq.stat().st_size / 1024
            tabela.add_row(str(i), arq.name, f"{tamanho_kb:.1f} KB")

        console.print(tabela)

        while True:
            padrao = "1" if arquivos else ""
            escolha = console.input(f"Selecione o número do arquivo [{padrao}]: ")

            if not escolha and arquivos:
                return arquivos[0].name

            try:
                idx = int(escolha) - 1
                if 0 <= idx < len(arquivos):
                    return arquivos[idx].name
                else:
                    console.print("[red]Número inválido. Tente novamente.[/red]")
            except ValueError:
                console.print("[red]Por favor, digite um número válido.[/red]")

    @staticmethod
    def selecionar_engine():
        console.print("\n⚙️ Motores TTS Disponíveis:")
        console.print("1. Kokoro (Alta Qualidade - Recomendado)")
        console.print("2. Piper (Mais Rápido)")

        while True:
            escolha = console.input("Escolha o motor [1/2]: ")
            if escolha in ["1", ""]:
                engine = "kokoro"
                break
            elif escolha == "2":
                engine = "piper"
                break
            else:
                console.print("[red]Opção inválida.[/red]")

        voz = None
        if engine == "kokoro":
            console.print("\n🗣️ Vozes Disponíveis (Kokoro - Português BR):")
            console.print("1. pf_dora (Feminino)")
            console.print("2. pm_alex (Masculino)")
            console.print("3. pm_santa (Masculino - Grave)")

            while True:
                escolha_voz = console.input("Escolha a voz [1/2/3]: ")
                if escolha_voz in ["1", ""]:
                    voz = "pf_dora"
                    break
                elif escolha_voz == "2":
                    voz = "pm_alex"
                    break
                elif escolha_voz == "3":
                    voz = "pm_santa"
                    break
                else:
                    console.print("[red]Opção inválida.[/red]")

        return engine, voz

    @staticmethod
    def criar_barra_progresso():
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=console,
        )