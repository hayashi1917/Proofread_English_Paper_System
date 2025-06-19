"""
LaTeX分割機能テスト専用APIエンドポイント

様々な分割モードの性能と精度を比較テストするためのエンドポイント群
"""
import time
from typing import List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query

from app.schemas.schemas import (
    LaTeXSplitRequest, 
    LaTeXSplitResponse, 
    ChunkInfo,
    MultipleSplitRequest,
    MultipleSplitResponse,
    SplitComparison,
    SplitModeEnum
)
from app.services.knowledge.chunking_file import ChunkingService
from app.services.shared.logging_utils import log_proofreading_info, log_proofreading_debug
from app.services.shared.exceptions import ChunkingError

router = APIRouter(
    prefix="/latex_split_test",
    tags=["latex_split_test"],
)

# ChunkingServiceのインスタンス
chunking_service = ChunkingService()


def _determine_chunk_type(content: str, split_mode: SplitModeEnum) -> str:
    """チャンクのタイプを判定"""
    content_lower = content.lower().strip()
    
    if split_mode == SplitModeEnum.HYBRID:
        if any(cmd in content_lower for cmd in ['\\documentclass', '\\usepackage', '\\title', '\\author']):
            return "preamble"
        elif '\\begin{document}' in content_lower:
            return "document_start"
        elif any(sec in content_lower for sec in ['\\section', '\\subsection', '\\chapter']):
            return "section_header"
        else:
            return "content"
    elif split_mode == SplitModeEnum.COMMAND:
        if content_lower.startswith('\\'):
            return "latex_command"
        else:
            return "text_content"
    elif split_mode == SplitModeEnum.SENTENCE:
        return "sentence"
    else:
        return "chunk"


def _get_split_function(split_mode: SplitModeEnum):
    """分割モードに対応する関数を取得"""
    if split_mode == SplitModeEnum.SECTION:
        return chunking_service.split_latex_by_section
    elif split_mode == SplitModeEnum.COMMAND:
        return chunking_service.split_latex_by_command
    elif split_mode == SplitModeEnum.SENTENCE:
        return chunking_service.split_latex_by_sentence
    elif split_mode == SplitModeEnum.HYBRID:
        return chunking_service.split_latex_by_hybrid
    elif split_mode == SplitModeEnum.RECURSIVE_NLP:
        return chunking_service.split_latex_by_recursive_nlp
    else:
        raise ValueError(f"サポートされていない分割モード: {split_mode}")


def _validate_latex_file(file: UploadFile) -> str:
    """LaTeXファイルの妥当性をチェックし、内容を返す"""
    # ファイル拡張子チェック
    if not file.filename:
        raise HTTPException(status_code=400, detail="ファイル名が指定されていません")
    
    allowed_extensions = ['.tex', '.latex', '.txt']
    file_extension = None
    for ext in allowed_extensions:
        if file.filename.lower().endswith(ext):
            file_extension = ext
            break
    
    if not file_extension:
        raise HTTPException(
            status_code=400, 
            detail=f"サポートされていないファイル形式です。対応形式: {', '.join(allowed_extensions)}"
        )
    
    # ファイルサイズチェック（10MB制限）
    max_size = 10 * 1024 * 1024  # 10MB
    content_bytes = file.file.read()
    if len(content_bytes) > max_size:
        raise HTTPException(status_code=413, detail=f"ファイルサイズが大きすぎます（最大: {max_size // 1024 // 1024}MB）")
    
    # ファイルが空でないかチェック
    if len(content_bytes) == 0:
        raise HTTPException(status_code=400, detail="ファイルが空です")
    
    # UTF-8でデコード
    try:
        content = content_bytes.decode('utf-8')
    except UnicodeDecodeError:
        try:
            # UTF-8が失敗した場合はCP932（Shift_JIS）を試す
            content = content_bytes.decode('cp932')
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="ファイルの文字エンコーディングがサポートされていません（UTF-8またはShift_JISが必要）")
    
    # 最小長チェック
    if len(content.strip()) < 10:
        raise HTTPException(status_code=400, detail="ファイル内容が短すぎます（最低10文字必要）")
    
    return content


def _recommend_split_mode(comparisons: List[SplitComparison], original_length: int) -> SplitModeEnum:
    """最適な分割モードを推奨"""
    # 文書の長さに基づく推奨ロジック
    if original_length < 500:
        # 短い文書：セクション分割が適切
        return SplitModeEnum.SECTION
    elif original_length < 2000:
        # 中程度の文書：ハイブリッド分割が最適
        return SplitModeEnum.HYBRID
    else:
        # 長い文書：文単位分割で細かく処理
        return SplitModeEnum.SENTENCE


@router.post("/split", response_model=LaTeXSplitResponse)
async def split_latex_file(
    file: UploadFile = File(..., description="LaTeXファイル (.tex, .latex, .txt)"),
    split_mode: SplitModeEnum = Form(SplitModeEnum.SECTION, description="分割モード")
):
    """
    アップロードされたLaTeXファイルを指定したモードで分割
    
    単一の分割モードでテストし、詳細な結果を返します。
    """
    try:
        log_proofreading_info(f"LaTeX分割テスト開始: {split_mode}")
        
        # ファイル内容を読み取り・検証
        latex_content = _validate_latex_file(file)
        
        # 分割処理実行
        start_time = time.time()
        split_function = _get_split_function(split_mode)
        chunks = split_function(latex_content)
        processing_time = (time.time() - start_time) * 1000  # ミリ秒に変換
        
        # チャンク情報を構築
        chunk_infos = []
        for i, chunk in enumerate(chunks):
            chunk_type = _determine_chunk_type(chunk, split_mode)
            chunk_infos.append(ChunkInfo(
                chunk_id=i,
                content=chunk,
                length=len(chunk),
                chunk_type=chunk_type
            ))
        
        log_proofreading_info(f"分割完了: {len(chunks)}チャンク, {processing_time:.2f}ms, ファイル: {file.filename}")
        
        return LaTeXSplitResponse(
            split_mode=split_mode,
            total_chunks=len(chunks),
            original_length=len(latex_content),
            chunks=chunk_infos,
            processing_time_ms=processing_time
        )
        
    except HTTPException:
        raise
    except ChunkingError as e:
        log_proofreading_debug(f"分割エラー: {e}")
        raise HTTPException(status_code=400, detail=f"分割処理に失敗しました: {e}")
    except Exception as e:
        log_proofreading_debug(f"予期しないエラー: {e}")
        raise HTTPException(status_code=500, detail=f"内部エラーが発生しました: {e}")


@router.post("/compare", response_model=MultipleSplitResponse)
async def compare_split_modes(
    file: UploadFile = File(..., description="LaTeXファイル (.tex, .latex, .txt)"),
    split_modes: Optional[str] = Form(
        "section,sentence,hybrid", 
        description="比較する分割モード（カンマ区切り）例: section,sentence,hybrid"
    )
):
    """
    アップロードされたファイルを複数の分割モードで比較分析
    
    パフォーマンスと精度の比較分析を提供します。
    """
    try:
        # 分割モードをパース
        split_mode_list = []
        for mode_str in split_modes.split(','):
            mode_str = mode_str.strip()
            try:
                split_mode_list.append(SplitModeEnum(mode_str))
            except ValueError:
                raise HTTPException(
                    status_code=400, 
                    detail=f"無効な分割モード: {mode_str}. 有効なモード: {[e.value for e in SplitModeEnum]}"
                )
        
        log_proofreading_info(f"分割モード比較開始: {len(split_mode_list)}モード, ファイル: {file.filename}")
        
        # ファイル内容を読み取り・検証
        latex_content = _validate_latex_file(file)
        
        total_start_time = time.time()
        comparisons = []
        
        for split_mode in split_mode_list:
            try:
                # 各分割モードで処理
                start_time = time.time()
                split_function = _get_split_function(split_mode)
                chunks = split_function(latex_content)
                processing_time = (time.time() - start_time) * 1000
                
                # サンプルチャンク（最初の3つ、長すぎる場合は省略）
                sample_chunks = []
                for chunk in chunks[:3]:
                    if len(chunk) > 100:
                        sample_chunks.append(chunk[:97] + "...")
                    else:
                        sample_chunks.append(chunk)
                
                comparisons.append(SplitComparison(
                    split_mode=split_mode,
                    chunk_count=len(chunks),
                    processing_time_ms=processing_time,
                    sample_chunks=sample_chunks
                ))
                
                log_proofreading_debug(f"{split_mode}: {len(chunks)}チャンク, {processing_time:.2f}ms")
                
            except Exception as e:
                log_proofreading_debug(f"{split_mode}でエラー: {e}")
                # エラーが発生したモードはスキップ
                continue
        
        total_processing_time = (time.time() - total_start_time) * 1000
        
        if not comparisons:
            raise HTTPException(status_code=400, detail="すべての分割モードで処理に失敗しました")
        
        # 推奨モードを決定
        recommended_mode = _recommend_split_mode(comparisons, len(latex_content))
        
        log_proofreading_info(f"比較完了: {len(comparisons)}モード, 推奨: {recommended_mode}")
        
        return MultipleSplitResponse(
            original_length=len(latex_content),
            comparisons=comparisons,
            recommended_mode=recommended_mode,
            total_processing_time_ms=total_processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_proofreading_debug(f"比較処理でエラー: {e}")
        raise HTTPException(status_code=500, detail=f"比較処理中にエラーが発生しました: {e}")


@router.get("/download_sample/{sample_name}")
async def download_sample_latex(sample_name: str):
    """
    サンプルLaTeXファイルをダウンロード
    
    テスト用にサンプルファイルを.tex形式でダウンロードできます。
    """
    from fastapi.responses import Response
    
    samples = await get_sample_latex()
    
    if sample_name not in samples:
        raise HTTPException(
            status_code=404, 
            detail=f"サンプル '{sample_name}' が見つかりません。利用可能: {list(samples.keys())}"
        )
    
    sample = samples[sample_name]
    content = sample["content"].strip()
    filename = f"{sample_name}_sample.tex"
    
    return Response(
        content=content,
        media_type="application/x-tex",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/sample_latex")
async def get_sample_latex():
    """
    テスト用のサンプルLaTeXコンテンツを返す
    
    様々な複雑さのサンプルを提供し、分割テストに使用できます。
    """
    samples = {
        "simple": {
            "name": "シンプルな論文",
            "description": "基本的なLaTeX構造を持つ短い論文",
            "content": r"""
\documentclass{article}
\usepackage{amsmath}
\title{Simple Paper}
\author{Test Author}

\begin{document}
\maketitle

\section{Introduction}
This is a simple introduction. It contains basic sentences.

\section{Conclusion}
This is the conclusion. The paper is now complete.

\end{document}
"""
        },
        "complex": {
            "name": "複雑な論文",
            "description": "数式、図表、複数セクションを含む論文",
            "content": r"""
\documentclass[12pt]{article}
\usepackage{amsmath, amssymb, graphicx}
\title{Advanced Research in Machine Learning}
\author{John Doe\thanks{University of Science}}
\date{\today}

\begin{document}
\maketitle

\begin{abstract}
This paper presents a novel approach to deep learning. We demonstrate significant improvements over existing methods. The experimental results show promising outcomes for real-world applications.
\end{abstract}

\section{Introduction}
Machine learning has revolutionized many fields in recent years. In particular, deep neural networks have shown remarkable success in various domains. The fundamental equation for neural network computation is:

\begin{equation}
f(x) = \sigma(Wx + b)
\end{equation}

where $\sigma$ represents the activation function, $W$ is the weight matrix, and $b$ is the bias vector.

Recent studies have demonstrated the effectiveness of this approach. However, several challenges remain to be addressed. Our method provides a novel solution to these limitations.

\section{Methodology}
We propose a new architecture based on transformer models. The key innovation lies in the attention mechanism. Our approach differs from previous work in several important ways.

\subsection{Data Preprocessing}
Data quality is crucial for model performance. We applied several preprocessing steps including normalization and feature selection. The preprocessing pipeline consists of the following stages:

\begin{itemize}
\item Data cleaning and validation
\item Feature extraction and transformation
\item Normalization and scaling
\end{itemize}

\subsection{Model Architecture}
The proposed model consists of multiple layers with specific functions. Each layer performs targeted transformations on the input data.

\section{Experimental Results}
Our experiments demonstrate significant improvements over baseline methods. The accuracy increased by 15% compared to state-of-the-art approaches. Training time was also reduced substantially.

\section{Conclusion}
This work presents a novel approach to machine learning with promising results. Future research will explore additional applications and extensions of this method.

\end{document}
"""
        },
        "preamble_heavy": {
            "name": "プリアンブル重点",
            "description": "多くのパッケージと設定を含むプリアンブル",
            "content": r"""
\documentclass[11pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{amsmath}
\usepackage{amsfonts}
\usepackage{amssymb}
\usepackage{graphicx}
\usepackage{geometry}
\usepackage{hyperref}
\usepackage{natbib}
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{array}
\usepackage{multirow}
\usepackage{wrapfig}
\usepackage{float}
\usepackage{colortbl}
\usepackage{pdflscape}
\usepackage{tabu}
\usepackage{threeparttable}
\usepackage{threeparttablex}
\usepackage{makecell}
\usepackage{xcolor}

\geometry{margin=1in}
\hypersetup{colorlinks=true, linkcolor=blue, citecolor=red}

\title{A Comprehensive Study}
\author{Research Team}
\date{\today}

\begin{document}
\maketitle

\section{Introduction}
This document demonstrates a complex preamble with many packages. The content itself is relatively simple.

\section{Methods}
We used standard statistical methods for analysis.

\section{Results}
The results are presented in the following sections.

\section{Conclusion}
This study provides insights into the research question.

\end{document}
"""
        }
    }
    
    return samples


@router.get("/modes")
async def get_available_split_modes():
    """
    利用可能な分割モードの一覧と説明を返す
    """
    modes = {
        "section": {
            "name": "セクション分割",
            "description": "LaTeXのセクション区切り（\\section, \\subsection等）で分割",
            "best_for": "構造化された論文、章節による分割が必要な場合",
            "performance": "高速"
        },
        "command": {
            "name": "コマンド分割", 
            "description": "LaTeXコマンド単位で分割",
            "best_for": "プリアンブル部分、LaTeX構造の詳細分析",
            "performance": "中程度"
        },
        "sentence": {
            "name": "文分割",
            "description": "NLTKを使用した高精度な文単位分割",
            "best_for": "詳細な文章分析、校正処理",
            "performance": "中程度（高精度）"
        },
        "hybrid": {
            "name": "ハイブリッド分割",
            "description": "プリアンブルはコマンド単位、本文は文単位で分割",
            "best_for": "バランスの取れた分割、一般的な論文処理",
            "performance": "最適"
        },
        "recursive_nlp": {
            "name": "再帰的NLP分割",
            "description": "LangChainの高性能RecursiveCharacterTextSplitter使用",
            "best_for": "長い文書、チャンクサイズ制御が重要な場合",
            "performance": "高速（大規模文書向け）"
        }
    }
    
    return {
        "available_modes": list(modes.keys()),
        "mode_details": modes,
        "recommended_workflow": [
            "1. /sample_latex でサンプル一覧を確認",
            "2. /download_sample/{sample_name} でテスト用ファイルをダウンロード",
            "3. /split でファイルをアップロードして個別モードをテスト", 
            "4. /compare でファイルをアップロードして複数モードを比較",
            "5. 最適なモードを選択して本格運用"
        ],
        "file_requirements": {
            "supported_formats": [".tex", ".latex", ".txt"],
            "max_file_size": "10MB",
            "encoding": ["UTF-8", "Shift_JIS"],
            "min_content_length": "10文字以上"
        }
    }