# 数据集上传与解析实现计划

> **面向 AI 代理的工作者：** 使用测试驱动开发，按步骤验证后再提交。

**目标：** 已登录用户可上传 CSV/XLSX，系统安全保存原始文件、解析字段元信息，并返回前 20 行预览。

**架构：** API 只负责文件接收和鉴权；`DatasetService` 负责校验、落盘、Pandas 解析及数据库事务；`Dataset` 与 `DatasetColumn` 仅保存元数据，原始文件保存在 `storage/uploads`。

**技术栈：** FastAPI、SQLAlchemy、Pandas、OpenPyXL、Pytest、MySQL。

---

### 任务 1：数据集模型与数据库补丁

**文件：**
- 新建：`backend/app/models/dataset.py`
- 修改：`backend/app/db/session.py`
- 新建：`backend/sql/002_create_dataset_tables.sql`
- 测试：`backend/tests/test_dataset_api.py`

- [ ] 编写 API 上传测试，断言上传后返回数据集 ID、行数、列数、字段信息和前 20 行预览。
- [ ] 运行 `python -m pytest tests/test_dataset_api.py -q`，预期因路由缺失而失败。
- [ ] 定义 `datasets`、`dataset_columns` SQLAlchemy 模型及 MySQL 安全建表补丁。
- [ ] 运行测试，预期失败原因转为服务/路由尚未实现。

### 任务 2：文件解析与安全落盘

**文件：**
- 新建：`backend/app/services/dataset_service.py`
- 修改：`backend/app/core/config.py`
- 修改：`backend/requirements.txt`
- 测试：`backend/tests/test_dataset_api.py`

- [ ] 编写 CSV、XLSX 解析测试，覆盖列名、数值列、缺失值统计和 GBK CSV 回退编码。
- [ ] 运行聚焦测试，预期因解析服务缺失而失败。
- [ ] 实现 20 MB 限制、`.csv/.xlsx` 白名单、UUID 文件名、CSV 编码回退和字段类型推断。
- [ ] 运行聚焦测试，预期通过。

### 任务 3：鉴权上传接口

**文件：**
- 新建：`backend/app/api/v1/datasets.py`
- 修改：`backend/app/main.py`
- 测试：`backend/tests/test_dataset_api.py`

- [ ] 编写未登录上传返回 401、错误文件类型返回 400 的测试。
- [ ] 运行测试，预期因上传路由缺失而失败。
- [ ] 实现 `POST /api/v1/datasets/upload`，通过 JWT 获取归属用户并调用服务层。
- [ ] 运行 `python -m pytest tests -q`、`python -m compileall app tests -q` 和 `git diff --check`。

### 任务 4：Docker 在线验证与交付

**文件：**
- 修改：`README.md`

- [ ] 补充 Swagger 上传验证说明与支持格式说明。
- [ ] 重建 Docker 后端，以注册账号上传一份 CSV，并验证返回预览和 MySQL 元信息。
- [ ] 提交 `feat: 新增数据集文件上传与解析`，合并到 `main` 并推送至 `ican0506`。
