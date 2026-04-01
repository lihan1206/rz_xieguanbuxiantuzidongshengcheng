# 线缆/管道自动布线系统架构设计

## 1. 系统架构概览

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              客户端层 (Client Layer)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Web App    │  │  Mobile App  │  │   Desktop    │  │  第三方集成   │     │
│  │   (React)    │  │  (React Native)│  │   (Electron) │  │   (API)      │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
└─────────┼─────────────────┼─────────────────┼─────────────────┼─────────────┘
          │                 │                 │                 │
          └─────────────────┴─────────────────┴─────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           网关层 (Gateway Layer)                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      Nginx / API Gateway                             │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │   │
│  │  │  负载均衡    │  │  限流熔断    │  │  SSL终结    │  │  路由转发   │ │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          应用服务层 (Application Layer)                       │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Node.js / Express / NestJS                        │   │
│  │                                                                      │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │   │
│  │  │ 用户管理  │ │ 设备输入  │ │ 连接规划  │ │ 路径算法  │ │ 导出引擎  │  │   │
│  │  │  服务     │ │  服务     │ │  服务     │ │  服务     │ │  服务     │  │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘  │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐               │   │
│  │  │ 项目管理  │ │ 协作服务  │ │ 通知服务  │ │ 日志服务  │               │   │
│  │  │  服务     │ │  服务     │ │  服务     │ │  服务     │               │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          算法引擎层 (Algorithm Layer)                         │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     Python / FastAPI / Celery                        │   │
│  │                                                                      │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │  │   A* 算法    │  │  路径优化    │  │  碰撞检测    │              │   │
│  │  │   引擎       │  │   引擎       │  │   引擎       │              │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │  │  网格生成    │  │  成本计算    │  │  并行计算    │              │   │
│  │  │   引擎       │  │   引擎       │  │   引擎       │              │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          数据层 (Data Layer)                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   MySQL      │  │    Redis     │  │  MinIO/S3    │  │ Elasticsearch │    │
│  │  (主数据库)   │  │  (缓存/会话)  │  │  (文件存储)   │  │  (全文搜索)   │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         基础设施层 (Infrastructure Layer)                     │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Docker     │  │  Kubernetes  │  │  Prometheus  │  │    Grafana   │     │
│  │  (容器化)     │  │  (编排)       │  │  (监控)       │  │  (可视化)     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                        │
│  │ GitHub Actions│  │    ELK       │  │   Jaeger     │                        │
│  │   (CI/CD)    │  │  (日志聚合)   │  │  (链路追踪)   │                        │
│  └──────────────┘  └──────────────┘  └──────────────┘                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 2. 核心模块划分

### 2.1 用户管理模块 (User Management)
- **功能**: 用户注册、登录、权限管理、角色分配
- **子功能**:
  - JWT认证与授权
  - OAuth2.0第三方登录
  - RBAC权限模型
  - 用户组与组织架构

### 2.2 设备输入模块 (Device Input)
- **功能**: 设备信息录入、CAD图纸导入、参数配置
- **子功能**:
  - 支持DXF/DWG格式导入
  - 设备库管理
  - 批量导入导出
  - 设备参数校验

### 2.3 连接规划模块 (Connection Planning)
- **功能**: 定义连接关系、约束条件、优先级设置
- **子功能**:
  - 连接关系可视化编辑
  - 约束条件管理（长度、弯曲半径等）
  - 优先级与权重设置
  - 冲突检测

### 2.4 路径算法模块 (Path Algorithm)
- **功能**: A*路径计算、障碍物避让、路径优化
- **子功能**:
  - 3D网格空间划分
  - A*寻路算法
  - 多目标路径规划
  - 并行计算加速

### 2.5 导出引擎模块 (Export Engine)
- **功能**: 多格式导出、报告生成、图纸输出
- **子功能**:
  - PDF报告生成
  - SVG矢量图导出
  - Excel材料清单
  - CAD图纸导出

### 2.6 API接口模块 (API Gateway)
- **功能**: RESTful API、WebSocket实时通信、版本管理
- **子功能**:
  - API版本控制
  - 请求限流
  - 接口文档(Swagger)
  - 实时协作同步

## 3. 技术栈选择

### 3.1 前端技术栈
| 层级 | 技术 | 用途 |
|------|------|------|
| 框架 | React 18 + TypeScript | UI开发 |
| 状态管理 | Zustand / Redux Toolkit | 全局状态 |
| UI组件 | Ant Design / Material-UI | 组件库 |
| 图形渲染 | Three.js / React-Three-Fiber | 3D可视化 |
| 2D绘图 | Fabric.js / Konva.js | 2D图纸编辑 |
| 构建工具 | Vite | 构建优化 |
| 测试 | Jest + React Testing Library | 单元测试 |

### 3.2 后端技术栈
| 层级 | 技术 | 用途 |
|------|------|------|
| 运行时 | Node.js 20 LTS | 服务端运行 |
| 框架 | NestJS | 企业级框架 |
| 算法服务 | Python 3.11 + FastAPI | 路径计算 |
| 任务队列 | BullMQ (Redis) | 异步任务 |
| ORM | Prisma / TypeORM | 数据库操作 |
| 文档 | Swagger/OpenAPI | API文档 |

### 3.3 数据库技术栈
| 类型 | 技术 | 用途 |
|------|------|------|
| 关系型数据库 | MySQL 8.0 | 主数据存储 |
| 缓存 | Redis 7.x | 会话/缓存/队列 |
| 对象存储 | MinIO / AWS S3 | 文件存储 |
| 搜索引擎 | Elasticsearch | 全文搜索 |

### 3.4 运维技术栈
| 类型 | 技术 | 用途 |
|------|------|------|
| 容器化 | Docker + Docker Compose | 本地开发 |
| 编排 | Kubernetes | 生产部署 |
| CI/CD | GitHub Actions | 自动化流程 |
| 监控 | Prometheus + Grafana | 性能监控 |
| 日志 | ELK Stack | 日志聚合 |

## 4. 数据库设计

### 4.1 用户表 (users)
```sql
CREATE TABLE users (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    username        VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
    email           VARCHAR(100) NOT NULL UNIQUE COMMENT '邮箱',
    password_hash   VARCHAR(255) NOT NULL COMMENT '密码哈希',
    avatar          VARCHAR(255) COMMENT '头像URL',
    role            ENUM('admin', 'engineer', 'viewer') DEFAULT 'engineer' COMMENT '角色',
    status          ENUM('active', 'inactive', 'suspended') DEFAULT 'active' COMMENT '状态',
    department_id   BIGINT UNSIGNED COMMENT '部门ID',
    last_login_at   TIMESTAMP NULL COMMENT '最后登录时间',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_email (email),
    INDEX idx_department (department_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';
```

### 4.2 设备表 (devices)
```sql
CREATE TABLE devices (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    project_id      BIGINT UNSIGNED NOT NULL COMMENT '项目ID',
    name            VARCHAR(100) NOT NULL COMMENT '设备名称',
    type            VARCHAR(50) NOT NULL COMMENT '设备类型',
    model           VARCHAR(100) COMMENT '设备型号',
    position_x      DECIMAL(10, 3) NOT NULL COMMENT 'X坐标',
    position_y      DECIMAL(10, 3) NOT NULL COMMENT 'Y坐标',
    position_z      DECIMAL(10, 3) DEFAULT 0 COMMENT 'Z坐标',
    rotation        DECIMAL(5, 2) DEFAULT 0 COMMENT '旋转角度',
    width           DECIMAL(10, 3) COMMENT '宽度',
    height          DECIMAL(10, 3) COMMENT '高度',
    depth           DECIMAL(10, 3) COMMENT '深度',
    properties      JSON COMMENT '扩展属性',
    created_by      BIGINT UNSIGNED NOT NULL COMMENT '创建者',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_project (project_id),
    INDEX idx_type (type),
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='设备表';
```

### 4.3 连接表 (connections)
```sql
CREATE TABLE connections (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    project_id      BIGINT UNSIGNED NOT NULL COMMENT '项目ID',
    name            VARCHAR(100) COMMENT '连接名称',
    source_device_id BIGINT UNSIGNED NOT NULL COMMENT '源设备ID',
    target_device_id BIGINT UNSIGNED NOT NULL COMMENT '目标设备ID',
    source_port     VARCHAR(50) COMMENT '源端口',
    target_port     VARCHAR(50) COMMENT '目标端口',
    type            ENUM('cable', 'pipe', 'conduit') NOT NULL COMMENT '连接类型',
    status          ENUM('planned', 'routed', 'installed') DEFAULT 'planned' COMMENT '状态',
    priority        INT DEFAULT 5 COMMENT '优先级(1-10)',
    constraints     JSON COMMENT '约束条件',
    path_data       JSON COMMENT '路径数据(点序列)',
    length          DECIMAL(10, 3) COMMENT '路径长度',
    created_by      BIGINT UNSIGNED NOT NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_project (project_id),
    INDEX idx_source (source_device_id),
    INDEX idx_target (target_device_id),
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (source_device_id) REFERENCES devices(id),
    FOREIGN KEY (target_device_id) REFERENCES devices(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='连接表';
```

### 4.4 路径表 (routes)
```sql
CREATE TABLE routes (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    connection_id   BIGINT UNSIGNED NOT NULL COMMENT '连接ID',
    algorithm       VARCHAR(50) DEFAULT 'astar' COMMENT '算法类型',
    path_points     JSON NOT NULL COMMENT '路径点数组',
    waypoints       JSON COMMENT '途经点',
    obstacles       JSON COMMENT '避让的障碍物',
    total_length    DECIMAL(10, 3) NOT NULL COMMENT '总长度',
    bend_count      INT DEFAULT 0 COMMENT '弯折次数',
    cost_score      DECIMAL(10, 4) COMMENT '成本评分',
    is_optimal      BOOLEAN DEFAULT FALSE COMMENT '是否最优路径',
    calculation_time_ms INT COMMENT '计算耗时(ms)',
    version         INT DEFAULT 1 COMMENT '版本号',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_connection (connection_id),
    INDEX idx_optimal (is_optimal),
    FOREIGN KEY (connection_id) REFERENCES connections(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='路径表';
```

### 4.5 项目表 (projects)
```sql
CREATE TABLE projects (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(200) NOT NULL COMMENT '项目名称',
    description     TEXT COMMENT '项目描述',
    type            ENUM('cable_tray', 'pipeline', 'hvac') NOT NULL COMMENT '项目类型',
    status          ENUM('draft', 'active', 'completed', 'archived') DEFAULT 'draft' COMMENT '状态',
    owner_id        BIGINT UNSIGNED NOT NULL COMMENT '所有者',
    workspace_id    BIGINT UNSIGNED NOT NULL COMMENT '工作空间ID',
    settings        JSON COMMENT '项目设置',
    grid_size       DECIMAL(5, 2) DEFAULT 10.00 COMMENT '网格大小',
    bounds          JSON COMMENT '边界范围',
    thumbnail       VARCHAR(255) COMMENT '缩略图',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_owner (owner_id),
    INDEX idx_workspace (workspace_id),
    INDEX idx_status (status),
    FOREIGN KEY (owner_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='项目表';
```

### 4.6 障碍物表 (obstacles)
```sql
CREATE TABLE obstacles (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    project_id      BIGINT UNSIGNED NOT NULL COMMENT '项目ID',
    name            VARCHAR(100) COMMENT '障碍物名称',
    type            ENUM('wall', 'column', 'equipment', 'zone') NOT NULL COMMENT '类型',
    shape           ENUM('box', 'cylinder', 'polygon') NOT NULL COMMENT '形状',
    position        JSON NOT NULL COMMENT '位置坐标 {x, y, z}',
    dimensions      JSON NOT NULL COMMENT '尺寸 {width, height, depth}',
    rotation        JSON COMMENT '旋转 {x, y, z}',
    buffer_zone     DECIMAL(5, 2) DEFAULT 0 COMMENT '缓冲区域',
    is_active       BOOLEAN DEFAULT TRUE COMMENT '是否生效',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_project (project_id),
    INDEX idx_active (is_active),
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='障碍物表';
```

### 4.7 导出记录表 (exports)
```sql
CREATE TABLE exports (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    project_id      BIGINT UNSIGNED NOT NULL COMMENT '项目ID',
    user_id         BIGINT UNSIGNED NOT NULL COMMENT '用户ID',
    type            ENUM('pdf', 'svg', 'dxf', 'excel', 'json') NOT NULL COMMENT '导出类型',
    file_name       VARCHAR(255) NOT NULL COMMENT '文件名',
    file_url        VARCHAR(500) NOT NULL COMMENT '文件URL',
    file_size       BIGINT COMMENT '文件大小(字节)',
    options         JSON COMMENT '导出选项',
    status          ENUM('pending', 'processing', 'completed', 'failed') DEFAULT 'pending' COMMENT '状态',
    error_message   TEXT COMMENT '错误信息',
    completed_at    TIMESTAMP NULL COMMENT '完成时间',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_project (project_id),
    INDEX idx_user (user_id),
    INDEX idx_status (status),
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='导出记录表';
```

## 5. ER图

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│    users    │       │  projects   │       │   devices   │
├─────────────┤       ├─────────────┤       ├─────────────┤
│ id (PK)     │◄──────┤ owner_id    │◄──────┤ project_id  │
│ username    │       │ id (PK)     │       │ id (PK)     │
│ email       │       │ name        │       │ name        │
│ role        │       │ type        │       │ type        │
└─────────────┘       │ status      │       │ position_x  │
                      │ workspace_id│       │ position_y  │
                      └─────────────┘       │ position_z  │
                            │               └─────────────┘
                            │                     │
                            ▼                     │
                      ┌─────────────┐             │
                      │  obstacles  │             │
                      ├─────────────┤             │
                      │ id (PK)     │             │
                      │ project_id  │             │
                      │ type        │             │
                      │ position    │             │
                      └─────────────┘             │
                                                  │
                            ┌─────────────────────┘
                            │
                            ▼
                      ┌─────────────┐       ┌─────────────┐
                      │ connections │──────►│   routes    │
                      ├─────────────┤       ├─────────────┤
                      │ id (PK)     │       │ id (PK)     │
                      │ project_id  │       │ connection_id│
                      │ source_id   │       │ path_points │
                      │ target_id   │       │ total_length│
                      │ type        │       │ is_optimal  │
                      │ path_data   │       └─────────────┘
                      └─────────────┘             │
                            │                     │
                            ▼                     │
                      ┌─────────────┐             │
                      │   exports   │◄────────────┘
                      ├─────────────┤
                      │ id (PK)     │
                      │ project_id  │
                      │ user_id     │
                      │ type        │
                      │ file_url    │
                      └─────────────┘
```
