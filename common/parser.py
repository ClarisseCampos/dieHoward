from pathlib import Path
from pypdf import PdfReader
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup

class DocumentParser:
    @staticmethod
    def extrair_texto(caminho_arquivo: str | Path) -> str:
        """Lê a extensão do arquivo e direciona para o extrator correto."""
        path = Path(caminho_arquivo)
        extensao = path.suffix.lower()

        if extensao == '.txt':
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        
        elif extensao == '.pdf':
            return DocumentParser._extrair_pdf(path)
        
        elif extensao == '.epub':
            return DocumentParser._extrair_epub(path)
        
        else:
            raise ValueError(f"Formato de arquivo não suportado: {extensao}")

    @staticmethod
    def _extrair_pdf(path: Path) -> str:
        leitor = PdfReader(str(path))
        texto_completo = []
        for pagina in leitor.pages:
            texto_pagina = pagina.extract_text()
            if texto_pagina:
                texto_completo.append(texto_pagina)
        return "\n".join(texto_completo)

    @staticmethod
    def _extrair_epub(path: Path) -> str:
        livro = epub.read_epub(str(path))
        texto_completo = []
        
        # Percorre todos os documentos (capítulos) dentro do EPUB
        for item in livro.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            conteudo_html = item.get_content()
            sopa = BeautifulSoup(conteudo_html, 'html.parser')
            texto_completo.append(sopa.get_text(separator='\n'))
            
        return "\n".join(texto_completo)