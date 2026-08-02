# 系统架构

## 分层职责

- **前端**：Vue Router 管理页面访问，Pinia 保存认证态，Axios 统一附带 JWT、处理 401 与全局请求状态。
- **接口层**：FastAPI 负责鉴权、参数校验、HTTP 状态码和 Swagger/OpenAPI。
- **服务层**：DatasetService、DataCleaningService、MetricsService、AIAnalysisService、ReportService 承担业务编排。
- **数据层**：SQLAlchemy 管理 MySQL 中的用户、数据集、字段、清洗运行与操作日志。

## 关键数据流

1. 用户上传文件，后端解析并写入数据集元信息。
2. 清洗服务产生标准化 CSV 和清洗运行记录。
3. 指标服务基于最新清洗结果计算销售指标。
4. AI 服务把真实指标送入 DeepSeek Prompt；缺少密钥或调用失败时使用规则报告降级。
5. 报告服务复用分析结果生成 Excel、Word、PDF 流式下载。

## 权限边界

JWT 由登录接口签发；数据集的清洗、指标、AI 分析与导出均校验 `owner_id`，前端隐藏不构成权限控制。
