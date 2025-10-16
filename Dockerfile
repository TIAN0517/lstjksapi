# BossJy-Pro 優化版 Dockerfile
# 企業級數據清洗和處理服務

# ==================== 多階段建置 ====================
FROM python:3.11-slim as builder

# 安裝系統依賴和編譯工具
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    curl \
    git \
    autoconf \
    automake \
    libtool \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# 編譯並安裝 libpostal
RUN git clone https://github.com/openvenues/libpostal /tmp/libpostal && \
    cd /tmp/libpostal && \
    ./bootstrap.sh && \
    ./configure --datadir=/usr/local/share/libpostal && \
    make -j"$(nproc)" && \
    make install && \
    ldconfig && \
    rm -rf /tmp/libpostal

# 設置工作目錄
WORKDIR /app

# 複製依賴文件
COPY requirements.txt .

# 安裝 Python 依賴
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ==================== 運行階段 ====================
FROM python:3.11-slim

# 安裝運行時依賴
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 創建非 root 用戶
RUN useradd --create-home --shell /bin/bash app

# 設置工作目錄
WORKDIR /app

# 從 builder 階段複製 libpostal 庫和數據
COPY --from=builder /usr/local/lib/libpostal* /usr/local/lib/
COPY --from=builder /usr/local/include/libpostal /usr/local/include/libpostal
COPY --from=builder /usr/local/share/libpostal /usr/local/share/libpostal
RUN ldconfig

# 從 builder 階段複製 Python 依賴
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 複製應用代碼
COPY app/ ./app/
COPY web/ ./web/
COPY run_web.py ./run_web.py
COPY init.sql ./

# 創建模型目錄（用於 fastText LID 模型）
RUN mkdir -p /app/models
# Note: Download lid.176.ftz from https://fasttext.cc/docs/en/language-identification.html
# and place it in ./models/ before building

# 設置權限
RUN chown -R app:app /app

# 切換到非 root 用戶
USER app

# 設置環境變數
ENV PYTHONPATH=/app
ENV PATH=/usr/local/bin:$PATH

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 暴露端口
EXPOSE 8000

# 啟動命令
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
