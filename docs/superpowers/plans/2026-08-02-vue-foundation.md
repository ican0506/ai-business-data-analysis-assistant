# Vue 3 前端迁移第一阶段实现计划

**目标：** 在不修改 FastAPI 接口和不删除原生前端的前提下，创建可独立启动的 Vue 3 基础工程，并完成登录和 JWT Token 本地保存。

**架构：** Vue 工程放在 `frontend/vue-app/`，Vite 开发服务器通过 `/api` 代理转发到 FastAPI `http://127.0.0.1:8000`。Axios 请求实例统一从 localStorage 读取 Token 并注入 Bearer 请求头；Pinia 管理登录用户与认证状态。

## 任务

1. 创建 Vite + Vue 3 工程配置，加入 Vue Router、Pinia、Axios，并将构建产物排除在 Git 之外。
2. 编写路由与认证状态 Store；登录页调用既有 `/api/v1/auth/login`，成功后保存 Token 并跳转到占位工作台。
3. 编写最小组件测试/构建验证，启动 Vite 后通过代理验证登录接口。

## 验收

- `npm run dev` 能启动前端开发服务器。
- 未登录访问工作台会跳转到登录页。
- 登录成功后 localStorage 保存 `ai_insight_token`。
- Axios 请求 `GET /api/v1/auth/me` 自动携带 JWT。
- 不改动任何 FastAPI 路由与后端业务代码。
