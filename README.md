# AI 智能数据分析助手

面向企业销售运营场景的数据分析系统。第一阶段基础工程已提供 FastAPI 健康检查、MySQL 配置模板、前端入口与 Docker Compose。

## 技术栈

- 后端：Python、FastAPI、SQLAlchemy、MySQL
- 前端：HTML、CSS、JavaScript
- 后续模块：Pandas、NumPy、OpenPyXL、ECharts、LLM API、报告导出

## 本地运行（Windows）

```powershell
cd backend
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

打开：

- 前端入口：<http://127.0.0.1:8000/>
- Swagger：<http://127.0.0.1:8000/docs>
- 健康检查：<http://127.0.0.1:8000/api/v1/health>

未启动 MySQL 时，健康接口会返回 `degraded`，但 FastAPI 与 Swagger 仍能正常访问。

## 测试

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -q
```

## Docker 运行

请先在项目根目录复制配置并设置密码：

```powershell
Copy-Item .env.example .env
```

然后执行：

```powershell
docker compose up --build
```

停止容器：

```powershell
docker compose down
```

不要提交根目录 `.env`、`backend/.env`、上传文件、导出报告或真实 LLM 密钥。
