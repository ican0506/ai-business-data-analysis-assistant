# 部署说明

## Docker Compose

1. 在项目根目录复制 `.env.example` 为 `.env`，设置 `MYSQL_ROOT_PASSWORD` 与至少 32 位的 `JWT_SECRET_KEY`。
2. 不使用大模型时设置 `LLM_PROVIDER=rule_based` 并保持 `LLM_API_KEY` 为空；使用 DeepSeek 时再填写密钥、模型和基础地址。
3. 先运行 `docker compose config` 检查变量是否齐全，再执行 `docker compose up --build -d`。
4. 使用 `docker compose ps` 检查 `mysql`、`backend`、`nginx` 状态。默认访问前端 `http://localhost/`，Swagger 为 `http://localhost:8001/docs`。

默认端口为：Nginx `80`、后端 `8001`、MySQL `3308`；均可通过根目录 `.env` 覆盖。`./storage` 挂载到后端容器的 `/storage`，用于上传文件和清洗结果。停止但保留数据使用 `docker compose down`；不要随意使用 `-v`，它会删除 MySQL volume。

## Linux 建议

- 使用反向代理（Nginx）暴露 HTTPS，后端仅在内网端口监听。
- 使用强随机数据库密码和环境变量/密钥管理服务，不写入 Git。
- 挂载持久化目录保存 MySQL volume、上传文件和导出报告。
- 配置备份、日志轮转、健康检查与最小 CORS 白名单。
