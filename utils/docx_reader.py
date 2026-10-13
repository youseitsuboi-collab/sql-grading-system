from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P


def iter_block_items(parent):
    """
    Word文書内の段落と表を出現順に取得する
    """
    for child in parent.element.body.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl):
            yield Table(child, parent)


def read_docx(file_path: str) -> str:
    doc = Document(file_path)
    texts = []

    for block in iter_block_items(doc):
        # 段落
        if isinstance(block, Paragraph):
            text = block.text.strip()
            if text:
                texts.append(text)

        # 表
        elif isinstance(block, Table):
            for row in block.rows:
                cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if cells:
                    texts.append("\n".join(cells))

    return "\n".join(texts)
