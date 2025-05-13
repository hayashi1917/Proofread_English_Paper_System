FROM python:3.12

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Poetryのインストール
RUN pip install poetry \
    && poetry config virtualenvs.create false

# 依存関係ファイルだけを最初にコピーし、キャッシュを効率化
COPY ./pyproject.toml ./poetry.lock* ./

# Poetryで依存関係をインストール
RUN poetry install --no-interaction --no-ansi --no-root

# 残りのファイルをコピー
COPY . .

# 環境変数を指定
# ARG ENV=local
# ENV ENV=${ENV}

# アプリケーションの実行
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]