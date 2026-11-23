import os
import json
from pathlib import Path


def _caminho_de_outro_so(caminho_str: str) -> bool:
    if os.name == "nt" and caminho_str.startswith("/"):
        return True  # Caminho estilo Linux/macOS rodando no Windows
    if os.name != "nt" and len(caminho_str) >= 2 and caminho_str[1] == ":":
        return True  # Caminho estilo Windows (C:\...) rodando no Linux
    return False


# Fixa a raiz do projeto (duas pastas acima de common/settings.py)
PROJECT_ROOT = Path(__file__).resolve().parent.parent


class SettingsManager:
    DEFAULT_CONFIG = {
        "input_dir": str(PROJECT_ROOT / "data" / "input"),
        "output_dir": str(PROJECT_ROOT / "data" / "output"),
        "auto_open_output": True,
        "default_engine": "kokoro",
        "kokoro_voice": "pf_dora",
        "speech_speed": 0.85,
    }

    KOKORO_VOICES = {
        "pf_dora": "pf_dora (Feminino)",
        "pm_alex": "pm_alex (Masculino)",
        "pm_santa": "pm_santa (Masculino - Grave)",
    }

    SPEED_PRESETS = {
        0.75: "0.75x (Lento)",
        0.85: "0.85x (Audiobook - Padrão)",
        1.00: "1.00x (Normal)",
        1.15: "1.15x (Rápido)",
        1.30: "1.30x (Muito rápido)",
    }

    def __init__(self, config_path: str | Path = None):
        if config_path is None:
            config_path = PROJECT_ROOT / "common" / "config" / "settings.json"
        self.config_path = Path(config_path)
        self.config = self._carregar()

    def _carregar(self) -> dict:
        if not self.config_path.exists():
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            self._salvar_dados(self.DEFAULT_CONFIG)
            return self.DEFAULT_CONFIG.copy()

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                dados = json.load(f)
            config_mesclada = self.DEFAULT_CONFIG.copy()
            config_mesclada.update(dados)

            alterado = False
            if _caminho_de_outro_so(config_mesclada.get("input_dir", "")):
                config_mesclada["input_dir"] = self.DEFAULT_CONFIG["input_dir"]
                alterado = True
            if _caminho_de_outro_so(config_mesclada.get("output_dir", "")):
                config_mesclada["output_dir"] = self.DEFAULT_CONFIG["output_dir"]
                alterado = True

            if alterado:
                self._salvar_dados(config_mesclada)

            return config_mesclada
        except (json.JSONDecodeError, OSError):
            return self.DEFAULT_CONFIG.copy()

    def _salvar_dados(self, dados: dict) -> None:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=4, ensure_ascii=False)

    @staticmethod
    def _normalizar_caminho(caminho_str: str) -> Path:
        limpo = caminho_str.strip().strip("'\"")
        caminho = Path(limpo).expanduser()
        # Se for um caminho relativo, resolve a partir da raiz real do projeto
        if not caminho.is_absolute():
            caminho = PROJECT_ROOT / caminho
        return caminho

    def get_input_path(self) -> Path:
        return self._normalizar_caminho(self.config["input_dir"])

    def get_output_path(self) -> Path:
        return self._normalizar_caminho(self.config["output_dir"])

    def get_auto_open_output(self) -> bool:
        return bool(self.config.get("auto_open_output", True))

    def get_default_engine(self) -> str:
        engine = self.config.get("default_engine", "kokoro")
        return engine if engine in ("kokoro", "piper") else "kokoro"

    def get_kokoro_voice(self) -> str:
        voz = self.config.get("kokoro_voice", "pf_dora")
        return voz if voz in self.KOKORO_VOICES else "pf_dora"

    def get_kokoro_voice_label(self) -> str:
        voz = self.get_kokoro_voice()
        return self.KOKORO_VOICES.get(voz, "pf_dora (Feminino)")

    def get_speech_speed(self) -> float:
        try:
            speed = float(self.config.get("speech_speed", 0.85))
            if 0.5 <= speed <= 2.0:
                return round(speed, 2)
        except (TypeError, ValueError):
            pass
        return 0.85

    def get_speech_speed_label(self) -> str:
        speed = self.get_speech_speed()
        for preset_val, label in self.SPEED_PRESETS.items():
            if abs(speed - preset_val) < 0.001:
                return label
        return f"{speed:.2f}x (Personalizado)"

    def get_piper_length_scale(self) -> str:
        speed = self.get_speech_speed()
        return f"{1.0 / speed:.2f}"

    def set_input_dir(self, novo_caminho: str) -> tuple[bool, str]:
        caminho = self._normalizar_caminho(novo_caminho)
        if not caminho.exists() or not caminho.is_dir():
            return False, f"A pasta '{caminho}' não existe ou não é um diretório válido."
        self.config["input_dir"] = str(caminho)
        self._salvar_dados(self.config)
        return True, f"Pasta de entrada definida para: {caminho}"

    def set_output_dir(self, novo_caminho: str) -> tuple[bool, str]:
        caminho = self._normalizar_caminho(novo_caminho)
        try:
            caminho.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            return False, f"Não foi possível criar/acessar a pasta '{caminho}': {e}"
        self.config["output_dir"] = str(caminho)
        self._salvar_dados(self.config)
        return True, f"Pasta de saída definida para: {caminho}"

    def set_default_engine(self, engine: str) -> tuple[bool, str]:
        if engine not in ("kokoro", "piper"):
            return False, f"Motor inválido: '{engine}'."
        self.config["default_engine"] = engine
        self._salvar_dados(self.config)
        nome_exibicao = "Kokoro-82M" if engine == "kokoro" else "Piper TTS"
        return True, f"Motor padrão definido para: {nome_exibicao}"

    def set_kokoro_voice(self, voz: str) -> tuple[bool, str]:
        if voz not in self.KOKORO_VOICES:
            return False, f"Voz inválida: '{voz}'."
        self.config["kokoro_voice"] = voz
        self._salvar_dados(self.config)
        return True, f"Voz padrão do Kokoro definida para: {self.KOKORO_VOICES[voz]}"

    def set_speech_speed(self, nova_velocidade: float | str) -> tuple[bool, str]:
        try:
            valor_str = str(nova_velocidade).strip().replace(",", ".")
            valor = round(float(valor_str), 2)
        except ValueError:
            return False, "Valor inválido."
        if not (0.5 <= valor <= 2.0):
            return False, "A velocidade deve estar entre 0.50x e 2.00x."
        self.config["speech_speed"] = valor
        self._salvar_dados(self.config)
        return True, f"Velocidade definida para: {self.get_speech_speed_label()}"

    def toggle_auto_open_output(self) -> bool:
        novo_valor = not self.get_auto_open_output()
        self.config["auto_open_output"] = novo_valor
        self._salvar_dados(self.config)
        return novo_valor

    def restaurar_padrao(self) -> None:
        self.config = self.DEFAULT_CONFIG.copy()
        self._salvar_dados(self.config)