import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/drive']

def get_google_drive_credentials() -> Credentials:
    """
    Google Drive API用の認証情報を取得する共通関数
    
    Returns:
        Credentials: Google Drive API用の認証情報
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
    
    return creds

def get_google_drive_service():
    """
    Google Drive APIサービスオブジェクトを取得する
    
    Returns:
        Google Drive APIサービスオブジェクト
    """
    credentials = get_google_drive_credentials()
    return build("drive", "v3", credentials=credentials)