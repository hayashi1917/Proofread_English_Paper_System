"""
カスタム例外クラスの定義
"""

class ServiceError(Exception):
    """サービス層の基底例外クラス"""
    pass

class GoogleDriveError(ServiceError):
    """Google Drive操作関連のエラー"""
    pass

class VectorStoreError(ServiceError):
    """ベクターストア操作関連のエラー"""
    pass

class ProofreadingError(ServiceError):
    """校正処理関連のエラー"""
    pass

class ChunkingError(ServiceError):
    """テキスト分割処理関連のエラー"""
    pass

class KnowledgeExtractionError(ServiceError):
    """知識抽出処理関連のエラー"""
    pass