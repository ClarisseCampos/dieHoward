import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from common.normalizer import TextNormalizer
from common.parser import DocumentParser
from common.settings import SettingsManager
from engines.kokoro.kokoro_engine import KokoroCPUEngine
from engines.piper.piper_engine import PiperEngine


def _emitir(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False), flush=True)


def _resolver_caminho(settings: SettingsManager, chave: str, padrao_relativo: str) -> Path:
    if chave == "input_dir":
        caminho = settings.get_input_path()
    elif chave == "output_dir":
        caminho = settings.get_output_path()
    else:
        caminho = Path(padrao_relativo)

    if not caminho.is_absolute():
        caminho = RAIZ / caminho
    return caminho


def _obter_config_completa(settings: SettingsManager) -> dict:
    dados = dict(settings.config)
    dados.setdefault("input_dir", "data/input")
    dados.setdefault("output_dir", "data/output")
    dados.setdefault("auto_open", False)
    dados.setdefault("engine", "kokoro")
    dados.setdefault("voz", "pf_dora")
    dados.setdefault("velocidade", 0.85)
    return dados


def _listar_livros(settings: SettingsManager) -> list[str]:
    pasta_input = _resolver_caminho(settings, "input_dir", "data/input")
    pasta_input.mkdir(parents=True, exist_ok=True)

    extensoes = {".txt", ".pdf", ".epub"}
    livros = []
    for item in pasta_input.iterdir():
        if item.is_file() and not item.name.startswith(".") and item.suffix.lower() in extensoes:
            livros.append(item.name)

    livros.sort(key=lambda s: s.lower())
    return livros


def _sintetizar(
    settings: SettingsManager,
    arquivo: str,
    modo: str,
    engine_tipo: str,
    voz: str | None,
    velocidade: float,
) -> None:
    pasta_input = _resolver_caminho(settings, "input_dir", "data/input")
    pasta_output = _resolver_caminho(settings, "output_dir", "data/output")
    pasta_output.mkdir(parents=True, exist_ok=True)

    caminho_arquivo = Path(arquivo)
    if not caminho_arquivo.is_absolute():
        caminho_arquivo = pasta_input / arquivo

    if not caminho_arquivo.exists():
        _emitir({"tipo": "erro", "mensagem": f"Arquivo não encontrado: {caminho_arquivo}"})
        return

    _emitir({"tipo": "status", "mensagem": f"Lendo {caminho_arquivo.name}..."})
    _emitir({"tipo": "etapa", "rotulo": "Extraindo e normalizando texto"})

    try:
        texto_bruto = DocumentParser.extrair_texto(caminho_arquivo)
        normalizer = TextNormalizer()
        texto_tratado = normalizer.processar(texto_bruto)
    except Exception as exc:
        _emitir({"tipo": "erro", "mensagem": f"Falha ao extrair/normalizar texto: {exc}"})
        return

    destino = pasta_output / f"{caminho_arquivo.stem}_{engine_tipo}.wav"
    _emitir({"tipo": "etapa", "rotulo": f"Sintetizando com {engine_tipo} (modo: {modo})"})
    _emitir({"tipo": "progresso", "rotulo": "Preparando áudio", "porcentagem": 5})

    def on_progresso(porcentagem, atual=None, total=None):
        pct = max(5, min(99, int(porcentagem)))
        rotulo = f"Bloco {atual}/{total}" if atual is not None and total is not None else "Sintetizando"
        _emitir({"tipo": "progresso", "rotulo": rotulo, "porcentagem": pct})

    try:
        if engine_tipo == "piper":
            modelo_piper = RAIZ / "models" / "pt_BR-faber-medium.onnx"
            if not modelo_piper.exists():
                modelo_piper = RAIZ / "models" / "piper" / "pt_BR-faber-medium.onnx"

            # Converte velocidade (~0.85x) em length_scale aproximado para o Piper
            vel_segura = velocidade if velocidade > 0 else 0.85
            length_scale = f"{max(0.5, min(2.5, 1.0 / vel_segura)):.2f}"

            motor = PiperEngine(model_path=str(modelo_piper), length_scale=length_scale)
            motor.gerar_audio_com_progresso(
                texto=texto_tratado,
                output_path=str(destino),
                progress_callback=on_progresso,
            )
        else:
            voz_escolhida = voz or _obter_config_completa(settings).get("voz", "pf_dora")
            motor = KokoroCPUEngine(
                model_path=str(RAIZ / "models" / "kokoro" / "kokoro-v1.0.onnx"),
                voices_path=str(RAIZ / "models" / "kokoro" / "voices-v1.0.bin"),
            )
            motor.gerar_audio_com_progresso(
                texto=texto_tratado,
                output_path=str(destino),
                voice=voz_escolhida,
                speed=velocidade,
                progress_callback=on_progresso,
            )

        _emitir({"tipo": "concluido", "destino": str(destino)})
    except Exception as exc:
        _emitir({"tipo": "erro", "mensagem": f"Erro na síntese: {exc}"})


def main() -> None:
    if len(sys.argv) < 2:
        print(json.dumps({"erro": "Comando não informado"}))
        sys.exit(1)

    comando = sys.argv[1]
    settings = SettingsManager(RAIZ / "common" / "config" / "settings.json")

    if comando == "obter-config":
        print(json.dumps(_obter_config_completa(settings), ensure_ascii=False))
        return

    if comando == "salvar-config":
        raw = sys.argv[2] if len(sys.argv) > 2 else "{}"
        nova = json.loads(raw)
        atual = _obter_config_completa(settings)
        atual.update(nova)
        settings.config = atual
        settings._salvar_dados(settings.config)
        print(json.dumps(_obter_config_completa(settings), ensure_ascii=False))
        return

    if comando == "restaurar-padrao":
        settings.restaurar_padrao()
        print(json.dumps(_obter_config_completa(settings), ensure_ascii=False))
        return

    if comando == "listar-livros":
        print(json.dumps(_listar_livros(settings), ensure_ascii=False))
        return

    if comando == "sintetizar":
        arquivo = ""
        modo = "unico"
        engine = "kokoro"
        voz = None
        velocidade = 0.85

        i = 2
        while i < len(sys.argv):
            arg = sys.argv[i]
            if arg == "--arquivo" and i + 1 < len(sys.argv):
                arquivo = sys.argv[i + 1]
                i += 2
            elif arg == "--modo" and i + 1 < len(sys.argv):
                modo = sys.argv[i + 1]
                i += 2
            elif arg in ("--engine", "--motor") and i + 1 < len(sys.argv):
                engine = sys.argv[i + 1]
                i += 2
            elif arg == "--voz" and i + 1 < len(sys.argv):
                voz = sys.argv[i + 1]
                i += 2
            elif arg == "--velocidade" and i + 1 < len(sys.argv):
                try:
                    velocidade = float(sys.argv[i + 1])
                except ValueError:
                    velocidade = 0.85
                i += 2
            else:
                i += 1

        _sintetizar(settings, arquivo, modo, engine, voz, velocidade)
        return

    print(json.dumps({"erro": f"Comando desconhecido: {comando}"}))
    sys.exit(1)


if __name__ == "__main__":
    main()