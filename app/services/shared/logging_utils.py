"""
ログ出力用のユーティリティ関数
"""
import logging
from typing import Any
from app.services.proofreading.config.proofreading_config import ENABLE_DEBUG_LOGGING

logger = logging.getLogger(__name__)

def log_proofreading_debug(message: str, data: Any = None) -> None:
    """
    校正処理のデバッグログを出力
    
    Args:
        message (str): ログメッセージ
        data (Any, optional): 出力するデータ
    """
    if ENABLE_DEBUG_LOGGING:
        if data is not None:
            logger.debug(f"{message}: {data}")
        else:
            logger.debug(message)

def log_proofreading_info(message: str) -> None:
    """
    校正処理の情報ログを出力
    
    Args:
        message (str): ログメッセージ
    """
    logger.info(message)

def log_proofreading_error(message: str, error: Exception = None) -> None:
    """
    校正処理のエラーログを出力
    
    Args:
        message (str): ログメッセージ
        error (Exception, optional): 例外オブジェクト
    """
    if error:
        logger.error(f"{message}: {error}")
    else:
        logger.error(message)