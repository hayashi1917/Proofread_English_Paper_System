from typing import List, Dict, Any, Union
from langchain_text_splitters import LatexTextSplitter  
from TexSoup import TexSoup, TexNode
import re



# def chunking_tex(tex_data: bytes | str) -> List[str]:
#     """
#     LaTeX ソースをチャンク分割する
#     Parameters
#     ----------
#     tex_data : bytes | str
#         ・bytes なら UTF-8 / Latin-1 などでデコードしてから処理  
#         ・str ならそのまま

#     Returns
#     -------
#     chunks : list[str]
#         チャンク済み文字列のリスト
#     """
#     text = _ensure_str(tex_data)
#     return _splitter.split_text(text)




SECTION_RE = re.compile(
    r'\\(?:section)\*?\s*{[^}]*}',
    flags=re.IGNORECASE
)

def _ensure_str(data: Union[str, bytes]) -> str:
    """bytes → str を安全に変換（UTF-8→Shift-JISフォールバック）"""
    if isinstance(data, str):
        return data
    for enc in ("utf-8", "utf-8-sig", "shift_jis", "cp932"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")     # どうしても通らなければ置換復号

def split_latex_by_splitter(latex: Union[str, bytes]) -> List[str]:
    _splitter = LatexTextSplitter(chunk_size=2000, chunk_overlap=100)
    text = _ensure_str(latex)
    return _splitter.split_text(text)

def split_latex_by_section(latex: Union[str, bytes]) -> List[str]:
    """LaTeX 文字列をセクション区切りで分割し、最低 1 チャンク返す"""
    text = _ensure_str(latex)
    # 前文（\begin{document} 以前）は要らない場合が多いので除外
    doc_start = text.find(r"\begin{document}")
    if doc_start != -1:
        text = text[doc_start:]

    matches = list(SECTION_RE.finditer(text))
    if not matches:                      # セクションが無い ⇢ 全文 1 チャンク
        return [text.strip()]

    chunks = []
    for i, m in enumerate(matches):
        start = m.start()
        end   = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        chunks.append(text[start:end].strip())

    return chunks

# def split_latex_by_section(latex: str) -> List[str]:
#     latex = _ensure_str(latex)       # ★ 追加 ★
#     soup = TexSoup(latex)
#     sections, buffer = [], []
#     in_section = False

#     for node in soup.all:
#         if isinstance(node, TexNode) and node.name == "section":
#             if in_section:
#                 sections.append("".join(buffer).strip())
#                 buffer.clear()
#             in_section = True
#         if in_section:
#             buffer.append(str(node))

#     if buffer:
#         sections.append("".join(buffer).strip())
#     return sections

def chunking_tex_files(tex_files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []

    for tex in tex_files:
        chunks = split_latex_by_splitter(tex["content"])
        print(f"{tex['name']} → {len(chunks)} 個に分割")

        results.append(
            {
                "name": tex["name"],
                "knowledge_type": tex["knowledge_type"],
                "chunks": [
                    {"chunk_id": i, "chunk_text": c} for i, c in enumerate(chunks)
                ],
            }
        )
    return results
