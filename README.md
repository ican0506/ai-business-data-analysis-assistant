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
- 数据集与字段元信息 SQL 补丁：`backend/sql/002_create_dataset_tables.sql`
- 数据清洗记录 SQL 补丁：`backend/sql/003_create_dataset_cleaning_runs.sql`

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

## 数据集上传接口

- 上传并解析：`POST /api/v1/datasets/upload`
- 必须先在 Swagger 的 **Authorize** 中完成登录授权。
- 支持 `.csv`、`.xlsx`，单文件最大 20 MB；CSV 自动尝试 UTF-8-SIG、UTF-8 与 GBK 编码。
- 接口返回数据集 ID、行列数、字段类型、缺失值数量和前 20 行预览。原始文件存放在 `storage/uploads/`，不会提交到 Git。

## 数据清洗接口

- 清洗接口：`POST /api/v1/datasets/{dataset_id}/clean`
- 必须先在 Swagger 的 **Authorize** 中完成登录授权；`dataset_id` 使用上传接口返回的 `data.id`。
- 清洗不会修改原始上传文件，而是在 `storage/cleaned/` 输出标准化 CSV，并在 `dataset_cleaning_runs` 保存审计记录。
- 当前规则：销售常见中英文列名映射、全空行删除、重复行删除、日期标准化为 `YYYY-MM-DD`、金额/目标/客户数转为数值，并返回清洗摘要和预览。

## 统计分析接口

- 分析接口：`GET /api/v1/datasets/{dataset_id}/metrics`
- 基于最新一次清洗结果，返回总行数、销售额总计/均值/最大/最小值、首末日期销售额增长率、整体完成率和区域销售额 TOP 10。

## AI 业务分析接口

- 报告接口：`POST /api/v1/datasets/{dataset_id}/ai-analysis`
- 当前默认 `rule_based` 模式：基于真实统计指标输出数据摘要、异常发现、业务问题和优化建议，适合无 API Key 的本地演示。
- 后续配置真实 LLM Provider 时，接口返回结构保持不变；真实密钥仅放在 `.env`，不得提交到 Git。

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
SOURCE backend/sql/002_create_dataset_tables.sql;
SOURCE backend/sql/003_create_dataset_cleaning_runs.sql;
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
