# CLAUDE.md
必ず日本語で回答してください｡

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

Start the FastAPI development server:
```bash
uvicorn app.main:app --reload
```

The server runs on http://localhost:8000 by default and serves a static HTML interface at the root path.

## Environment Setup

The application requires a `.env.local` file with the following Azure and OpenAI credentials:
- `AZURE_OPENAI_KEY` - For OpenAI GPT-4o-mini model access
- `AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT` and `AZURE_DOCUMENT_INTELLIGENCE_KEY` - For document analysis
- `ENGLISH_PAPER_BEFORE_PROOFREADING_FOLDER_ID` - Google Drive folder ID for input papers
- `TEST_FOLDER_ID` - Google Drive folder ID for knowledge base documents

## Architecture Overview

This is an English paper proofreading system that combines knowledge-based validation with LLM proofreading. The system has two main pipelines:

### 1. Knowledge Pipeline
- Downloads LaTeX files from Google Drive (`access_google_drive.py`)
- Chunks documents into sections (`chunking_file.py`) 
- Extracts structured knowledge using LLM (`structure_tex_to_knowledge.py`)
- Stores knowledge embeddings in ChromaDB vector database (`utils/vector_store_service.py`)
- Saves knowledge as timestamped CSV files in `/output/`

### 2. Proofreading Pipeline
- Takes LaTeX papers (from Google Drive or file upload)
- Chunks papers into sections
- Uses HyDE (Hypothetical Document Embeddings) to generate search queries (`create_queries_by_HyDE.py`)
- Retrieves relevant knowledge from vector database
- Combines retrieved knowledge with LLM to generate proofreading suggestions (`proofread_paper_by_knowledge.py`)

### Key Components

**API Layer**: FastAPI with 4 main route modules:
- `/proofread_english_paper/` - Main proofreading endpoints
- `/analyze_document/` - Document analysis functionality  
- `/knowledge_pipeline/` - Knowledge base management
- `/store_and_search_db/` - Vector database operations

**Services Layer**: Core business logic with modular services for each major function

**Azure Integration**: Uses Azure OpenAI (GPT-4o-mini) and Document Intelligence services via custom client wrappers in `libs/azure_client.py`

**Vector Database**: ChromaDB with OpenAI embeddings for semantic search of knowledge base

**Data Flow**: LaTeX → Chunking → Knowledge Extraction/HyDE Queries → Vector Search → LLM Proofreading → Structured Results

## Project Structure Notes

- Poetry is used for dependency management (`pyproject.toml`)
- Static files served from `/static/` directory
- Knowledge base outputs saved to `/output/` with timestamps
- Vector database persisted in `chroma_db/` directory
- All services expect `.env.local` environment configuration