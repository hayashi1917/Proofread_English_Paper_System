"""
英語学術論文校正サービス

Google DriveやアップロードされたLaTeX文書を校正し、
学術出版品質の英語に改善するための包括的なサービスを提供します。
"""
from typing import List, Dict, Any

from app.services.proofreading.core.proofreading_paper_engine import ProofreadingPaperEngine
from app.services.shared.logging_utils import log_proofreading_info
from app.services.shared.exceptions import ProofreadingError


class EnglishPaperProofreadingService:
    """英語学術論文校正サービス"""
    
    def __init__(self):
        self.engine = ProofreadingPaperEngine()
    
    def proofread_english_paper(self) -> List[Dict[str, Any]]:
        """
        Google Driveから校正対象論文をダウンロードして校正
        
        環境変数で設定されたGoogle Driveフォルダから校正前の論文を取得し、
        知識ベースを活用した高品質な校正を実行します。
        
        Returns:
            List[Dict[str, Any]]: 校正結果のリスト
            各結果は以下の構造:
            - "pre_proofread": 校正前テキスト
            - "post_proofread": 校正後テキスト  
            - "description": 校正根拠・説明
            - "queries": 使用したHyDEクエリ
            - "knowledge": 参照した知識ベース
            
        Raises:
            ProofreadingError: 校正処理に失敗した場合
            
        Note:
            環境変数 ENGLISH_PAPER_BEFORE_PROOFREADING_FOLDER_ID の設定が必要
        """
        try:
            log_proofreading_info("Google Drive論文校正サービスを開始")
            return self.engine.proofread_from_google_drive()
        except Exception as e:
            raise ProofreadingError(f"Google Drive論文校正中にエラーが発生しました: {e}")
    
    def proofread_english_paper_posted_file(self, tex_file: str) -> List[Dict[str, Any]]:
        """
        アップロードされたLaTeXファイルを校正（知識ベース使用）
        
        Args:
            tex_file (str): アップロードされたLaTeXファイルの内容
            
        Returns:
            List[Dict[str, Any]]: 校正結果のリスト
            各結果は以下の構造:
            - "pre_proofread": 校正前テキスト
            - "post_proofread": 校正後テキスト
            - "description": 校正根拠・説明
            - "queries": 使用したHyDEクエリ
            - "knowledge": 参照した知識ベース
            
        Raises:
            ProofreadingError: 校正処理に失敗した場合
        """
        try:
            log_proofreading_info("アップロードファイル校正サービスを開始（知識ベースあり）")
            return self.engine.proofread_uploaded_file(tex_file, use_knowledge=True)
        except Exception as e:
            raise ProofreadingError(f"アップロードファイル校正中にエラーが発生しました: {e}")
    
    def proofread_english_paper_without_knowledge(self, tex_file: str) -> List[Dict[str, Any]]:
        """
        アップロードされたLaTeXファイルを校正（知識ベース不使用）
        
        知識ベースを使用せず、LLMの基本的な校正能力のみで論文を校正します。
        
        Args:
            tex_file (str): LaTeXファイルの内容
            
        Returns:
            List[Dict[str, Any]]: 校正結果のリスト
            各結果は以下の構造:
            - "pre_proofread": 校正前テキスト
            - "post_proofread": 校正後テキスト
            - "description": 校正根拠・説明
            - "queries": 空のリスト
            - "knowledge": 空の文字列
            
        Raises:
            ProofreadingError: 校正処理に失敗した場合
        """
        try:
            log_proofreading_info("アップロードファイル校正サービスを開始（知識ベースなし）")
            return self.engine.proofread_uploaded_file(tex_file, use_knowledge=False)
        except Exception as e:
            raise ProofreadingError(f"知識ベースなし校正中にエラーが発生しました: {e}")
    
    def proofread_with_options(
        self, 
        tex_file: str = None,
        use_google_drive: bool = False,
        use_knowledge: bool = True
    ) -> List[Dict[str, Any]]:
        """
        オプション指定による柔軟な校正実行
        
        Args:
            tex_file (str, optional): LaTeXファイル内容（Google Drive使用時は不要）
            use_google_drive (bool): Google Driveからファイル取得するかどうか
            use_knowledge (bool): 知識ベースを使用するかどうか
            
        Returns:
            List[Dict[str, Any]]: 校正結果のリスト
            
        Raises:
            ProofreadingError: 校正処理に失敗した場合
        """
        try:
            if use_google_drive:
                if not use_knowledge:
                    raise ProofreadingError("Google Drive使用時は知識ベースが必須です")
                return self.proofread_english_paper()
            else:
                if not tex_file:
                    raise ProofreadingError("アップロードファイル使用時はtex_fileが必要です")
                return self.proofread_uploaded_file(tex_file, use_knowledge)
        except Exception as e:
            raise ProofreadingError(f"オプション指定校正中にエラーが発生しました: {e}")


# 下位互換性のためのサービスインスタンス
_service = EnglishPaperProofreadingService()

def proofread_english_paper() -> List[Dict[str, Any]]:
    """
    下位互換性のための関数ラッパー
    """
    return _service.proofread_english_paper()

def proofread_english_paper_posted_file(tex_file: str) -> List[Dict[str, Any]]:
    """
    下位互換性のための関数ラッパー
    """
    return _service.proofread_english_paper_posted_file(tex_file)

def proofread_english_paper_without_knowledge(tex_file: str) -> List[Dict[str, Any]]:
    """
    下位互換性のための関数ラッパー
    """
    return _service.proofread_english_paper_without_knowledge(tex_file)