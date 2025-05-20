import os.path
import io
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError
from langchain.text_splitter import LatexTextSplitter
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

def main():
    tex_file = "neurips_2024.tex"

    chunks = chunking_tex(tex_file)
    print("chunks:", chunks)

if __name__ == "__main__":
    main()
# [END drive_quickstart]


