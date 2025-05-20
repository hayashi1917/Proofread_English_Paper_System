from typing import List, Dict, Any
from langchain_text_splitters import LatexTextSplitter   # ← v0.2 以降はこちら

# 共通の splitter は再利用すると速い
_splitter = LatexTextSplitter(chunk_size=500, chunk_overlap=200)

def _ensure_str(data: bytes | str, *, encodings: tuple[str, ...] = ("utf-8", "latin-1")) -> str:
    """
    bytes → str 変換ユーティリティ
    - data が str ならそのまま返す
    - bytes なら encodings を順に試して decode
    """
    if isinstance(data, str):
        return data

    for enc in encodings:
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    # すべて失敗したら置換付き decode
    return data.decode(encodings[0], errors="replace")


def chunking_tex(tex_data: bytes | str) -> List[str]:
    """
    LaTeX ソースをチャンク分割する
    Parameters
    ----------
    tex_data : bytes | str
        ・bytes なら UTF-8 / Latin-1 などでデコードしてから処理  
        ・str ならそのまま

    Returns
    -------
    chunks : list[str]
        チャンク済み文字列のリスト
    """
    text = _ensure_str(tex_data)
    return _splitter.split_text(text)


def chunking_tex_files(tex_files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    LaTeX ファイル群をチャンク化してメタデータとともに返す

    Parameters
    ----------
    tex_files : [
        {
            "name": str,
            "knowledge_type": str,
            "content": bytes | str
        }, ...
    ]

    Returns
    -------
    [
        {
            "name": str,
            "knowledge_type": str,
            "chunks": [
                {"chunk_id": int, "chunk_text": str}, ...
            ]
        }, ...
    ]
    """
    results: List[Dict[str, Any]] = []

    for tex in tex_files:
        chunks = chunking_tex(tex["content"])
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
