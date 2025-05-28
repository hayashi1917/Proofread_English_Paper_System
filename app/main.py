from dotenv import load_dotenv
import os

load_dotenv(".env.local")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .api.api import api_router
import uvicorn

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
