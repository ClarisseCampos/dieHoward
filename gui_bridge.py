import re
import sys
import json
import argparse
from pathlib import Path
from common.settings import SettingsManager
from common.pipeline import AudioPipeline


def emitir_evento(tipo: str, **dados):
    """Imprime uma linha JSON limpa para o frontend em Rust ler via stdout."""
    payload = {"tipo": tipo, **dados}
    print(json.dumps(payload, ensure_ascii=False), flush=True)


def main():
    parser = argparse.ArgumentParser(description="Ponte JSON para a GUI do DieHoward")
    parser.add_argument("--arquivo", required=True, help="Caminho do livro (.txt, .pdf, .epub)")
    parser.add_argument("--modo", choices=["unico", "capitulos"], default="unico")
    parser.add_argument("--engine", choices=["kokoro", "piper"], default=None)
    parser.add_argument("--voz", default=None)
    parser.add_argument("--velocidade", type=float, default=None)
    args = parser.parse_args()

    try:
        settings = SettingsManager()

        if args.engine:
            settings.set_default_engine(args.engine)
        if args.voz:
            settings.set_kokoro_voice(args.voz)
        if args.velocidade:
            settings.set_speech_speed(args.velocidade)

        emitir_evento("status", mensagem="Inicializando motor de áudio...")
        pipeline = AudioPipeline(settings)

        path_in = Path(args.arquivo)
        output_dir = settings.get_output_path()

        def on_log(msg: str):
            limpo = re.sub(r"\[/?[^\]]+\]", "", msg).strip()
            if limpo:
                emitir_evento("log", mensagem=limpo)

        def on_progress_start(engine: str, rotulo: str):
            emitir_evento("etapa", rotulo=rotulo)

            def atualizar(porcentagem: int, atual: int, total: int):
                emitir_evento(
                    "progresso",
                    porcentagem=porcentagem,
                    atual=atual,
                    total=total,
                    rotulo=rotulo,
                )

            return atualizar

        if args.modo == "unico":
            destino = pipeline.processar_unico(path_in, output_dir, on_log, on_progress_start)
        else:
            destino = pipeline.processar_capitulos(path_in, output_dir, on_log, on_progress_start)

        emitir_evento("concluido", destino=str(destino))

    except Exception as e:
        emitir_evento("erro", mensagem=str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()