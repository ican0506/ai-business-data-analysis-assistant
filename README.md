# AI 智能数据分析助手

面向企业运营场景的全栈数据分析平台。项目采用“确定性计算 + AI 解释”架构：Python / Pandas 负责数据清洗与可信数据准备，**MoonBit Core Engine 负责订单核心 KPI 与设备风险规则计算**，DeepSeek 只对结构化结果做解释和建议，不生成核心业务数值。

## 核心特点

- CSV/XLSX 上传、清洗记录、JWT 鉴权和操作审计
- `CanonicalFieldMapper` 自动字段映射，支持数据集级人工 override
- `AnalysisEngine + AnalysisPlanner` 选择可执行分析能力
- MoonBit 参与订单销售额、订单数、平均客单价，以及设备温度/振动/故障/状态风险规则
- Python / Pandas 完成真实数据准备；AI 只解释已有结构化结果
- Vue3 动态 Dashboard、字段映射、AI 报告与下载中心
- AI 数据问答（Data Chat）：基于已清洗订单数据的自然语言查询、数据依据展示与按数据集临时会话恢复
- DeepSeek 可选接入，调用失败自动降级为规则引擎
- 制造业生产经营驾驶舱、设备管理、设备诊断和经营报告快照
- Python 确定性预测：设备风险、能耗趋势、生产达成；AI 仅解释预测结果
- Docker Compose：MySQL、FastAPI、Nginx/Vue

## 技术栈

| 层级 | 技术 |
| --- | --- |
| 前端 | Vue 3、Vite、Pinia、Vue Router、Axios、Element Plus、ECharts |
| 后端 | FastAPI、SQLAlchemy、Pandas、NumPy、OpenPyXL、python-docx、ReportLab |
| MoonBit Core Engine | 订单核心 KPI（销售额、订单数、平均客单价）与设备风险阈值规则 |
| 数据库 | MySQL 8 |
| AI | DeepSeek（OpenAI-compatible）+ 规则 fallback |
| 部署 | Docker、Docker Compose、Nginx |

## 系统架构

```mermaid
flowchart TD
  U[用户] --> V[Vue 3 前端]
  V -->|REST API| F[FastAPI 接口层与业务编排]

  F --> J[JWT 认证]
  F --> D[数据集业务]
  F --> MF[制造业业务]
  F --> O[操作日志 / 审计]
  J --> M[(MySQL)]
  D <--> M
  MF <--> M
  O --> M

  M --- MT[生产记录、设备记录、能耗记录<br/>经营报告快照、预测运行快照]

  D <--> S[(Storage：原始 Excel/CSV 与清洗文件)]
  D --> C[数据清洗与字段映射]
  C -->|清洗记录、字段 override| M
  C --> E[AnalysisEngine / AnalysisPlan]
  E --> P[Pandas 数据校验、可信金额聚合与分析准备]
  P --> MB[MoonBit Core Engine<br/>订单 KPI 与设备风险规则]
  MB --> K[KPI、趋势、统计与异常检测]

  V --> DC[Vue Data Chat 页面]
  DC -->|用户问题 + dataset_id| DQ[Data Chat API]
  DQ --> QI[规则问题解析 / 受限 LLM 解析]
  QI --> QP[QueryPlan + Pydantic 白名单校验]
  QP --> MQ[MetricQueryEngine]
  MQ -->|复用 OrderAnalyzer| P
  MQ --> SR[Structured Result]
  SR --> AG[DeepSeek / 规则回答生成]
  AG --> DC

  K --> A[AI 解释服务]
  A -->|仅使用已计算的结构化指标| DS[DeepSeek V4 Pro 深度分析]
  A -. 调用失败 .-> RF[规则引擎回退]
  K --> R[报告导出：Excel / Word / PDF]

  MF --> MD[生产驾驶舱 / 设备管理]
  MF --> ED[设备规则诊断]
  ED --> MB
  MF --> BP[经营报告快照]
  MF --> FP[Python 确定性预测]
  FP -->|设备风险、能耗趋势、生产达成| PE[预测解释服务]
  PE -->|仅解释 prediction_result| A
  FP --> PR[预测运行快照]
  PE --> PR

  A --> X[分析结果]
  RF --> X
  K --> X
  X --> F
  R --> F
  F --> V
```

## MoonBit Core Engine：真实业务职责

仓库根目录的 [`moonbit/`](./moonbit) 是项目的一部分，不是演示代码。后端通过 [`MoonBitService`](./backend/app/services/moonbit_service.py) 使用 stdin JSON / stdout JSON 调用已构建的 MoonBit 原生程序。

| MoonBit 文件 | 实际业务职责 | Python 保留职责 |
| --- | --- | --- |
| `moonbit/core/kpi.mbt` | 对 Python 已验证的订单金额执行销售额、订单数、平均客单价计算 | CSV/XLSX 读取、Pandas 清洗、重复订单处理和可信金额校验 |
| `moonbit/core/risk.mbt` | 对温度、振动、故障次数和设备状态执行风险阈值规则 | 设备记录查询、既有告警文本与 FastAPI 响应编排 |
| `moonbit/cmd/main/main.mbt` | JSON 输入输出适配 | 超时控制、严格 JSON 校验、异常日志和 Python fallback |

真实调用链：

```text
Vue 3
  ↓ REST API
FastAPI
  ↓
Python / Pandas：读取、清洗、可信数据准备、业务编排
  ↓
MoonBit Core Engine：KPI / Risk / Rule Result
  ↓
Python：复用既有 Metrics、设备告警、报告与 Data Chat 链路
  ↓
DeepSeek：仅解释结构化结果
  ↓
Vue 3 展示
```

MoonBit 订单 KPI 输入：

```json
{"operation":"order_kpi","verified_order_amounts":[120.0,80.0,0.0]}
```

输出：

```json
{"sales_total":200.0,"order_count":3,"average_order_value":66.67}
```

设备风险输入：

```json
{"operation":"equipment_risk","temperature":85.0,"vibration":5.2,"fault_count":1,"status":"运行"}
```

当 MoonBit 引擎未配置、可执行文件不可用、超时、异常退出或返回非法 JSON 时，`MoonBitService` 会返回降级信号，`OrderAnalyzer` 与 `EquipmentManagementService` 自动复用原有 Python 计算，不改变现有 API 返回格式。

### MoonBit 验证状态

以下结果已在 MoonBit CLI `0.1.20260904`、`moonc v0.10.12` 环境中真实验证：

- `moon check`：通过；
- `moon check --deny-warn`：通过；
- `moon test`：4 / 4 passed；
- `moon build --target native --release`：通过，生成 `moonbit/_build/native/release/build/cmd/main/main.exe`；
- Python → `subprocess` → MoonBit native executable → stdin JSON → stdout JSON：通过。真实桥接测试验证订单金额 `[1200.0, 800.0, 0.0]` 返回销售总额 `2000.0`、订单数 `3`、平均客单价 `666.67`，并验证中文设备状态可通过 UTF-8 JSON 协议得到风险规则结果。

## 当前支持领域

| 领域 | 输出 |
| --- | --- |
| Order | 订单统计、可信销售额、客单价、商品/品类/地区分析、时间趋势、客户复购、状态/支付/折扣分析与数据质量检查（字段可用时） |
| StudentScore | 学生数、成绩概览、学科/班级/学生聚合、考试趋势（字段可用时） |
| Inventory | 库存概览、低库存、库存价值、分类/仓库/供应商汇总（字段可用时） |
| Generic | 行数、列画像、缺失值分析；是合法 fallback，不是系统错误 |

### 制造业生产经营模块

| 模块 | 数据来源 | 已实现能力 |
| --- | --- | --- |
| 生产经营驾驶舱 | `production_records`、`equipment_records`、`energy_records` | 今日产量、生产达成率、设备运行率、单位能耗、生产/能耗趋势和设备状态图表 |
| 设备管理 | `equipment_records` | 设备列表、详情、温度/振动历史趋势、基于阈值的异常提示 |
| AI 设备诊断 | 最新设备运行与异常规则结果 | 风险等级、问题分析、可能原因和处理建议；复用统一 AI 调用与规则降级 |
| AI 经营报告中心 | 生产、设备、能耗记录及诊断结果 | 生产/设备/能耗确定性指标、AI 总结、报告历史，以及 Excel/Word/PDF 快照导出 |
| 预测与预警 | 三类制造业历史记录 | 设备故障风险、能耗趋势、生产达成预测、风险统计、趋势图与预测历史 |

#### 制造业预测职责边界

- `EquipmentFailurePredictor` 依据温度、振动、故障次数和设备状态输出确定性设备风险。
- `EnergyConsumptionPredictor` 使用移动平均和趋势斜率预测单位能耗趋势与预警等级。
- `ProductionCompletionPredictor` 依据水泥实际产量与计划产量重新计算完成率，并判断生产达成趋势。
- 所有预测数值、趋势和风险等级均由 Python 产生并保存为 `manufacturing_prediction_runs` 快照；AI 不重算、不覆盖风险等级，也不新增数值、传感器数据或故障记录。
- `PredictionExplanationService` 仅向统一的 `AIAnalysisService` 提交 `prediction_result`、已确定风险等级与规则原因，返回 AI 总结、风险解释与建议；DeepSeek 不可用时自动回退规则解释。

`null` / `—` 表示不可分析或不适用，**不等于 0**；真实计算值为 `0` 会原样保留。Python / Pandas 是指标真值来源，AI 不计算或编造核心指标。

### 订单分析口径

- 支持确定性字段映射：`user_id → customer_id`、`user_name → customer_name`、`city → region`、`order_time → date`、`order_amount → sales_amount`，以及分类、折扣、支付方式、性别、年龄等常见订单字段。
- 销售统计使用可信金额：行内 `unit_price`、`quantity`、`discount` 都有效时优先计算 `unit_price × quantity × discount`；整个数据集没有折扣列时按 `unit_price × quantity`；无法计算但 `order_amount` 有效时才使用该原始金额。两者同时存在且不一致会被记录，不会静默覆盖。
- `record_count` 是实际记录行数，`order_count` 优先按非空 `order_id` 去重；完整重复行、重复订单号、非法日期/价格/数量/折扣/年龄/状态和金额不一致均在数据质量结果中说明。
- AI 只读取 Pandas 已计算的聚合结果，不接收原始整表、手机号、邮箱或备注；它负责解释、风险提示和建议，不重算销售额或编造业务指标。

## AI 数据问答 / Data Chat

Data Chat 当前仅支持 **Order 订单领域**。用户选择已完成清洗的数据集后，可以用自然语言查询真实业务指标；前端保留数据依据，而不是只展示 AI 文案。

- 规则解析优先；规则无法解析时，DeepSeek 仅生成受限 `QueryPlan`。
- `QueryPlan` 经过 Pydantic 白名单校验，只能执行已定义的订单指标、筛选、分组、排序和数量限制。
- `MetricQueryEngine` 复用统一 `OrderAnalyzer` 口径，由 Python / Pandas 计算真实结果。
- DeepSeek 只将结构化结果组织为中文回答，不接收完整原始 DataFrame，也不负责业务指标计算。
- DeepSeek 未配置、超时、异常、空回答或出现未验证数字时，自动使用 Rule Based fallback。
- 前端展示数据集、查询指标、日期范围、分组、筛选、问题解析方式、回答生成方式和已计算结果。

### 当前支持的查询

- 销售总额、销售数量、订单数量、平均客单价。
- 指定月份、指定日期范围。
- 商品、品类、地区筛选。
- 商品 / 品类 / 地区 Top N，以及“哪个地区销售额最高”这类无需明确数量的 Top 1 表达。
- 月度趋势。

示例：

- `2026年5月销售总额是多少？`
- `2026年5月销售数量是多少？`
- `2026年5月有多少订单？`
- `哪个地区销售额最高？`
- `销售额最高的5个商品是什么？`
- `每个月销售额是多少？`

### Data Chat 可信度边界

```text
用户问题
  → Rule Based Question Interpreter
  → （必要时）LLM 受限解析
  → QueryPlan
  → Pydantic 校验
  → MetricQueryEngine
  → Python / Pandas 确定性计算
  → Structured Result
  → DeepSeek / Rule Based Answer
  → Vue Data Chat 页面
```

LLM 不负责业务指标计算，Python / Pandas 是数据真值来源。Data Chat 与 Dashboard、AI Report 复用统一 `OrderAnalyzer` 指标口径，`sales_amount`、`order_count`、`average_order_value` 不会单独重新实现。缺失字段导致的 **无法计算不等于 0**：系统会返回明确不可用原因，不会伪造 0；真实计算值为 0 时会如实保留。

### Data Chat 前端体验与临时会话

- 支持数据集选择、推荐问题、用户 / AI 消息气泡、DeepSeek / Rule Based 回答模式标识和“查看数据依据”。
- 当前浏览器标签页内使用 `sessionStorage` 临时保存最近选择的数据集和消息；切换页面或刷新后可以恢复。
- 聊天记录按 `dataset_id` 隔离，清空对话只影响当前数据集。
- 会话恢复仅用于 UI 展示；每次请求仍只向后端发送 `dataset_id` 与 `question`，不是多轮上下文。

## 快速开始

### 数据库与后端

先创建空数据库，例如：

```sql
CREATE DATABASE ai_data_analysis DEFAULT CHARACTER SET utf8mb4;
```

复制 `backend/.env.example` 为 `backend/.env`，填写 MySQL 连接、JWT 随机密钥和可选 LLM 配置：

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

Swagger：<http://127.0.0.1:8000/docs>

首次启动会由 SQLAlchemy `Base.metadata.create_all()` 创建当前模型表。已有 MySQL 数据库可按顺序执行 `backend/sql/001_create_users_table.sql` 至 `backend/sql/009_create_manufacturing_prediction_runs.sql`；项目未使用 Alembic。

其中 `006` 创建制造业生产/设备/能耗表，`007` 写入演示数据，`008` 创建制造业经营报告快照表，`009` 创建制造业预测运行快照表。生产数据库执行 `007` 前请确认需要演示数据。

`STORAGE_ROOT` 对应的上传和清洗目录会由应用运行时创建；运行数据不应提交到 Git。

### 前端

```powershell
cd frontend/vue-app
Copy-Item .env.example .env.local
npm install
npm run dev
```

默认地址：<http://127.0.0.1:5173>。Axios 仅从 `VITE_API_BASE_URL` 读取 API 地址；留空时 Vite 的 `/api` 代理使用 `VITE_API_PROXY_TARGET`（默认 `http://127.0.0.1:8000`）。

### MoonBit Core Engine（可选启用，真实业务计算）

先按 [MoonBit 官方安装文档](https://docs.moonbitlang.com/en/latest/) 安装 MoonBit CLI。当前后端在未配置 MoonBit 引擎时仍可安全运行，并使用既有 Python 确定性计算；要让 MoonBit 实际处理订单 KPI 与设备风险规则，请执行：

```powershell
cd moonbit
moon check --deny-warn
moon test
moon build --target native --release
```

构建后的 Windows 原生程序位于模块内的相对路径：

```text
moonbit/_build/native/release/build/cmd/main/main.exe
```

将该程序的绝对路径填入 `backend/.env`：

```dotenv
MOONBIT_ENGINE_ENABLED=true
MOONBIT_ENGINE_PATH=C:\absolute\path\to\moonbit-core.exe
MOONBIT_ENGINE_TIMEOUT_SECONDS=1
```

单独验证 JSON 协议：

```powershell
cd moonbit
$moonbitExe = Resolve-Path '.\_build\native\release\build\cmd\main\main.exe'
'{"operation":"order_kpi","verified_order_amounts":[120.0,80.0]}' | & $moonbitExe

'{"operation":"equipment_risk","temperature":85.0,"vibration":5.2,"fault_count":1,"status":"运行"}' | & $moonbitExe
```

### Docker Compose

```powershell
Copy-Item .env.example .env
# 编辑 .env：替换 MYSQL_ROOT_PASSWORD、JWT_SECRET_KEY；如使用 DeepSeek 再替换 LLM_API_KEY
docker compose config
# 首次启动：前台构建并启动，便于查看 MySQL 初始化和服务日志
docker compose up --build
```

首次启动成功后，可按 `Ctrl+C` 停止前台进程，再使用后台模式：

```powershell
docker compose up -d
docker compose ps
```

访问地址：

- 前端：<http://localhost>
- 后端：<http://localhost:8000>
- Swagger：<http://localhost:8000/docs>

停止服务但保留数据库数据：

```powershell
docker compose down
```

MySQL 在**首次创建空的 `mysql_data` volume** 时，会按文件名顺序执行 `backend/sql/001` 至 `008`：创建用户、数据集、清洗记录、审计日志、字段映射、制造业表、演示数据和经营报告表。已有 volume 不会重复执行这些 SQL；不要随意执行 `docker compose down -v`，否则会删除本地数据库数据。

## 环境变量

根目录 `.env.example` 仅供 Docker Compose：

| 变量 | 用途 |
| --- | --- |
| `MYSQL_ROOT_PASSWORD` | MySQL root 密码，同时传给后端 |
| `JWT_SECRET_KEY` | JWT 签名密钥，生产环境使用至少 32 位随机值 |
| `MYSQL_DATABASE`、`MYSQL_PORT` | Compose 数据库名和端口 |
| `FRONTEND_PORT`、`BACKEND_PORT` | Nginx 与 FastAPI 主机端口 |
| `CORS_ALLOWED_ORIGINS` | 允许凭据访问的浏览器 Origin 白名单 |
| `LLM_PROVIDER`、`LLM_API_KEY`、`LLM_BASE_URL`、`LLM_MODEL`、`LLM_TIMEOUT_SECONDS` | 可选大模型配置；DeepSeek 思考模式示例使用 `deepseek-v4-pro`，默认 25 秒超时且不自动重试，失败时降级规则分析 |
| `MOONBIT_ENGINE_ENABLED`、`MOONBIT_ENGINE_PATH`、`MOONBIT_ENGINE_TIMEOUT_SECONDS` | MoonBit 核心计算引擎开关、原生程序绝对路径与子进程超时；不可用时自动回退 Python |

`backend/.env.example` 用于本地后端，包含 MySQL、存储、上传大小、JWT 和 LLM 变量。`frontend/vue-app/.env.example` 用于前端 API 地址和 Vite 代理。所有 `.env` 文件均被 Git 忽略。

## 使用流程

通用数据分析流程：注册 / 登录 → 上传 CSV/XLSX → 清洗 → 自动映射与领域识别 → 必要时人工 override → 动态 Dashboard / AI 数据问答 → AI 分析 → 导出 Excel/Word/PDF。

制造业流程：登录 → 生产经营驾驶舱 → 设备管理与异常诊断 → 生成经营报告快照或预测快照 → 查看 Python 指标/预测趋势 → 查看 AI 解释或规则降级解释。

制造业预测页面入口：<http://127.0.0.1:5173/manufacturing/prediction>。预测详情中的 AI 解释来自已保存快照；历史快照没有解释字段时前端会显示空状态，但预测结果与图表仍可正常查看。

字段 override 使用 `PUT /api/v1/datasets/{id}/field-mapping` 全量替换：

```json
{"overrides": {"学生编号": "student_id", "课程名": "subject", "总评": "score"}}
```

`{"overrides": {}}` 可恢复自动映射。覆盖优先级为用户 override > 自动 alias > 原始字段，且只作用于内存分析副本，不改写原始或清洗文件。

## 示例数据

`examples/` 中四份 UTF-8、无隐私 CSV 可直接上传：

- `order_sample.csv`：订单编号、商品名称、数量、单价、区域、订单日期
- `student_score_sample.csv`：学号、学生姓名、科目、成绩、班级、考试日期
- `inventory_sample.csv`：商品编号、商品名称、库存数量、安全库存、单位成本、仓库
- `generic_sample.csv`：姓名、城市、备注

## API、CORS 与目录

FastAPI 内置 Swagger，开发环境访问 `/docs`。主要接口类别为认证、数据集、字段映射、指标、AI、Data Chat、报告、审计日志，以及制造业生产/设备/诊断/经营报告/预测。

CORS 使用 `CORS_ALLOWED_ORIGINS` 白名单并允许凭据，不使用 `*`。Docker Nginx 将 `/api/` 代理至 FastAPI。Docker 的 `./storage` 挂载到后端 `/storage`，用于上传与清洗结果。

## 测试

```powershell
cd backend
python -m pytest tests -q

cd ../frontend/vue-app
npm run test
npm run build

cd ../../moonbit
moon check --deny-warn
moon test
moon build --target native --release
```

MoonBit 测试需要本机已安装 MoonBit CLI；本仓库把 MoonBit 编译输出与依赖缓存忽略，不提交平台相关二进制文件。

项目没有独立 lint 脚本。不要提交 `.env`、密钥、上传/清洗/报告文件、日志、虚拟环境、`node_modules`、`dist` 或 `coverage`。

## 项目目录

```text
backend/                 FastAPI、通用与制造业领域服务、预测器、SQL 补丁、测试
frontend/vue-app/        Vue 3 前端
examples/                可直接演示的 CSV
storage/                 运行数据（忽略实际内容）
docs/                    架构、数据库、部署说明
docker-compose.yml       MySQL + Backend + Nginx
```

## 已知限制

- 暂不支持 fuzzy/embedding/LLM 自动字段映射。
- 暂不支持库存预测、EOQ、ABC 分类、学生 GPA、自动业务规则推断或更多领域。
- Data Chat 当前仅支持 Order 领域；不支持数据库聊天历史、跨设备同步、真正多轮上下文、Streaming、WebSocket、Agent、SQL Agent 或 RAG。
- Data Chat 的 LLM 不直接计算业务指标，也不会接收完整原始 DataFrame。
- 制造业预测采用可解释的移动平均、简单趋势和阈值规则，不包含在线训练、深度学习或复杂机器学习模型。
- AI 不重算指标；外部模型失败时返回规则解释。
- Compose 适合单机演示；真实生产仍需 HTTPS、备份、日志轮转和专用密钥管理。

## 安全说明

不要提交 API Key、数据库密码、JWT 密钥、个人 Token、上传文件或报告。仓库中的示例数据均为虚构演示数据。
