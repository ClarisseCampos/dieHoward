import urllib.request
from pathlib import Path
from rich.console import Console
from rich.progress import (
    Progress,
    TextColumn,
    BarColumn,
    DownloadColumn,
    TransferSpeedColumn,
    TimeRemainingColumn,
)
from common.settings import PROJECT_ROOT

console = Console()


class ModelDownloader:
    MODELOS = {
        "kokoro": [
            {
                "nome": "Kokoro-82M (Modelo ONNX v1.0)",
                "destino": PROJECT_ROOT / "models" / "kokoro" / "kokoro-v1.0.onnx",
                "url": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx",
            },
            {
                "nome": "Kokoro-82M (Pacote de Vozes v1.0)",
                "destino": PROJECT_ROOT / "models" / "kokoro" / "voices-v1.0.bin",
                "url": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin",
            },
        ],
        "piper": [
            {
                "nome": "Piper PT-BR (Faber Medium - ONNX)",
                "destino": PROJECT_ROOT / "models" / "piper" / "pt_BR-faber-medium.onnx",
                "url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_BR/faber/medium/pt_BR-faber-medium.onnx",
            },
            {
                "nome": "Piper PT-BR (Faber Medium - Config JSON)",
                "destino": PROJECT_ROOT / "models" / "piper" / "pt_BR-faber-medium.onnx.json",
                "url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_BR/faber/medium/pt_BR-faber-medium.onnx.json",
            },
        ],
    }

    @staticmethod
    def _baixar_arquivo(url: str, destino: Path, descricao: str) -> None:
        destino.parent.mkdir(parents=True, exist_ok=True)
        arquivo_temp = destino.with_suffix(destino.suffix + ".part")

        req = urllib.request.Request(url, headers={"User-Agent": "DieHoward-TTS/1.0"})
        with urllib.request.urlopen(req, timeout=60) as resposta:
            total_bytes = int(resposta.headers.get("Content-Length", 0))

            with Progress(
                TextColumn("[bold cyan]{task.description}"),
                BarColumn(bar_width=None),
                DownloadColumn(),
                TransferSpeedColumn(),
                TimeRemainingColumn(),
                console=console,
            ) as progress:
                task = progress.add_task(descricao, total=total_bytes or None)
                with open(arquivo_temp, "wb") as f:
                    while True:
                        bloco = resposta.read(1024 * 64)
                        if not bloco:
                            break
                        f.write(bloco)
                        progress.update(task, advance=len(bloco))

        # Renomeia apenas após concluir 100%, evitando arquivos corrompidos
        arquivo_temp.replace(destino)

    @classmethod
    def garantir_modelos(cls, engine: str | None = None) -> None:
        """Verifica e baixa os modelos ausentes. Se engine=None, verifica todos."""
        motores = [engine] if engine in cls.MODELOS else list(cls.MODELOS.keys())
        pendentes = []

        for motor in motores:
            for item in cls.MODELOS[motor]:
                if not item["destino"].exists() or item["destino"].stat().st_size == 0:
                    pendentes.append(item)

        if not pendentes:
            return

        console.print(
            f"\n[bold yellow]⬇️ Baixando {len(pendentes)} arquivo(s) de modelo necessário(s)...[/bold yellow]"
        )
        for item in pendentes:
            cls._baixar_arquivo(item["url"], item["destino"], item["nome"])
        console.print("[bold green]✔ Modelos prontos para uso![/bold green]\n")