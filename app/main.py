from dotenv import load_dotenv
import os
import logging
import sys

load_dotenv(".env.local")

# ログ設定を早期に初期化
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[logging.StreamHandler(sys.stdout)]
)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .api.api import api_router
import uvicorn

# カスタムログ設定をインポート（追加設定のため）
from .services.shared.logging_utils import logger

async def lifespan(app: FastAPI):
    yield

app = FastAPI(
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静的ファイルの配信設定
app.mount("/static", StaticFiles(directory="static"), name="static")

# API ルーターを含める
app.include_router(api_router)  

# ルートパスでHTMLファイルを返す
@app.get("/")
async def read_root():
    return FileResponse('static/index.html')

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3000, reload=True, log_level="info")
