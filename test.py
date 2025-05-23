import os.path
import io
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError
from langchain.text_splitter import LatexTextSplitter
from typing import List, Union

SCOPES = ['https://www.googleapis.com/auth/drive']

def download_folder_contents(folder_id, output_dir):
    """Downloads all files from a specific Google Drive folder.
    
    Args:
        folder_id (str): The ID of the Google Drive folder to download from
        output_dir (str): The local directory to save the downloaded files
    """
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("drive", "v3", credentials=creds)
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # List all files in the folder
        results = service.files().list(
            q=f"'{folder_id}' in parents",
            fields="nextPageToken, files(id, name, mimeType)"
        ).execute()
        
        items = results.get("files", [])
        
        if not items:
            print("No files found in the folder.")
            return
            
        print(f"Found {len(items)} files. Starting download...")
        
        for item in items:
            file_id = item['id']
            file_name = item['name']
            mime_type = item['mimeType']
            
            # Skip Google Docs/Sheets/Slides files
            if mime_type.startswith('application/vnd.google-apps'):
                print(f"Skipping Google Workspace file: {file_name}")
                continue
                
            print(f"Downloading: {file_name}")
            
            request = service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                print(f"Download {int(status.progress() * 100)}%")
                
            # Save the file
            file_path = os.path.join(output_dir, file_name)
            with open(file_path, 'wb') as f:
                f.write(fh.getvalue())
                
        print("Download completed!")
        
    except HttpError as error:
        print(f"An error occurred: {error}")

def chunking_tex(tex_file: str) -> list[str]:
    """
    テキストファイルをチャンク分割する。
    入力: Latexファイルのバイトストリーム
    出力: チャンク分割したLatexファイルの段落毎のリスト
    """
    with open(tex_file, "r") as f:
        tex_file = f.read()
    splitter = LatexTextSplitter(chunk_size=500, chunk_overlap=200)
    chunks = splitter.split_text(tex_file)
    print("chunks:", chunks)
    return chunks


import re

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
    return data.decode("utf-8", errors="replace") 

def get_document_body(latex_string):
    """
    LaTeX文字列から \\begin{document} と \\end{document} の間の内容を抽出します。
    見つからない場合は None を返します。
    """
    match = re.search(r"\\begin\{document\}(.*?)\\end\{document\}", latex_string, re.DOTALL)
    if match:
        return match.group(1)
    else:
        print("警告: \\begin{document}...\\end{document} が見つかりませんでした。")
        return None


def clean_section_title(raw_title_content):
    """
    セクションタイトルの内容文字列（波括弧の中身）から基本的な書式コマンドを除去し、
    人間が読みやすい形に整形します。
    例: "My \\textbf{Important} Title" -> "My Important Title"
    """
    if raw_title_content is None:
        return None
        
    title = raw_title_content
    
    # LaTeXの改行コマンド (\\ や \newline) をスペースに置換
    title = re.sub(r"\\\\(?:\[[^\]]*\])?|\\newline", " ", title)

    # 一般的な書式設定コマンドを除去（中身のテキストは残す）
    # 必要に応じてこのリストは拡張してください
    formatting_commands = [
        'textbf', 'textit', 'texttt', 'emph', 'textsl', 'textsc', 'textnormal',
        'bf', 'it', 'tt', 'rm', 'sf', 'sc', 'ul', # 古い形式のコマンド
        'MakeUppercase', 'MakeLowercase', 'uppercase', 'lowercase'
    ]
    for cmd in formatting_commands:
        # \cmd{content} -> content
        title = re.sub(r'\\' + cmd + r'\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}', r'\1', title)
        # \cmd (後にスペースか行末が続く場合) -> 空白 (コマンド自体を除去)
        title = re.sub(r'\\' + cmd + r'(?=\s|$)', '', title)

    # LaTeXの数学モードのデリミタ ($...$, $$...$$ など) や特殊な記号コマンドはここでは単純除去していません。
    # タイトル内に複雑なLaTeX表現がある場合は、より高度な処理が必要です。

    # LaTeXの一般的なエスケープ文字を通常の文字に戻す (簡易版)
    latex_escapes = {
        r"\\%": "%", r"\\&": "&", r"\\#": "#", r"\\_": "_", r"~": " ",
        r"\\,": " ", r"\\thinspace": " ", r"\\enspace": " ", r"\\quad": " ", r"\\qquad": " ",
        r"\\{": "{", r"\\}": "}", r"\\\$": "$", # これらは文脈に注意が必要
        r"``": '"', r"''": '"', r"`": "'"
    }
    for tex_char, normal_char in latex_escapes.items():
        title = title.replace(tex_char, normal_char)
    
    # 残っているかもしれない単純なコマンド (例: \LaTeX) は、ここでは除去しません。
    # 必要であれば追加: title = re.sub(r'\\[a-zA-Z@]+', '', title)

    # 空の波括弧などを除去
    title = re.sub(r"\{\s*\}", "", title)
    title = re.sub(r"\[\s*\]", "", title)

    # 連続する空白を一つにまとめ、前後の空白を除去
    title = re.sub(r'\s+', ' ', title).strip()
    
    return title


def split_tex_by_section(latex_string):
    """
    LaTeX文字列を \\section コマンドで分割し、各セクションの情報をリストとして返します。
    """
    document_body = get_document_body(latex_string)
    if document_body is None:
        return []

    # \section コマンドのパターン。アスタリスク付き、オプション引数も考慮。
    # キャプチャグループ:
    # 1: \sectionコマンド全体 (例: \section*{My Title} や \section[short]{My Title})
    # 2: タイトルの波括弧の中身 (例: My Title や My \textbf{Title})
    #    ネストした波括弧にも対応: ([^{}]*(?:\{[^{}]*\}[^{}]*)*)
    section_pattern = r"(\\section\*?(?:\[[^\]]*\])?\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\})"
    
    # re.splitは、パターンにマッチした部分と、それによって区切られた部分を交互にリストにします。
    # パターン内にキャプチャグループがあると、そのグループの内容もリストに含まれます。
    # parts の構造: [text_before_sec1, sec1_full_cmd, sec1_title_content, text_after_sec1, sec2_full_cmd, sec2_title_content, ...]
    parts = re.split(section_pattern, document_body)
    
    extracted_sections = []
    
    # 最初の \section より前の部分 (parts[0])
    # これを「導入部」または「アブストラクト」などとして扱います。
    if parts and parts[0].strip():
        extracted_sections.append({
            'section_command_raw': None,    # \section コマンドではないため None
            'title_content_raw': None,      # 元のタイトル内容もない
            'title_clean': "導入部 / アブストラクト",
            'content_raw': parts[0].strip() # 内容は生のLaTeX
        })
        
    # \section コマンドで分割された部分の処理
    # parts のインデックスは1から始まり、3つ組 (コマンド全体, タイトル内容, 後続テキスト) で進みます。
    idx = 1
    while idx < len(parts):
        section_full_command = parts[idx]
        section_title_content_raw = parts[idx+1] # 波括弧の中身
        
        # 次のセクションコマンドまでのテキストが、このセクションの内容になります。
        content_after_section_raw = parts[idx+2].strip() if (idx+2) < len(parts) else ""

        cleaned_title = clean_section_title(section_title_content_raw)
        
        extracted_sections.append({
            'section_command_raw': section_full_command,
            'title_content_raw': section_title_content_raw,
            'title_clean': cleaned_title,
            'content_raw': content_after_section_raw
        })
        idx += 3 # 次のセクションの組へ
        
    return extracted_sections

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

def split_tex_by_langchain(latex_string):
    splitter = LatexTextSplitter(chunk_size=500, chunk_overlap=200)
    chunks = splitter.split_text(latex_string)
    return chunks

def main():
    tex_file = "neurips_2024.tex"

    with open(tex_file, "r") as f:
        tex_file = f.read()

    sections = split_latex_by_section(tex_file)

    for section in sections:
        print("チャンク：")
        print(section)
        print("--------------------------------")


if __name__ == "__main__":
    main()
# [END drive_quickstart]


