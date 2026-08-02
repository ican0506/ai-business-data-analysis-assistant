FROM docker.m.daocloud.io/library/python:3.14-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app
# 保留后端已有静态入口所需目录；生产访问由独立 frontend 容器处理。
COPY frontend/index.html /frontend/index.html
COPY frontend/assets /frontend/assets

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
