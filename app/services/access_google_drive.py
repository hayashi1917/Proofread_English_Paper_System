import os.path
import io
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/drive']

def download_knowledge_tex_files(folder_id: str) -> list[bytes]:
    """ 
    ナレッジ構築用のファイルをダウンロードする。
    入力: フォルダID
    出力: ダウンロードしたファイルのバイトストリームを格納したリスト
    """
    tex_files = []
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
        page_token = None
        while True:
            resp = service.files().list(
                q=f"'{folder_id}' in parents",
                fields="files(id,name,mimeType),nextPageToken",
                pageToken=page_token,
                pageSize=1000,
            ).execute()
            for f in resp.get("files", []):
                tex_file = {}
                request = service.files().get_media(fileId=f["id"])
                tex_file["name"] = f["name"]
                tex_file["knowledge_type"] = "学会フォーマット"
                fh = io.BytesIO()
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    _, done = downloader.next_chunk()
                fh.seek(0)
                tex_file["content"] = fh.read()
                tex_files.append(tex_file)
                print("tex_file:", tex_file)
            page_token = resp.get("nextPageToken", None)
            if page_token is None:
                break
        return tex_files
    
    except HttpError as error:
        print(f"An error occurred: {error}")
        return []


def download_knowledge_pdf_files(folder_id: str) -> list[dict]:
    """ 
    ナレッジ構築用のPDFファイルをダウンロードする。
    入力: フォルダID
    出力: ダウンロードしたPDFファイルの情報とバイトストリームを格納したリスト
    """
    pdf_files = []
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
        page_token = None
        while True:
            resp = service.files().list(
                q=f"'{folder_id}' in parents and mimeType='application/pdf'",
                fields="files(id,name,mimeType),nextPageToken",
                pageToken=page_token,
                pageSize=1000,
            ).execute()
            for f in resp.get("files", []):
                pdf_file = {}
                request = service.files().get_media(fileId=f["id"])
                pdf_file["name"] = f["name"]
                pdf_file["knowledge_type"] = "一般的な論文"
                fh = io.BytesIO()
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    _, done = downloader.next_chunk()
                fh.seek(0)
                pdf_file["content"] = fh.read()
                pdf_files.append(pdf_file)
                print("pdf_file:", pdf_file["name"])
            page_token = resp.get("nextPageToken", None)
            if page_token is None:
                break
        return pdf_files
    
    except HttpError as error:
        print(f"An error occurred: {error}")
        return []


def download_pre_proofread_tex_file(folder_id: str) -> bytes:
    """ 
    プルーフリード前のファイルをダウンロードする。
    入力: フォルダID
    出力: ダウンロードしたファイルのバイトストリーム
    """
    
    # 最初のファイルを返す（通常は1つだけ）
    tex_files = download_knowledge_tex_files(folder_id)
    return tex_files[0]["content"]