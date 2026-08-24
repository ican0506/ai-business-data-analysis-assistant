# 制造业经营报告快照（第一轮）实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 `superpowers:executing-plans` 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法跟踪进度。

**目标：** 为制造业经营分析报告建立不可变数据库快照、最小持久化服务和详情查询能力。

**架构：** 新增 `ManufacturingBusinessReport` SQLAlchemy 模型，以 JSON 保存完整报告快照；`ManufacturingBusinessReportService` 只负责创建、保存和按用户读取详情。本轮不接入 AI、导出、路由或 Vue。

**技术栈：** FastAPI 项目既有 SQLAlchemy、Pydantic、MySQL SQL migration、pytest。

---

### 任务 1：模型、迁移与 Schema

**文件：**
- 创建：`backend/app/models/manufacturing_business_report.py`
- 创建：`backend/app/schemas/manufacturing_business_report.py`
- 创建：`backend/sql/008_create_manufacturing_business_reports.sql`
- 修改：`backend/app/db/session.py`
- 测试：`backend/tests/test_manufacturing_business_report.py`

- [ ] **步骤 1：编写失败测试**

```python
def test_report_snapshot_model_persists_json_and_generation_metadata(db):
    report = ManufacturingBusinessReport(
        user_id=1,
        title="测试报告",
        risk_level="中风险",
        ai_mode="rule_based",
        summary="测试摘要",
        snapshot={"kpis": {"cement_output": 6500}},
        generated_at=datetime(2026, 8, 1, tzinfo=timezone.utc),
    )
    db.add(report); db.commit(); db.refresh(report)
    assert report.snapshot["kpis"]["cement_output"] == 6500
```

- [ ] **步骤 2：运行测试验证失败**

运行：`python -m pytest tests/test_manufacturing_business_report.py::test_report_snapshot_model_persists_json_and_generation_metadata -q`

预期：因模型尚不存在而失败。

- [ ] **步骤 3：实现最小模型、Schema、迁移注册**

模型必须包含 `id`、`user_id`、`title`、`period_start`、`period_end`、`risk_level`、`ai_mode`、`summary`、`snapshot`、`generated_at`、`created_at`；数据库 migration 使用 `CREATE TABLE IF NOT EXISTS` 和 `(user_id, generated_at)` 联合索引。

- [ ] **步骤 4：运行模型测试验证通过**

运行：同步骤 2。预期：PASS。

### 任务 2：快照持久化服务

**文件：**
- 创建：`backend/app/services/manufacturing_business_report_service.py`
- 测试：`backend/tests/test_manufacturing_business_report.py`

- [ ] **步骤 1：编写失败测试**

```python
def test_service_creates_and_reads_immutable_report_snapshot(db, user):
    service = ManufacturingBusinessReportService()
    created = service.create_snapshot(db, user.id, payload)
    payload["snapshot"]["kpis"]["cement_output"] = 0
    detail = service.get_detail(db, user.id, created["id"])
    assert detail["snapshot"]["kpis"]["cement_output"] == 6500
```

- [ ] **步骤 2：运行测试验证失败**

运行：`python -m pytest tests/test_manufacturing_business_report.py::test_service_creates_and_reads_immutable_report_snapshot -q`

预期：因服务尚不存在而失败。

- [ ] **步骤 3：实现最小服务**

`create_snapshot` 必须在 commit 前深拷贝 JSON 兼容载荷；`get_detail` 必须按 `id` 和 `user_id` 查询，以保证后续 API 可复用用户隔离约束。

- [ ] **步骤 4：运行定向服务测试验证通过**

运行：同步骤 2。预期：PASS。

### 任务 3：迁移文本与定向回归

**文件：**
- 测试：`backend/tests/test_manufacturing_business_report.py`

- [ ] **步骤 1：编写迁移失败测试**

```python
def test_business_report_migration_declares_snapshot_and_history_indexes():
    content = migration.read_text(encoding="utf-8").lower()
    assert "create table if not exists manufacturing_business_reports" in content
    assert "snapshot json not null" in content
    assert "idx_manufacturing_business_reports_user_generated" in content
```

- [ ] **步骤 2：运行测试验证失败**

运行：`python -m pytest tests/test_manufacturing_business_report.py -q`

预期：因 migration 尚不存在而失败。

- [ ] **步骤 3：实现 migration**

创建 `008_create_manufacturing_business_reports.sql`，不修改任何已有表或 migration。

- [ ] **步骤 4：运行定向回归**

运行：`python -m pytest tests/test_manufacturing_business_report.py -q`

预期：全部 PASS。

### 任务 4：最终验证

**文件：** 本轮新增或修改的后端文件。

- [ ] **步骤 1：运行本轮定向测试**

运行：`python -m pytest tests/test_manufacturing_business_report.py -q`

- [ ] **步骤 2：检查 diff 格式**

运行：`git diff --check`

- [ ] **步骤 3：检查范围**

运行：`git status --short`

预期：仅包含模型、Schema、Service、迁移、数据库注册、测试与本计划文档。
