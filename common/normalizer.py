import json
import re
from pathlib import Path

# Garante que o atalho .sh encontre os arquivos JSON a partir da raiz do projeto
PROJECT_ROOT = Path(__file__).resolve().parent.parent

class TextNormalizer:
    def __init__(
        self,
        lexicon_path: str | Path = None,
        ipa_rules_path: str | Path = None,
    ):
        if lexicon_path is None:
            lexicon_path = PROJECT_ROOT / "common" / "config" / "lexicon.json"
        if ipa_rules_path is None:
            ipa_rules_path = PROJECT_ROOT / "common" / "config" / "ipa_rules.json"

        self.lexicon = self._carregar_e_achatar_json(lexicon_path)
        self.ipa_rules = self._carregar_e_achatar_json(ipa_rules_path)

    def _achatar_dicionario(self, dados: dict) -> dict[str, str]:
        resultado = {}
        for chave, valor in dados.items():
            if isinstance(valor, dict):
                resultado.update(self._achatar_dicionario(valor))
            elif isinstance(valor, str):
                resultado[chave.lower()] = valor
        return resultado

    def _carregar_e_achatar_json(self, caminho: str | Path) -> dict[str, str]:
        path = Path(caminho)
        if not path.exists():
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                dados = json.load(f)
            if isinstance(dados, dict):
                return self._achatar_dicionario(dados)
            return {}
        except (json.JSONDecodeError, OSError):
            return {}

    def _aplicar_lexicon(self, texto: str) -> str:
        if not self.lexicon:
            return texto

        chaves_ordenadas = sorted(self.lexicon.keys(), key=len, reverse=True)
        padrao = re.compile(
            r"\b(" + "|".join(re.escape(k) for k in chaves_ordenadas) + r")\b",
            flags=re.IGNORECASE,
        )

        def substituir(match: re.Match) -> str:
            original = match.group(0)
            substituto = self.lexicon[original.lower()]

            if original.isupper() and len(original) > 1:
                return substituto.upper()
            if original[0].isupper():
                return substituto[0].upper() + substituto[1:]
            return substituto

        return padrao.sub(substituir, texto)

    def _aplicar_regras_nasais(self, texto: str) -> str:
        texto = re.sub(r"([a-záéíóúâêôç])ão\b", r"\1ãu", texto, flags=re.IGNORECASE)
        texto = re.sub(r"([a-záéíóúâêôç])ãos\b", r"\1ãus", texto, flags=re.IGNORECASE)
        texto = re.sub(r"([a-záéíóúâêôç])ões\b", r"\1õis", texto, flags=re.IGNORECASE)
        return texto

    def processar(self, texto: str) -> str:
        # 1. Remove caracteres de controle invisíveis, preservando quebras de linha (\n)
        texto = "".join(char for char in texto if char.isprintable() or char in "\n\t")

        # 2. Normaliza espaços horizontais sem destruir as quebras de linha dos parágrafos
        linhas = [re.sub(r"[ \t]+", " ", linha).strip() for linha in texto.split("\n")]
        texto = "\n".join(linha for linha in linhas if linha)

        # 3. Aplica o léxico personalizado (categorias achatadas)
        texto = self._aplicar_lexicon(texto)

        # 4. Aplica regras gerais de reforço nasal
        texto = self._aplicar_regras_nasais(texto)

        # 5. Aplica regras extras do ipa_rules.json (se houver)
        for padrao, substituto in self.ipa_rules.items():
            texto = re.sub(padrao, substituto, texto, flags=re.IGNORECASE)

        return texto