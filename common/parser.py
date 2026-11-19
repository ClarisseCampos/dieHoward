import re
from pathlib import Path
from pypdf import PdfReader
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup

class DocumentParser:
    @staticmethod
    def extrair_texto(caminho_arquivo: str | Path) -> str:
        capitulos = DocumentParser.extrair_capitulos(caminho_arquivo)
        return "\n\n".join(cap["texto"] for cap in capitulos if cap["texto"].strip())

    @staticmethod
    def extrair_capitulos(caminho_arquivo: str | Path) -> list[dict[str, str]]:
        path = Path(caminho_arquivo)
        extensao = path.suffix.lower()

        if extensao == '.txt':
            return DocumentParser._extrair_capitulos_txt(path)
        elif extensao == '.pdf':
            return DocumentParser._extrair_capitulos_pdf(path)
        elif extensao == '.epub':
            return DocumentParser._extrair_capitulos_epub(path)
        else:
            raise ValueError(f"Formato de arquivo não suportado: {extensao}")

    @staticmethod
    def _separar_por_regex(texto: str, titulo_padrao: str) -> list[dict[str, str]]:
        """Plano B: Fatiar texto buscando linhas que comecem com 'Capítulo' ou 'Parte'"""
        padrao = re.compile(r'(?m)^((?:cap[íi]tulo|parte)\s+[^\n]+)$', re.IGNORECASE)
        partes = padrao.split(texto)

        if len(partes) <= 1:
            return [{"titulo": titulo_padrao, "texto": texto}]

        capitulos = []
        if partes[0].strip():
            capitulos.append({"titulo": "Introducao", "texto": partes[0].strip()})

        for i in range(1, len(partes), 2):
            titulo = partes[i].strip()
            conteudo = partes[i + 1].strip() if i + 1 < len(partes) else ""
            if conteudo:
                capitulos.append({"titulo": titulo, "texto": f"{titulo}.\n{conteudo}"})

        return capitulos

    @staticmethod
    def _extrair_capitulos_txt(path: Path) -> list[dict[str, str]]:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            texto = f.read()
        return DocumentParser._separar_por_regex(texto, path.stem)

    @staticmethod
    def _extrair_capitulos_pdf(path: Path) -> list[dict[str, str]]:
        leitor = PdfReader(str(path))
        total_paginas = len(leitor.pages)
        marcadores = []

        def coletar_marcadores(itens):
            for item in itens:
                if isinstance(item, list):
                    coletar_marcadores(item)
                else:
                    try:
                        pag_idx = leitor.get_destination_page_number(item)
                        marcadores.append((item.title.strip(), pag_idx))
                    except Exception:
                        pass

        if leitor.outline:
            coletar_marcadores(leitor.outline)

        marcadores_unicos = []
        paginas_vistas = set()
        for titulo, pag in marcadores:
            if pag not in paginas_vistas:
                marcadores_unicos.append((titulo, pag))
                paginas_vistas.add(pag)

        # Se não tiver marcadores nativos, extrai tudo e usa o Plano B (Regex)
        if not marcadores_unicos:
            texto_completo = "\n".join([p.extract_text() or "" for p in leitor.pages])
            return DocumentParser._separar_por_regex(texto_completo, path.stem)

        capitulos = []
        for idx, (titulo, pag_inicio) in enumerate(marcadores_unicos):
            pag_fim = (
                marcadores_unicos[idx + 1][1]
                if idx + 1 < len(marcadores_unicos)
                else total_paginas
            )
            trecho_paginas = [
                leitor.pages[p].extract_text() or ""
                for p in range(pag_inicio, pag_fim)
            ]
            texto_cap = "\n".join(trecho_paginas).strip()
            if texto_cap:
                capitulos.append({"titulo": titulo, "texto": texto_cap})

        return capitulos

    @staticmethod
    def _extrair_capitulos_epub(path: Path) -> list[dict[str, str]]:
        livro = epub.read_epub(str(path))
        capitulos = []

        for idx, item in enumerate(livro.get_items_of_type(ebooklib.ITEM_DOCUMENT), 1):
            conteudo_html = item.get_content()
            sopa = BeautifulSoup(conteudo_html, 'html.parser')
            texto = sopa.get_text(separator='\n').strip()

            if not texto:
                continue

            heading = sopa.find(['h1', 'h2', 'h3'])
            titulo = heading.get_text(strip=True) if heading else f"Capitulo_{idx:02d}"
            capitulos.append({"titulo": titulo, "texto": texto})

        # Se o EPUB empacotou o livro todo num arquivo só, usa o Plano B (Regex)
        if len(capitulos) <= 1:
            return DocumentParser._separar_por_regex(capitulos[0]["texto"] if capitulos else "", path.stem)

        return capitulos