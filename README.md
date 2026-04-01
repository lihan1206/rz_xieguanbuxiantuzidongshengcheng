# 线缆/管道自动布线系统 (RouteGen)

<p align="center">
  <img src="docs/assets/logo.png" alt="RouteGen Logo" width="200"/>
</p>

<p align="center">
  <a href="https://github.com/your-org/route-gen/actions"><img src="https://github.com/your-org/route-gen/workflows/CI/CD%20Pipeline/badge.svg" alt="CI/CD"></a>
  <a href="https://codecov.io/gh/your-org/route-gen"><img src="https://codecov.io/gh/your-org/route-gen/branch/main/graph/badge.svg" alt="Coverage"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License"></a>
  <a href="https://github.com/your-org/route-gen/releases"><img src="https://img.shields.io/github/v/release/your-org/route-gen" alt="Release"></a>
</p>

## 📋 项目简介

RouteGen 是一个专业的线缆/管道自动布线系统，支持多用户协作，提供智能路径规划、3D可视化、多格式导出等功能。广泛应用于数据中心、工业厂房、建筑智能化等领域。

### 核心特性

- 🎯 **智能路径规划**：基于A*算法，支持障碍物避让、路径优化
- 🎨 **可视化设计**：2D/3D双模式，实时预览布线效果
- 📤 **多格式导出**：支持PDF、SVG、DXF、Excel等格式
- 👥 **多用户协作**：实时同步，权限管理
- 🔧 **灵活配置**：自定义约束条件、网格大小、单位系统
- 🚀 **高性能**：并行计算，支持大规模项目

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                        客户端层                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │  Web App │  │ Mobile   │  │ Desktop  │  │  API     │    │
│  │  (React) │  │ (RN)     │  │(Electron)│  │ (REST)   │    │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘    │
└───────┼─────────────┼─────────────┼─────────────┼──────────┘
        │             │             │             │
        └─────────────┴─────────────┴─────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                      网关层 (Nginx)                          │
└─────────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   前端服务    │  │   后端API    │  │  算法引擎    │
│  (React/Vite)│  │(Node/NestJS) │  │(Python/FastAPI)│
└──────────────┘  └──────┬───────┘  └──────────────┘
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│    MySQL     │  │    Redis     │  │    MinIO     │
│   (主数据库)  │  │ (缓存/队列)   │  │  (对象存储)   │
└──────────────┘  └──────────────┘  └──────────────┘
```

## 🚀 快速开始

### 环境要求

- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Node.js**: 20 LTS (本地开发)
- **Python**: 3.11+ (本地开发)
- **Git**: 2.30+

### 使用 Docker Compose 部署

1. **克隆仓库**

```bash
git clone https://github.com/your-org/route-gen.git
cd route-gen
```

2. **配置环境变量**

```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库密码、JWT密钥等
```

3. **启动服务**

```bash
# 开发环境
docker-compose up -d

# 生产环境
docker-compose -f docker-compose.prod.yml up -d
```

4. **访问应用**

- 前端界面: http://localhost:8080
- API文档: http://localhost:3000/api/docs
- MinIO控制台: http://localhost:9001 (minioadmin/minioadmin)
- Grafana监控: http://localhost:3001 (admin/admin)

### 本地开发环境搭建

#### 前端开发

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 运行测试
npm run test

# 构建生产版本
npm run build
```

#### 后端开发

```bash
cd backend

# 安装依赖
npm install

# 配置环境变量
cp .env.example .env

# 数据库迁移
npx prisma migrate dev

# 启动开发服务器
npm run start:dev

# 运行测试
npm run test
```

#### 算法服务开发

```bash
cd algorithm

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 启动服务
uvicorn main:app --reload --port 8000

# 运行测试
pytest
```

## 📁 项目结构

```
route-gen/
├── frontend/                 # 前端应用 (React + TypeScript)
│   ├── src/
│   │   ├── components/      # 组件
│   │   ├── pages/           # 页面
│   │   ├── hooks/           # 自定义Hooks
│   │   ├── stores/          # 状态管理
│   │   ├── utils/           # 工具函数
│   │   └── types/           # TypeScript类型
│   ├── public/              # 静态资源
│   └── Dockerfile           # 前端Dockerfile
│
├── backend/                  # 后端API (NestJS)
│   ├── src/
│   │   ├── modules/         # 业务模块
│   │   │   ├── auth/        # 认证模块
│   │   │   ├── users/       # 用户模块
│   │   │   ├── projects/    # 项目模块
│   │   │   ├── devices/     # 设备模块
│   │   │   ├── connections/ # 连接模块
│   │   │   └── exports/     # 导出模块
│   │   ├── common/          # 公共模块
│   │   └── main.ts          # 入口文件
│   ├── prisma/              # 数据库模型
│   └── Dockerfile           # 后端Dockerfile
│
├── algorithm/                # 算法服务 (Python)
│   ├── astar.py             # A*路径算法
│   ├── path_planner.py      # 路径规划器
│   ├── export_service.py    # 导出服务
│   ├── main.py              # FastAPI入口
│   └── Dockerfile           # 算法服务Dockerfile
│
├── database/                 # 数据库脚本
│   ├── init/                # 初始化脚本
│   └── migrations/          # 迁移脚本
│
├── docs/                     # 文档
│   ├── SYSTEM_ARCHITECTURE.md
│   ├── API_DESIGN.md
│   └── DEPLOYMENT.md
│
├── nginx/                    # Nginx配置
│   ├── nginx.conf
│   └── nginx.prod.conf
│
├── monitoring/               # 监控配置
│   ├── prometheus.yml
│   └── grafana/
│
├── docker-compose.yml        # 开发环境配置
├── docker-compose.prod.yml   # 生产环境配置
└── README.md                 # 本文件
```

## 🔧 核心模块

### 1. 用户管理模块
- JWT认证与授权
- RBAC权限模型
- OAuth2.0第三方登录
- 用户组与组织架构

### 2. 设备输入模块
- CAD图纸导入 (DXF/DWG)
- 设备库管理
- 批量导入导出
- 参数校验

### 3. 连接规划模块
- 可视化连接编辑
- 约束条件管理
- 优先级设置
- 冲突检测

### 4. 路径算法模块
- A*寻路算法
- 3D网格空间划分
- 多目标路径规划
- 并行计算加速

### 5. 导出引擎模块
- PDF报告生成
- SVG矢量图导出
- Excel材料清单
- CAD图纸导出

### 6. API接口模块
- RESTful API
- WebSocket实时通信
- API版本控制
- 请求限流

## 📊 数据库设计

### 核心表结构

| 表名 | 说明 | 主要字段 |
|------|------|----------|
| users | 用户表 | id, username, email, role, status |
| projects | 项目表 | id, name, type, status, owner_id, settings |
| devices | 设备表 | id, project_id, name, type, position, dimensions |
| connections | 连接表 | id, project_id, source_id, target_id, type, path_data |
| routes | 路径表 | id, connection_id, path_points, total_length, is_optimal |
| obstacles | 障碍物表 | id, project_id, type, position, dimensions |
| exports | 导出记录表 | id, project_id, type, file_url, status |

详细设计见 [数据库设计文档](docs/SYSTEM_ARCHITECTURE.md#数据库设计)

## 🔌 API 接口

### 基础信息

- **Base URL**: `https://api.routegen.com/v1`
- **认证方式**: Bearer Token (JWT)
- **数据格式**: JSON

### 主要接口

#### 认证
```http
POST /auth/login          # 登录
POST /auth/refresh        # 刷新Token
POST /auth/logout         # 登出
```

#### 项目
```http
GET    /projects              # 获取项目列表
POST   /projects              # 创建项目
GET    /projects/{id}         # 获取项目详情
PUT    /projects/{id}         # 更新项目
DELETE /projects/{id}         # 删除项目
```

#### 路径计算
```http
POST /projects/{id}/calculate-routes              # 批量计算路径
POST /projects/{id}/connections/{cid}/calculate-route  # 单条路径计算
```

#### 导出
```http
POST   /projects/{id}/exports     # 创建导出任务
GET    /exports/{id}              # 获取导出状态
GET    /exports/{id}/download     # 下载导出文件
```

完整API文档见 [API设计文档](docs/API_DESIGN.md)

## 🧪 测试

### 运行测试

```bash
# 前端测试
cd frontend
npm run test:unit        # 单元测试
npm run test:e2e         # E2E测试

# 后端测试
cd backend
npm run test             # 单元测试
npm run test:e2e         # E2E测试

# 算法测试
cd algorithm
pytest                   # 运行所有测试
pytest -v               # 详细输出
pytest --cov=app        # 覆盖率测试
```

### 测试覆盖率

| 模块 | 覆盖率 |
|------|--------|
| 前端 | 85% |
| 后端 | 88% |
| 算法 | 92% |

## 🚀 部署

### 使用 Docker Compose 部署

```bash
# 1. 拉取最新代码
git pull origin main

# 2. 构建并启动
docker-compose -f docker-compose.prod.yml up -d --build

# 3. 查看日志
docker-compose -f docker-compose.prod.yml logs -f

# 4. 停止服务
docker-compose -f docker-compose.prod.yml down
```

### 使用 Kubernetes 部署

```bash
# 应用配置
kubectl apply -k k8s/production/

# 查看状态
kubectl get pods -n production

# 查看日志
kubectl logs -f deployment/backend -n production
```

详细部署指南见 [部署文档](docs/DEPLOYMENT.md)

## 📈 监控与日志

### 监控指标

- **应用指标**: Prometheus + Grafana
- **日志聚合**: ELK Stack (Elasticsearch + Logstash + Kibana)
- **链路追踪**: Jaeger
- **告警通知**: AlertManager + Slack

### 访问监控面板

- Grafana: http://localhost:3001
- Prometheus: http://localhost:9090
- Kibana: http://localhost:5601

## 🤝 贡献指南

我们欢迎所有形式的贡献！

### 提交Issue

- 使用Issue模板描述问题
- 提供复现步骤和环境信息
- 标注相关标签

### 提交PR

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

### 代码规范

- 前端: ESLint + Prettier
- 后端: ESLint + TypeScript严格模式
- Python: PEP8 + Black + isort
- 提交信息: 遵循 Conventional Commits

## 📄 许可证

本项目采用 [MIT 许可证](LICENSE) 开源。

## 🙏 致谢

感谢以下开源项目的支持：

- [React](https://react.dev/)
- [NestJS](https://nestjs.com/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Three.js](https://threejs.org/)
- [Ant Design](https://ant.design/)

## 📞 联系我们

- **邮箱**: support@routegen.com
- **官网**: https://routegen.com
- **文档**: https://docs.routegen.com
- **GitHub Issues**: https://github.com/your-org/route-gen/issues

---

<p align="center">
  Made with ❤️ by RouteGen Team
</p>
