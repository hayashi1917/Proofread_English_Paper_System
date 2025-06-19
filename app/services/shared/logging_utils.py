"""
ログ出力用のユーティリティ関数
"""
import logging
import sys
from typing import Any
from app.services.proofreading.config.proofreading_config import ENABLE_DEBUG_LOGGING

# ロガーの設定
logger = logging.getLogger(__name__)

# ハンドラーが設定されていない場合のみ設定
if not logger.handlers:
    # 標準出力ハンドラーを作成
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
    # フォーマッターを設定
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    # ハンドラーをロガーに追加
    logger.addHandler(console_handler)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False  # 親ロガーへの伝播を停止

# ルートロガーも標準出力に設定
root_logger = logging.getLogger()
if not root_logger.handlers:
    root_console_handler = logging.StreamHandler(sys.stdout)
    root_console_handler.setLevel(logging.INFO)
    
    root_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    root_console_handler.setFormatter(root_formatter)
    
    root_logger.addHandler(root_console_handler)
    root_logger.setLevel(logging.INFO)

def log_proofreading_debug(message: str, data: Any = None) -> None:
    """
    校正処理のデバッグログを出力
    
    Args:
        message (str): ログメッセージ
        data (Any, optional): 出力するデータ
    """
    if ENABLE_DEBUG_LOGGING:
        log_msg = f"[DEBUG] {message}: {data}" if data is not None else f"[DEBUG] {message}"
        print(log_msg)  # 標準出力に直接出力
        logger.debug(f"{message}: {data}" if data is not None else message)

def log_proofreading_info(message: str) -> None:
    """
    校正処理の情報ログを出力
    
    Args:
        message (str): ログメッセージ
    """
    print(f"[INFO] {message}")  # 標準出力に直接出力
    logger.info(message)

def log_proofreading_error(message: str, error: Exception = None) -> None:
    """
    校正処理のエラーログを出力
    
    Args:
        message (str): ログメッセージ
        error (Exception, optional): 例外オブジェクト
    """
    error_msg = f"[ERROR] {message}: {error}" if error else f"[ERROR] {message}"
    print(error_msg)  # 標準出力に直接出力
    if error:
        logger.error(f"{message}: {error}")
    else:
        logger.error(message)