import json
from pathlib import Path


class SettingsManager:
    DEFAULT_CONFIG = {
        "input_dir": "data/input",
        "output_dir": "data/output",
        "auto_open_output": True,
        "default_engine": "kokoro",
    }

    def __init__(self, config_path: str | Path = "common/config/settings.json"):
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
        return Path(limpo).expanduser()

    def get_input_path(self) -> Path:
        return self._normalizar_caminho(self.config["input_dir"])

    def get_output_path(self) -> Path:
        return self._normalizar_caminho(self.config["output_dir"])

    def get_auto_open_output(self) -> bool:
        return bool(self.config.get("auto_open_output", True))

    def get_default_engine(self) -> str:
        engine = self.config.get("default_engine", "kokoro")
        return engine if engine in ("kokoro", "piper") else "kokoro"

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
            return False, f"Motor inválido: '{engine}'. Use 'kokoro' ou 'piper'."

        self.config["default_engine"] = engine
        self._salvar_dados(self.config)
        nome_exibicao = "Kokoro-82M" if engine == "kokoro" else "Piper TTS"
        return True, f"Motor padrão definido para: {nome_exibicao}"

    def toggle_auto_open_output(self) -> bool:
        novo_valor = not self.get_auto_open_output()
        self.config["auto_open_output"] = novo_valor
        self._salvar_dados(self.config)
        return novo_valor

    def restaurar_padrao(self) -> None:
        self.config = self.DEFAULT_CONFIG.copy()
        self._salvar_dados(self.config)