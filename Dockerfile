# 使用官方 Python 基礎映像
FROM python:3.11-slim

# 設定工作目錄
WORKDIR /app

# 複製程式檔案和 requirements
COPY . /app

# 安裝 Python 相依套件
RUN pip install --no-cache-dir -r requirements.txt

# 啟動程式（假設主程式叫做 main.py）
CMD ["python", "main.py"]
