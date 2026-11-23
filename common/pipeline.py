import os
import re
import sys
import subprocess
from pathlib import Path

from common.normalizer import TextNormalizer
from common.parser import DocumentParser
from common.settings import SettingsManager, PROJECT_ROOT
from engines.kokoro.kokoro_engine import KokoroCPUEngine
from engines.piper.piper_engine import PiperEngine


class AudioPipeline:
    def __init__(self, settings: SettingsManager):
        self.settings = settings
        self.engine_tipo = settings.get_default_engine()
        self.voz = settings.get_kokoro_voice() if self.engine_tipo == "kokoro" else "faber"
        self.velocidade = settings.get_speech_speed()
        
        # Inicializa o normalizador na forma padrão (compatível com a versão que você reverteu)
        self.normalizer = TextNormalizer()
        
        self.engine = self._inicializar_motor()

    def _inicializar_motor(self):
        if self.engine_tipo == "kokoro":
            return KokoroCPUEngine(
                model_path=str(PROJECT_ROOT / "models" / "kokoro" / "kokoro-v1.0.onnx"),
                voices_path=str(PROJECT_ROOT / "models" / "kokoro" / "voices-v1.0.bin")
            )
        else:
            return PiperEngine(
                model_path=str(PROJECT_ROOT / "models" / "piper" / "pt_BR-faber-medium.onnx"),
                length_scale=self.settings.get_piper_length_scale()
            )

    @staticmethod
    def limpar_nome_arquivo(texto: str) -> str:
        texto_limpo = re.sub(r'[\\/*?:"<>|]', "", texto)
        texto_limpo = re.sub(r"\s+", "_", texto_limpo.strip())
        return texto_limpo[:60] or "capitulo"

    @staticmethod
    def abrir_pasta_grafica(caminho: Path) -> None:
        destino = caminho.resolve()
        try:
            if sys.platform == "win32":
                os.startfile(str(destino))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(destino)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.Popen(["xdg-open", str(destino)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        except Exception:
            pass

    def processar_unico(self, path_in: Path, output_dir: Path, on_log, on_progress_start) -> Path:
        on_log(f"\n[dim]Extraindo texto completo de {path_in.name}...[/dim]")
        texto_bruto = DocumentParser.extrair_texto(path_in)
        texto_tratado = self.normalizer.processar(texto_bruto)

        path_out = output_dir / f"{path_in.stem}_{self.engine_tipo}.wav"
        atualizar_barra = on_progress_start(self.engine_tipo, "Sintetizando livro")

        if self.engine_tipo == "kokoro":
            self.engine.gerar_audio_com_progresso(texto_tratado, str(path_out), self.voz, self.velocidade, atualizar_barra)
        else:
            self.engine.gerar_audio_com_progresso(texto_tratado, str(path_out), atualizar_barra)

        if self.settings.get_auto_open_output():
            self.abrir_pasta_grafica(output_dir)

        return path_out

    def processar_capitulos(self, path_in: Path, output_dir: Path, on_log, on_progress_start) -> Path:
        on_log(f"\n[dim]Analisando capítulos de {path_in.name}...[/dim]")
        capitulos = DocumentParser.extrair_capitulos(path_in)
        on_log(f"[bold cyan]📚 {len(capitulos)} capítulo(s) identificado(s).[/bold cyan]\n")

        pasta_saida = output_dir / f"{self.limpar_nome_arquivo(path_in.stem)}_{self.engine_tipo}"
        pasta_saida.mkdir(parents=True, exist_ok=True)

        for idx, cap in enumerate(capitulos, 1):
            titulo = cap["titulo"]
            texto_tratado = self.normalizer.processar(cap["texto"])
            if not texto_tratado.strip():
                continue

            nome_wav = f"{idx:02d}_{self.limpar_nome_arquivo(titulo)}.wav"
            destino_cap = pasta_saida / nome_wav
            
            rotulo = f"Cap. {idx}/{len(capitulos)} ({titulo[:25]})"
            atualizar_barra = on_progress_start(self.engine_tipo, rotulo)

            if self.engine_tipo == "kokoro":
                self.engine.gerar_audio_com_progresso(texto_tratado, str(destino_cap), self.voz, self.velocidade, atualizar_barra)
            else:
                self.engine.gerar_audio_com_progresso(texto_tratado, str(destino_cap), atualizar_barra)

        if self.settings.get_auto_open_output():
            self.abrir_pasta_grafica(pasta_saida)
            
        return pasta_saida