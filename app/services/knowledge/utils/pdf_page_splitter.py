"""
PDFページ分割ユーティリティ

複数ページのPDFを個別ページに分割し、各ページを個別に処理できるように変換する機能を提供。
"""

import fitz  # PyMuPDF
from typing import List, Dict, Any
import io
from pathlib import Path


class PDFPageSplitter:
    """PDF文書を個別ページに分割するクラス"""
    
    def __init__(self):
        pass
    
    def split_pdf_to_pages(self, pdf_bytes: bytes, file_name: str) -> List[Dict[str, Any]]:
        """
        PDFバイトデータを個別ページに分割
        
        Args:
            pdf_bytes: PDFファイルのバイトデータ
            file_name: 元のファイル名
            
        Returns:
            List[Dict]: 各ページの情報を含む辞書のリスト
            - page_number: ページ番号（1から開始）
            - page_bytes: そのページのPDFバイトデータ
            - source_file: 元のファイル名
            - page_file_name: ページ固有のファイル名
        """
        pages_data = []
        
        try:
            # PDFバイトデータからドキュメントを開く
            pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
            
            # 各ページを個別に処理
            for page_num in range(pdf_document.page_count):
                # 新しいPDFドキュメントを作成し、1ページだけ挿入
                single_page_doc = fitz.open()
                single_page_doc.insert_pdf(pdf_document, from_page=page_num, to_page=page_num)
                
                # 1ページのPDFをバイトデータに変換
                page_bytes = single_page_doc.write()
                
                # ページ情報を保存
                page_info = {
                    "page_number": page_num + 1,
                    "page_bytes": page_bytes,
                    "source_file": file_name,
                    "page_file_name": f"{Path(file_name).stem}_page_{page_num + 1}.pdf"
                }
                
                pages_data.append(page_info)
                
                # メモリ解放
                single_page_doc.close()
            
            # 元のドキュメントを閉じる
            pdf_document.close()
            
            print(f"PDFを{len(pages_data)}ページに分割しました: {file_name}")
            
        except Exception as e:
            print(f"PDF分割中にエラーが発生しました ({file_name}): {e}")
            # エラーが発生した場合は元のPDFをそのまま返す
            pages_data = [{
                "page_number": 1,
                "page_bytes": pdf_bytes,
                "source_file": file_name,
                "page_file_name": file_name
            }]
        
        return pages_data
    
    def get_pdf_info(self, pdf_bytes: bytes) -> Dict[str, Any]:
        """
        PDFの基本情報を取得
        
        Args:
            pdf_bytes: PDFファイルのバイトデータ
            
        Returns:
            Dict: PDF情報
            - page_count: ページ数
            - metadata: PDFメタデータ
        """
        try:
            pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
            
            info = {
                "page_count": pdf_document.page_count,
                "metadata": pdf_document.metadata
            }
            
            pdf_document.close()
            return info
            
        except Exception as e:
            print(f"PDF情報取得中にエラーが発生しました: {e}")
            return {
                "page_count": 0,
                "metadata": {},
                "error": str(e)
            }


def split_pdf_files_to_pages(pdf_files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    複数のPDFファイルを全て個別ページに分割
    
    Args:
        pdf_files: PDFファイル情報のリスト
        - name: ファイル名
        - content: PDFバイトデータ
        - knowledge_type: ナレッジタイプ（オプション）
        
    Returns:
        List[Dict]: 全ページの情報を含むリスト
    """
    splitter = PDFPageSplitter()
    all_pages = []
    
    for pdf_file in pdf_files:
        file_name = pdf_file["name"]
        file_bytes = pdf_file["content"]
        knowledge_type = pdf_file.get("knowledge_type", "PDF")
        
        print(f"PDFページ分割処理中: {file_name}")
        
        # PDFを個別ページに分割
        pages_data = splitter.split_pdf_to_pages(file_bytes, file_name)
        
        # 各ページにナレッジタイプを追加
        for page_data in pages_data:
            page_data["knowledge_type"] = knowledge_type
            all_pages.append(page_data)
    
    print(f"合計 {len(all_pages)} ページに分割しました")
    return all_pages