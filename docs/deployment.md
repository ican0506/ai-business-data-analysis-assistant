# 部署说明

## Docker Compose

1. 在根目录复制 `.env.example` 为 `.env`。
2. 设置 `MYSQL_ROOT_PASSWORD`，可选设置 `LLM_PROVIDER=deepseek`、`LLM_API_KEY`、`LLM_BASE_URL`、`LLM_MODEL`。
3. 执行 `docker compose up --build -d`。
4. 使用 `docker compose ps` 检查 `mysql` 与 `backend` 状态，访问 `http://127.0.0.1:8000/docs`。

MySQL 映射到主机 `3307`，后端映射 `8000`。停止但保留数据：`docker compose down`；不要随意使用 `-v`，它会删除数据库 volume。

## Linux 建议

- 使用反向代理（Nginx）暴露 HTTPS，后端仅在内网端口监听。
- 使用强随机数据库密码和环境变量/密钥管理服务，不写入 Git。
- 挂载持久化目录保存 MySQL volume、上传文件和导出报告。
- 配置备份、日志轮转、健康检查与最小 CORS 白名单。
