FROM python:3.11-slim

WORKDIR /app

# 只装依赖，利用 Docker 缓存层
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 云部署必须监听 0.0.0.0，端口由平台注入
ENV HOST=0.0.0.0
ENV PORT=8000
EXPOSE 8000

CMD ["python", "run.py"]
