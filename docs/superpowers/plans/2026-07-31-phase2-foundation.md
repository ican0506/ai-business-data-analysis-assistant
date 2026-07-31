# 第二阶段：工程基础与健康检查实现计划

> **面向 AI 代理的工作者：** 后续使用 `superpowers-zh:executing-plans` 在当前隔离工作区逐项执行；每项均采用测试先行并在阶段结束后审查。

**目标：** 在 `codex/phase2-foundation` 中创建可配置、可测试的 FastAPI 基础工程，提供 `/api/v1/health` 健康检查、MySQL 连接配置和前端静态页面入口。

**架构：** 使用 Pydantic Settings 从环境变量读取配置，FastAPI 只负责 HTTP 边界，健康检查服务负责构造可测试的响应。数据库引擎在应用启动时按配置创建；默认不要求本机 MySQL 已运行，因此健康接口会明确返回数据库连接状态而不是让应用崩溃。

**技术栈：** Python 3.11+、FastAPI、Uvicorn、SQLAlchemy 2.x、PyMySQL、Pydantic Settings、Pytest、HTTPX、MySQL 8、原生 HTML/CSS/JavaScript。

---

## 文件结构

- 创建：`backend/requirements.txt` — 后端运行与测试依赖。
- 创建：`backend/.env.example` — 不含密钥的 MySQL、JWT、文件上传和 LLM 配置模板。
- 创建：`backend/.venv/` — 本地 Python 依赖隔离目录，已由 `.gitignore` 忽略。
- 创建：`backend/app/core/config.py` — `Settings` 与配置缓存。
- 创建：`backend/app/core/logging.py` — 应用日志初始化。
- 创建：`backend/app/db/session.py` — SQLAlchemy 引擎与会话工厂。
- 创建：`backend/app/services/health_service.py` — 数据库探活与健康响应构造。
- 创建：`backend/app/api/v1/health.py` — `/api/v1/health` 路由。
- 创建：`backend/app/main.py` — FastAPI 应用工厂、CORS、路由与静态文件。
- 创建：`backend/tests/conftest.py` — 测试环境配置与 TestClient。
- 创建：`backend/tests/test_health.py` — 健康检查接口测试。
- 创建：`frontend/index.html`、`frontend/assets/css/app.css`、`frontend/assets/js/app.js` — 最小前端入口与后端状态展示。
- 创建：`docker-compose.yml`、`backend/Dockerfile` — 后端与 MySQL 本地容器启动。
- 创建：`README.md` — Windows 本地运行、测试、Docker 运行说明。

### 任务 1：建立依赖与配置边界

**文件：**
- 创建：`backend/requirements.txt`
- 创建：`backend/.env.example`
- 创建：`backend/app/core/config.py`
- 测试：`backend/tests/test_config.py`

- [ ] **步骤 1：创建虚拟环境并安装测试依赖**

运行：`cd backend; python -m venv .venv; .\.venv\Scripts\python -m pip install -r requirements.txt`

预期：`.venv` 创建成功，`fastapi`、`pytest`、`pydantic-settings`、`sqlalchemy`、`pymysql` 和 `httpx` 可被该解释器导入。

- [ ] **步骤 2：编写失败测试**

```python
from app.core.config import Settings


def test_settings_builds_mysql_url_from_environment(monkeypatch):
    monkeypatch.setenv("MYSQL_HOST", "mysql.example")
    monkeypatch.setenv("MYSQL_PORT", "3307")
    monkeypatch.setenv("MYSQL_DATABASE", "analysis_db")
    monkeypatch.setenv("MYSQL_USER", "analysis_user")
    monkeypatch.setenv("MYSQL_PASSWORD", "safe-password")

    settings = Settings()

    assert settings.database_url == "mysql+pymysql://analysis_user:safe-password@mysql.example:3307/analysis_db"
```

- [ ] **步骤 3：运行测试确认失败**

运行：`cd backend; python -m pytest tests/test_config.py -q`

预期：失败，提示 `ModuleNotFoundError: No module named 'app'` 或 `config` 模块不存在。

- [ ] **步骤 4：最小实现配置**

```python
class Settings(BaseSettings):
    mysql_host: str = "127.0.0.1"
    mysql_port: int = 3306
    mysql_database: str = "ai_data_analysis"
    mysql_user: str = "root"
    mysql_password: str = ""

    @property
    def database_url(self) -> str:
        return f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
```

- [ ] **步骤 5：运行测试确认通过**

运行：`cd backend; python -m pytest tests/test_config.py -q`

预期：`1 passed`。

- [ ] **步骤 6：提交**

```powershell
git add backend/requirements.txt backend/.env.example backend/app/core/config.py backend/tests/test_config.py
git commit -m "chore: 初始化后端配置"
```

### 任务 2：实现数据库会话和可降级探活

**文件：**
- 创建：`backend/app/db/session.py`
- 创建：`backend/app/services/health_service.py`
- 测试：`backend/tests/test_health_service.py`

- [ ] **步骤 1：编写失败测试**

```python
from app.services.health_service import build_health_payload


def test_build_health_payload_marks_database_unavailable_when_probe_fails():
    payload = build_health_payload(lambda: False)

    assert payload == {"status": "degraded", "database": "unavailable"}
```

- [ ] **步骤 2：运行测试确认失败**

运行：`cd backend; python -m pytest tests/test_health_service.py -q`

预期：失败，提示 `health_service` 模块不存在。

- [ ] **步骤 3：最小实现服务和会话**

```python
def build_health_payload(database_probe: Callable[[], bool]) -> dict[str, str]:
    database_ok = database_probe()
    return {
        "status": "ok" if database_ok else "degraded",
        "database": "available" if database_ok else "unavailable",
    }
```

- [ ] **步骤 4：运行测试确认通过**

运行：`cd backend; python -m pytest tests/test_health_service.py -q`

预期：`1 passed`。

- [ ] **步骤 5：提交**

```powershell
git add backend/app/db/session.py backend/app/services/health_service.py backend/tests/test_health_service.py
git commit -m "feat: 添加数据库健康探活"
```

### 任务 3：暴露 FastAPI 健康检查接口

**文件：**
- 创建：`backend/app/api/v1/health.py`
- 创建：`backend/app/main.py`
- 创建：`backend/tests/conftest.py`
- 测试：`backend/tests/test_health.py`

- [ ] **步骤 1：编写失败测试**

```python
def test_health_endpoint_returns_unified_response(client, monkeypatch):
    monkeypatch.setattr("app.api.v1.health.is_database_available", lambda: True)

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "code": 0,
        "message": "success",
        "data": {"status": "ok", "database": "available"},
    }
```

- [ ] **步骤 2：运行测试确认失败**

运行：`cd backend; python -m pytest tests/test_health.py -q`

预期：失败，提示 `app.main` 或路由不存在。

- [ ] **步骤 3：最小实现应用和路由**

```python
router = APIRouter(prefix="/api/v1", tags=["系统"])

@router.get("/health")
def health_check() -> dict:
    return {"code": 0, "message": "success", "data": build_health_payload(is_database_available)}
```

- [ ] **步骤 4：运行测试确认通过**

运行：`cd backend; python -m pytest tests/test_health.py -q`

预期：`1 passed`。

- [ ] **步骤 5：提交**

```powershell
git add backend/app/api/v1/health.py backend/app/main.py backend/tests/conftest.py backend/tests/test_health.py
git commit -m "feat: 提供健康检查接口"
```

### 任务 4：提供最小前端入口和容器运行定义

**文件：**
- 创建：`frontend/index.html`
- 创建：`frontend/assets/css/app.css`
- 创建：`frontend/assets/js/app.js`
- 创建：`backend/Dockerfile`
- 创建：`docker-compose.yml`
- 测试：`backend/tests/test_health.py`

- [ ] **步骤 1：补充失败测试**

```python
def test_root_serves_frontend_entry(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "AI 智能数据分析助手" in response.text
```

- [ ] **步骤 2：运行测试确认失败**

运行：`cd backend; python -m pytest tests/test_health.py::test_root_serves_frontend_entry -q`

预期：失败，当前应用尚未定义根路径页面。

- [ ] **步骤 3：最小实现静态页面和容器配置**

```yaml
services:
  mysql:
    image: mysql:8.4
  backend:
    build: ./backend
    depends_on:
      mysql:
        condition: service_healthy
```

`backend/app/main.py` 同时增加：

```python
@app.get("/", include_in_schema=False)
def frontend_entry() -> FileResponse:
    return FileResponse(settings.frontend_index_path)
```

- [ ] **步骤 4：运行测试确认通过**

运行：`cd backend; python -m pytest tests/test_health.py -q`

预期：所有健康接口测试通过。

- [ ] **步骤 5：提交**

```powershell
git add frontend backend/Dockerfile docker-compose.yml backend/tests/test_health.py
git commit -m "feat: 添加前端入口与Docker基础配置"
```

### 任务 5：补充运行文档并执行集成验证

**文件：**
- 创建：`README.md`
- 修改：`backend/.env.example`
- 测试：`backend/tests/test_config.py`、`backend/tests/test_health_service.py`、`backend/tests/test_health.py`

- [ ] **步骤 1：编写失败测试**

```python
def test_health_endpoint_allows_frontend_origin(client):
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://127.0.0.1:5500",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5500"
```

- [ ] **步骤 2：运行测试确认失败**

运行：`cd backend; python -m pytest tests/test_health.py::test_health_endpoint_allows_frontend_origin -q`

预期：失败，应用尚未配置 CORS 中间件。

- [ ] **步骤 3：最小实现 CORS 和文档**

```markdown
## 本地启动

1. 复制 `backend/.env.example` 为 `backend/.env` 并填写 MySQL 密码。
2. 在 `backend` 目录安装依赖并运行 `uvicorn app.main:app --reload`。
3. 打开 `http://127.0.0.1:8000/docs` 验证 Swagger。
```

`backend/app/main.py` 增加：

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

- [ ] **步骤 4：运行完整验证**

运行：`cd backend; python -m pytest -q`

预期：全部测试通过；再运行 `python -m compileall app`，预期没有编译错误；再运行 `git diff --check`，预期无输出。

- [ ] **步骤 5：提交**

```powershell
git add README.md backend/.env.example backend/tests/test_health.py
git commit -m "docs: 补充基础工程运行说明"
```

## 计划自检

- 需求覆盖：配置、MySQL、FastAPI 健康接口、Swagger、前端入口、Docker、运行文档均有对应任务。
- 测试顺序：每项行为先创建失败测试，再编写最小实现并复测。
- 边界一致：健康接口统一返回 `code/message/data`，数据库不可用时返回 `degraded` 而不是 500；前端来源由 CORS 白名单控制。
- 范围控制：本计划不实现认证、文件上传、数据清洗、AI 或报告；它们在后续阶段单独规划。
