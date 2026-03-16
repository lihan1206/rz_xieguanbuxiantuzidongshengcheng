# 携观布线图自动生成软件

## 🛠 技术栈
- Frontend: React + Vite + Ant Design
- Backend: FastAPI + SQLAlchemy
- Database: MySQL 8.0

## 🚀 启动指南 (How to Run)
1. 确保 Docker Desktop 已启动。
2. 在根目录执行：`docker compose up --build`
3. 等待容器启动完成后访问系统。

## 🔗 服务地址 (Services)
- Frontend: http://localhost:13000
- Backend Swagger: http://localhost:8000/docs
- Backend Health: http://localhost:8000/health
- Database: localhost:13306 (user: xieguan / pass: xieguan123)

## 🧪 测试账号
- 管理员: admin / 123456

## ✅ 已实现功能
- 用户认证与权限基础（管理员、工程师）
- 项目管理（创建、筛选、删除）
- 设备与元件管理（真实数据库读写）
- 自动布线（最短路径规划）
- 规则校验与风险提示
- 历史版本快照
- 导出：PDF / SVG / DXF / JSON
- 删除操作采用 UI 确认弹窗，防误删

## 📦 目录结构
- `frontend/` 前端应用与 Nginx 配置
- `backend/` 后端应用、ORM 模型与 API
- `docker-compose.yml` 全链路容器编排
