# 数据库设计

数据库名默认 `ai_data_analysis`，时区字段由应用以 UTC 写入。

| 表 | 作用 | 关键字段 |
| --- | --- | --- |
| `users` | 用户与角色 | `username`、`email` 唯一；`password_hash`；`role` |
| `datasets` | 上传数据集 | `owner_id`、文件路径、状态、行列数、创建时间 |
| `dataset_columns` | 字段元信息 | 数据集 ID、字段名、类型、缺失/唯一值数量 |
| `dataset_cleaning_runs` | 清洗审计 | 原始/清洗行数、删除统计、输出路径 |
| `operation_logs` | 关键操作日志 | 用户、动作、目标、明细、时间 |

初始化脚本位于 `backend/sql/001_create_users_table.sql` 至 `003_create_dataset_cleaning_runs.sql`。生产环境建议改用 Alembic 管理增量迁移，避免直接删表或清空数据。
