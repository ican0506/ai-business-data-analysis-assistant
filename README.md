# AI 智能数据分析助手

面向企业销售运营场景的数据分析系统。当前已完成基础工程和认证模块，后续会继续开发文件上传、数据清洗、指标分析、ECharts 可视化、AI 分析报告和导出功能。

## 技术栈

- 后端：Python、FastAPI、SQLAlchemy、MySQL
- 前端：HTML、CSS、JavaScript、ECharts
- 数据处理：Pandas、NumPy、OpenPyXL
- AI：大语言模型 API、Prompt Engineering
- 部署：Git、Docker、Linux

## 已实现功能

- FastAPI 应用入口和 Swagger 文档
- MySQL 连接配置和健康检查
- Docker Compose 启动后端和 MySQL
- 用户注册、登录、JWT 认证
- 当前登录用户查询：`GET /api/v1/auth/me`
- 用户表 SQL 初始化脚本：`backend/sql/001_create_users_table.sql`

## 本地运行

```powershell
cd D:\开发\python项目\AI智能数据分析助手\backend
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

打开：

- 前端入口：<http://127.0.0.1:8000/>
- Swagger：<http://127.0.0.1:8000/docs>
- 健康检查：<http://127.0.0.1:8000/api/v1/health>

## 认证接口

- 注册：`POST /api/v1/auth/register`
- 登录：`POST /api/v1/auth/login`
- 当前用户：`GET /api/v1/auth/me`

示例注册参数：

```json
{
  "username": "sales_user",
  "email": "sales@example.com",
  "password": "Password123"
}
```

## 数据库

新数据库可以执行：

```sql
SOURCE backend/sql/001_create_users_table.sql;
```

当前开发环境启动 FastAPI 时也会自动创建已声明的数据表。正式生产环境后续会改为 Alembic 迁移管理。

## 测试

```powershell
cd D:\开发\python项目\AI智能数据分析助手\backend
.\.venv\Scripts\python.exe -m pytest -q
```

## Docker 运行

先在项目根目录复制配置：

```powershell
cd D:\开发\python项目\AI智能数据分析助手
Copy-Item .env.example .env
```

然后启动：

```powershell
docker compose up --build
```

停止容器：

```powershell
docker compose down
```

不要提交 `.env`、`backend/.env`、上传文件、导出报告、日志文件或真实 LLM 密钥。
