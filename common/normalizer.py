import json
import re
from pathlib import Path

class TextNormalizer:
    def __init__(self, rules_path="common/config/ipa_rules.json", lexicon_path="common/config/lexicon.json"):
        self.rules_path = Path(rules_path)
        self.lexicon_path = Path(lexicon_path)
        self.rules = self._load_json(self.rules_path)
        self.lexicon = self._load_json(self.lexicon_path)

    def _load_json(self, path: Path) -> dict:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _aplicar_substituicoes(self, texto: str, mapa_substituicoes: dict) -> str:
        """Aplica substituições com verificação recursiva para dicionários aninhados."""
        for chave, valor in mapa_substituicoes.items():
            if isinstance(valor, dict):
                # Se for um grupo/categoria (ex: {"g1": {"termo": "troca"}}), navega recursivamente
                texto = self._aplicar_substituicoes(texto, valor)
            elif isinstance(valor, str):
                # Aplica a substituição se o valor for uma string válida
                padrao = re.compile(r'\b' + re.escape(chave) + r'\b', re.IGNORECASE)
                texto = padrao.sub(valor, texto)
        return texto

    def processar(self, texto: str) -> str:
        """Sanitiza caracteres inválidos e aplica as regras lexicais e fonéticas no texto."""
        # 1. Remove caracteres de controle invisíveis e bytes nulos (\x00, \x11, etc) de PDFs e EPUBs
        texto_limpo = ''.join(char for char in texto if char.isprintable() or char in '\n\t')
        
        # 2. Normaliza múltiplos espaços/quebras de linha excessivas para evitar blocos vazios no TTS
        texto_processado = re.sub(r'[ \t]+', ' ', texto_limpo)
        texto_processado = re.sub(r'\n{3,}', '\n\n', texto_processado).strip()

        # 3. Aplica as substituições do léxico
        if self.lexicon:
            texto_processado = self._aplicar_substituicoes(texto_processado, self.lexicon)

        # 4. Aplica as regras de diacríticos e transliteração
        if self.rules:
            texto_processado = self._aplicar_substituicoes(texto_processado, self.rules)

        return texto_processado