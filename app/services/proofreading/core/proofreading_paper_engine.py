"""
英語論文校正のワークフローエンジン
"""
import os
from typing import List, Dict, Any

from app.services.knowledge.access_google_drive import download_pre_proofread_tex_file
from app.services.knowledge.chunking_file import chunking_tex_file
from app.services.proofreading.proofread_paper_by_knowledge import (
    proofread_paper_by_knowledge,
    proofread_paper_without_knowledge
)
from app.services.shared.logging_utils import log_proofreading_info, log_proofreading_debug
from app.services.proofreading.config.proofreading_paper_config import (
    ENGLISH_PAPER_FOLDER_ID_KEY,
    MIN_TEX_FILE_SIZE,
    MAX_TEX_FILE_SIZE,
    ProofreadingMode
)
from app.services.shared.exceptions import ProofreadingError


class ProofreadingPaperEngine:
    """英語論文校正ワークフローエンジン"""
    
    def __init__(self):
        self.folder_id = self._get_folder_id()
    
    def _get_folder_id(self) -> str:
        """
        環境変数から校正前論文フォルダIDを取得
        
        Returns:
            str: フォルダID
            
        Raises:
            ProofreadingError: フォルダIDが設定されていない場合
        """
        folder_id = os.getenv(ENGLISH_PAPER_FOLDER_ID_KEY)
        if not folder_id:
            raise ProofreadingError(
                f"環境変数 '{ENGLISH_PAPER_FOLDER_ID_KEY}' が設定されていません"
            )
        return folder_id
    
    def _validate_tex_content(self, tex_content: str) -> None:
        """
        LaTeXコンテンツの妥当性を検証
        
        Args:
            tex_content (str): LaTeXコンテンツ
            
        Raises:
            ProofreadingError: コンテンツが無効な場合
        """
        if not tex_content or not tex_content.strip():
            raise ProofreadingError("LaTeXコンテンツが空です")
        
        content_size = len(tex_content.encode('utf-8'))
        
        if content_size < MIN_TEX_FILE_SIZE:
            raise ProofreadingError(f"ファイルサイズが小さすぎます (最小: {MIN_TEX_FILE_SIZE}bytes)")
        
        if content_size > MAX_TEX_FILE_SIZE:
            raise ProofreadingError(f"ファイルサイズが大きすぎます (最大: {MAX_TEX_FILE_SIZE}bytes)")
    
    def _process_tex_content(
        self, 
        tex_content: str, 
        mode: str = ProofreadingMode.WITH_KNOWLEDGE
    ) -> List[Dict[str, Any]]:
        """
        LaTeXコンテンツを処理して校正結果を生成
        
        Args:
            tex_content (str): LaTeXコンテンツ
            mode (str): 校正モード
            
        Returns:
            List[Dict[str, Any]]: 校正結果
            
        Raises:
            ProofreadingError: 処理に失敗した場合
        """
        try:
            log_proofreading_debug("LaTeXコンテンツ処理開始", {
                "mode": mode,
                "content_size": len(tex_content)
            })
            
            # バリデーション
            self._validate_tex_content(tex_content)
            
            # チャンキング
            log_proofreading_debug("LaTeXコンテンツをチャンクに分割")
            sections = chunking_tex_file(tex_content)
            log_proofreading_info(f"チャンク分割完了: {len(sections)}セクション")
            
            # 校正処理
            if mode == ProofreadingMode.WITH_KNOWLEDGE:
                log_proofreading_debug("知識ベース使用校正を実行")
                results = proofread_paper_by_knowledge(sections)
            elif mode == ProofreadingMode.WITHOUT_KNOWLEDGE:
                log_proofreading_debug("知識ベース非使用校正を実行")
                results = proofread_paper_without_knowledge(sections)
            else:
                raise ProofreadingError(f"サポートされていない校正モードです: {mode}")
            
            log_proofreading_info(f"校正処理完了: {len(results)}結果")
            return results
            
        except Exception as e:
            raise ProofreadingError(f"LaTeXコンテンツ処理中にエラーが発生しました: {e}")
    
    def proofread_from_google_drive(self) -> List[Dict[str, Any]]:
        """
        Google Driveから校正対象ファイルをダウンロードして校正
        
        Returns:
            List[Dict[str, Any]]: 校正結果
            
        Raises:
            ProofreadingError: 処理に失敗した場合
        """
        try:
            log_proofreading_info("Google Driveからの論文校正を開始")
            
            # Google Driveからファイルダウンロード
            log_proofreading_debug(f"Google Driveからファイルダウンロード: {self.folder_id}")
            tex_bytes = download_pre_proofread_tex_file(self.folder_id)
            
            # バイトをテキストに変換
            tex_content = tex_bytes.decode('utf-8')
            
            # 校正処理
            results = self._process_tex_content(tex_content, ProofreadingMode.WITH_KNOWLEDGE)
            
            log_proofreading_info("Google Driveからの論文校正が完了")
            return results
            
        except Exception as e:
            raise ProofreadingError(f"Google Driveからの論文校正中にエラーが発生しました: {e}")
    
    def proofread_uploaded_file(
        self, 
        tex_content: str, 
        use_knowledge: bool = True
    ) -> List[Dict[str, Any]]:
        """
        アップロードされたファイルを校正
        
        Args:
            tex_content (str): LaTeXコンテンツ
            use_knowledge (bool): 知識ベースを使用するかどうか
            
        Returns:
            List[Dict[str, Any]]: 校正結果
            
        Raises:
            ProofreadingError: 処理に失敗した場合
        """
        try:
            log_proofreading_info(f"アップロードファイル校正を開始 (知識ベース: {use_knowledge})")
            
            mode = ProofreadingMode.WITH_KNOWLEDGE if use_knowledge else ProofreadingMode.WITHOUT_KNOWLEDGE
            results = self._process_tex_content(tex_content, mode)
            
            log_proofreading_info("アップロードファイル校正が完了")
            return results
            
        except Exception as e:
            raise ProofreadingError(f"アップロードファイル校正中にエラーが発生しました: {e}")