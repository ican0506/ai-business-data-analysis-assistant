# API 接口说明

接口根路径：`/api/v1`。除健康检查、注册和登录外均需 `Authorization: Bearer <token>`。

| 模块 | 方法 | 路径 | 说明 |
| --- | --- | --- | --- |
| 系统 | GET | `/health` | 健康检查 |
| 认证 | POST | `/auth/register` | 注册 |
| 认证 | POST | `/auth/login` | 返回 JWT |
| 认证 | GET | `/auth/me` | 当前用户 |
| 数据集 | POST | `/datasets/upload` | 上传 CSV/XLSX，最大 20MB |
| 数据集 | POST | `/datasets/{id}/clean` | 清洗数据 |
| 数据集 | GET | `/datasets/{id}/metrics` | 统计指标 |
| AI | POST | `/datasets/{id}/ai-analysis` | 生成业务报告 |
| 报告 | GET | `/datasets/{id}/reports/excel` | 下载 Excel |
| 报告 | GET | `/datasets/{id}/reports/word` | 下载 Word |
| 报告 | GET | `/datasets/{id}/reports/pdf` | 下载 PDF |
| 审计 | GET | `/audit-logs` | 管理员分页查询操作日志 |

返回包络：`{ "code": 0, "message": "...", "data": {} }`。错误响应使用 FastAPI 的 `detail` 字段；数据集相关接口还会校验资源归属。
