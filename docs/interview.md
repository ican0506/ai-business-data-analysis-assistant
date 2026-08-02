# 面试材料

## 1 分钟项目介绍

我开发了一个面向企业销售运营的 AI 数据分析助手。用户上传 Excel 或 CSV 后，系统自动完成字段解析、数据清洗、销售指标计算和 ECharts 驾驶舱展示；随后基于真实指标生成业务摘要、异常风险和行动建议，并能导出 Excel、Word、PDF 报告。项目采用 Vue3 + FastAPI + MySQL，使用 JWT 做资源归属校验，并通过 Docker Compose 降低部署复杂度。

## 技术难点

1. **非结构化表格兼容**：处理 CSV 编码、字段别名、日期与金额标准化，且保留原始文件。
2. **AI 结果可靠性**：Prompt 明确要求基于指标输出、不编造数据；LLM 不可用时降级为规则引擎。
3. **前端状态一致性**：Axios 拦截器统一 JWT、加载计数、错误提示和 401 退出；无历史接口时明确使用本机缓存而非伪造服务端数据。

## 为什么使用 Vue3

组件化适合驾驶舱、数据集、报告等多页面后台；Composition API 便于复用状态逻辑，Vue Router 与 Pinia 分别解决访问控制和认证态管理，Element Plus 可保证企业后台视觉一致性。

## AI 模块设计

先由 MetricsService 计算可追溯指标，再将指标传递给 DeepSeek。模型输出摘要、异常、问题和建议 JSON；服务端保留相同返回结构的规则降级路径，兼顾演示稳定性与真实 AI 能力。

## Docker 部署流程

通过 `.env` 注入 MySQL 与 LLM 配置，Docker Compose 启动 MySQL 与 FastAPI，healthcheck 确保数据库可用后再启动后端；生产环境配合 Nginx、HTTPS、持久卷与备份。

## 遇到的问题与解决方案

- GitHub 网络偶发连接失败：先验证本地 commit，再重试 push，避免误报已发布。
- Docker 端口被占用：通过调整宿主机端口映射并保留容器内部端口解决。
- 后端缺少部分历史查询接口：前端仅用 localStorage 保存本机展示记录，并明确提示其边界。
