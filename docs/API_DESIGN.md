# API接口设计文档

## 1. API概览

- **基础URL**: `https://api.routegen.com/v1`
- **协议**: HTTPS
- **数据格式**: JSON
- **认证方式**: Bearer Token (JWT)
- **字符编码**: UTF-8

## 2. 认证与授权

### 2.1 登录
```http
POST /auth/login
```

**请求体**:
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**响应**:
```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_in": 3600,
    "user": {
      "id": "usr_123456",
      "username": "张三",
      "email": "user@example.com",
      "role": "engineer"
    }
  }
}
```

### 2.2 刷新Token
```http
POST /auth/refresh
Authorization: Bearer {refresh_token}
```

### 2.3 登出
```http
POST /auth/logout
Authorization: Bearer {access_token}
```

## 3. 用户管理 API

### 3.1 获取当前用户信息
```http
GET /users/me
Authorization: Bearer {token}
```

**响应**:
```json
{
  "code": 200,
  "data": {
    "id": "usr_123456",
    "username": "张三",
    "email": "user@example.com",
    "avatar": "https://cdn.example.com/avatars/usr_123456.jpg",
    "role": "engineer",
    "department": {
      "id": "dept_001",
      "name": "工程设计部"
    },
    "created_at": "2024-01-15T08:30:00Z",
    "last_login_at": "2024-03-20T14:22:00Z"
  }
}
```

### 3.2 更新用户信息
```http
PUT /users/me
Authorization: Bearer {token}
Content-Type: application/json

{
  "username": "张三丰",
  "avatar": "https://cdn.example.com/avatars/new.jpg"
}
```

### 3.3 获取用户列表（管理员）
```http
GET /users?page=1&limit=20&role=engineer&keyword=张
Authorization: Bearer {token}
```

**响应**:
```json
{
  "code": 200,
  "data": {
    "items": [
      {
        "id": "usr_123456",
        "username": "张三",
        "email": "user@example.com",
        "role": "engineer",
        "status": "active",
        "created_at": "2024-01-15T08:30:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 156,
      "total_pages": 8
    }
  }
}
```

## 4. 项目管理 API

### 4.1 创建项目
```http
POST /projects
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "数据中心A区布线规划",
  "description": "包含服务器机柜、网络设备间的线缆规划",
  "type": "cable_tray",
  "settings": {
    "grid_size": 10,
    "unit": "mm",
    "bounds": {
      "min_x": 0,
      "min_y": 0,
      "max_x": 5000,
      "max_y": 3000
    }
  }
}
```

**响应**:
```json
{
  "code": 201,
  "message": "项目创建成功",
  "data": {
    "id": "proj_789012",
    "name": "数据中心A区布线规划",
    "type": "cable_tray",
    "status": "draft",
    "owner_id": "usr_123456",
    "created_at": "2024-03-20T15:30:00Z",
    "updated_at": "2024-03-20T15:30:00Z"
  }
}
```

### 4.2 获取项目列表
```http
GET /projects?page=1&limit=10&status=active&type=cable_tray
Authorization: Bearer {token}
```

### 4.3 获取项目详情
```http
GET /projects/{project_id}
Authorization: Bearer {token}
```

**响应**:
```json
{
  "code": 200,
  "data": {
    "id": "proj_789012",
    "name": "数据中心A区布线规划",
    "description": "包含服务器机柜、网络设备间的线缆规划",
    "type": "cable_tray",
    "status": "active",
    "owner": {
      "id": "usr_123456",
      "username": "张三"
    },
    "settings": {
      "grid_size": 10,
      "unit": "mm",
      "bounds": {
        "min_x": 0,
        "min_y": 0,
        "max_x": 5000,
        "max_y": 3000
      }
    },
    "stats": {
      "device_count": 45,
      "connection_count": 128,
      "total_length": 2560.5
    },
    "created_at": "2024-03-20T15:30:00Z",
    "updated_at": "2024-03-21T09:15:00Z"
  }
}
```

### 4.4 更新项目
```http
PUT /projects/{project_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "数据中心A区布线规划_v2",
  "description": "更新描述",
  "settings": {
    "grid_size": 5
  }
}
```

### 4.5 删除项目
```http
DELETE /projects/{project_id}
Authorization: Bearer {token}
```

### 4.6 复制项目
```http
POST /projects/{project_id}/clone
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "数据中心A区布线规划_副本",
  "include_routes": true
}
```

## 5. 设备管理 API

### 5.1 创建设备
```http
POST /projects/{project_id}/devices
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "服务器机柜-01",
  "type": "server_rack",
  "model": "RACK-42U-1000",
  "position": {
    "x": 500,
    "y": 300,
    "z": 0
  },
  "dimensions": {
    "width": 600,
    "height": 2000,
    "depth": 1000
  },
  "rotation": 0,
  "properties": {
    "power_rating": "3000W",
    "port_count": 48
  }
}
```

**响应**:
```json
{
  "code": 201,
  "message": "设备创建成功",
  "data": {
    "id": "dev_345678",
    "name": "服务器机柜-01",
    "type": "server_rack",
    "position": {
      "x": 500,
      "y": 300,
      "z": 0
    },
    "created_at": "2024-03-20T16:00:00Z"
  }
}
```

### 5.2 批量创建设备
```http
POST /projects/{project_id}/devices/batch
Authorization: Bearer {token}
Content-Type: application/json

{
  "devices": [
    {
      "name": "服务器机柜-02",
      "type": "server_rack",
      "position": {"x": 1200, "y": 300, "z": 0},
      "dimensions": {"width": 600, "height": 2000, "depth": 1000}
    },
    {
      "name": "服务器机柜-03",
      "type": "server_rack",
      "position": {"x": 1900, "y": 300, "z": 0},
      "dimensions": {"width": 600, "height": 2000, "depth": 1000}
    }
  ]
}
```

### 5.3 获取设备列表
```http
GET /projects/{project_id}/devices?type=server_rack&page=1&limit=50
Authorization: Bearer {token}
```

### 5.4 获取设备详情
```http
GET /projects/{project_id}/devices/{device_id}
Authorization: Bearer {token}
```

### 5.5 更新设备
```http
PUT /projects/{project_id}/devices/{device_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "服务器机柜-01-重命名",
  "position": {
    "x": 550,
    "y": 350
  }
}
```

### 5.6 删除设备
```http
DELETE /projects/{project_id}/devices/{device_id}
Authorization: Bearer {token}
```

### 5.7 导入设备（从Excel/CSV）
```http
POST /projects/{project_id}/devices/import
Authorization: Bearer {token}
Content-Type: multipart/form-data

file: [二进制文件]
format: "excel"  # 或 "csv"
```

## 6. 连接管理 API

### 6.1 创建连接
```http
POST /projects/{project_id}/connections
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "机柜01-02连接",
  "source_device_id": "dev_345678",
  "target_device_id": "dev_345679",
  "source_port": "Port-01",
  "target_port": "Port-01",
  "type": "cable",
  "priority": 5,
  "constraints": {
    "max_length": 5000,
    "min_bend_radius": 50,
    "avoid_zones": []
  }
}
```

**响应**:
```json
{
  "code": 201,
  "message": "连接创建成功",
  "data": {
    "id": "conn_567890",
    "name": "机柜01-02连接",
    "source_device_id": "dev_345678",
    "target_device_id": "dev_345679",
    "type": "cable",
    "status": "planned",
    "created_at": "2024-03-20T16:30:00Z"
  }
}
```

### 6.2 获取连接列表
```http
GET /projects/{project_id}/connections?status=planned&type=cable
Authorization: Bearer {token}
```

### 6.3 获取连接详情
```http
GET /projects/{project_id}/connections/{connection_id}
Authorization: Bearer {token}
```

**响应**:
```json
{
  "code": 200,
  "data": {
    "id": "conn_567890",
    "name": "机柜01-02连接",
    "source_device": {
      "id": "dev_345678",
      "name": "服务器机柜-01"
    },
    "target_device": {
      "id": "dev_345679",
      "name": "服务器机柜-02"
    },
    "type": "cable",
    "status": "routed",
    "priority": 5,
    "constraints": {
      "max_length": 5000,
      "min_bend_radius": 50
    },
    "route": {
      "id": "route_123",
      "path_points": [
        {"x": 800, "y": 300, "z": 0},
        {"x": 1000, "y": 300, "z": 0},
        {"x": 1000, "y": 500, "z": 0},
        {"x": 1200, "y": 500, "z": 0}
      ],
      "total_length": 450.5,
      "bend_count": 2,
      "is_optimal": true
    },
    "created_at": "2024-03-20T16:30:00Z"
  }
}
```

### 6.4 更新连接
```http
PUT /projects/{project_id}/connections/{connection_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "机柜01-02连接-重命名",
  "priority": 8,
  "constraints": {
    "max_length": 3000
  }
}
```

### 6.5 删除连接
```http
DELETE /projects/{project_id}/connections/{connection_id}
Authorization: Bearer {token}
```

## 7. 路径计算 API

### 7.1 计算单条路径
```http
POST /projects/{project_id}/connections/{connection_id}/calculate-route
Authorization: Bearer {token}
Content-Type: application/json

{
  "algorithm": "astar",
  "constraints": {
    "max_length": 5000,
    "weight_factors": {
      "length": 1.0,
      "bends": 0.5
    }
  },
  "waypoints": [
    {"x": 1000, "y": 400, "z": 0}
  ]
}
```

**响应**:
```json
{
  "code": 200,
  "message": "路径计算成功",
  "data": {
    "route_id": "route_123",
    "connection_id": "conn_567890",
    "algorithm": "astar",
    "path_points": [
      {"x": 800, "y": 300, "z": 0},
      {"x": 1000, "y": 300, "z": 0},
      {"x": 1000, "y": 500, "z": 0},
      {"x": 1200, "y": 500, "z": 0}
    ],
    "total_length": 450.5,
    "bend_count": 2,
    "bend_points": [
      {"x": 1000, "y": 300, "z": 0},
      {"x": 1000, "y": 500, "z": 0}
    ],
    "calculation_time_ms": 45.2,
    "is_optimal": true,
    "cost_breakdown": {
      "length_cost": 450.5,
      "bend_cost": 100.0,
      "total_cost": 550.5
    }
  }
}
```

### 7.2 批量计算路径
```http
POST /projects/{project_id}/calculate-routes
Authorization: Bearer {token}
Content-Type: application/json

{
  "connection_ids": ["conn_567890", "conn_567891", "conn_567892"],
  "algorithm": "astar",
  "parallel": true,
  "constraints": {
    "avoid_crossing": true,
    "max_length": 10000
  }
}
```

**响应**:
```json
{
  "code": 200,
  "message": "批量路径计算完成",
  "data": {
    "results": [
      {
        "connection_id": "conn_567890",
        "status": "success",
        "route": {
          "route_id": "route_123",
          "total_length": 450.5,
          "bend_count": 2
        }
      },
      {
        "connection_id": "conn_567891",
        "status": "success",
        "route": {
          "route_id": "route_124",
          "total_length": 320.0,
          "bend_count": 1
        }
      },
      {
        "connection_id": "conn_567892",
        "status": "failed",
        "error": "无法找到有效路径，请检查障碍物设置"
      }
    ],
    "summary": {
      "total": 3,
      "success": 2,
      "failed": 1,
      "total_calculation_time_ms": 128.5
    }
  }
}
```

### 7.3 重新计算路径
```http
POST /projects/{project_id}/connections/{connection_id}/recalculate-route
Authorization: Bearer {token}
Content-Type: application/json

{
  "algorithm": "astar",
  "constraints": {
    "prefer_straight": true
  }
}
```

### 7.4 获取路径历史
```http
GET /projects/{project_id}/connections/{connection_id}/route-history
Authorization: Bearer {token}
```

## 8. 障碍物管理 API

### 8.1 创建障碍物
```http
POST /projects/{project_id}/obstacles
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "承重柱-A1",
  "type": "column",
  "shape": "box",
  "position": {
    "x": 1500,
    "y": 1000,
    "z": 0
  },
  "dimensions": {
    "width": 400,
    "height": 400,
    "depth": 3000
  },
  "buffer_zone": 50,
  "is_active": true
}
```

### 8.2 获取障碍物列表
```http
GET /projects/{project_id}/obstacles?is_active=true
Authorization: Bearer {token}
```

### 8.3 更新障碍物
```http
PUT /projects/{project_id}/obstacles/{obstacle_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "buffer_zone": 100,
  "is_active": false
}
```

### 8.4 删除障碍物
```http
DELETE /projects/{project_id}/obstacles/{obstacle_id}
Authorization: Bearer {token}
```

## 9. 导出 API

### 9.1 创建导出任务
```http
POST /projects/{project_id}/exports
Authorization: Bearer {token}
Content-Type: application/json

{
  "format": "pdf",
  "options": {
    "page_size": "A3",
    "orientation": "landscape",
    "include_title": true,
    "include_legend": true,
    "include_table": true,
    "title": "数据中心A区布线规划图",
    "company_name": "XX科技有限公司"
  },
  "connection_ids": ["conn_567890", "conn_567891"],  # 可选，导出指定连接
  "notify_email": true
}
```

**响应**:
```json
{
  "code": 202,
  "message": "导出任务已创建",
  "data": {
    "export_id": "exp_987654",
    "project_id": "proj_789012",
    "format": "pdf",
    "status": "pending",
    "created_at": "2024-03-20T17:00:00Z",
    "estimated_completion": "2024-03-20T17:00:10Z"
  }
}
```

### 9.2 获取导出任务状态
```http
GET /exports/{export_id}
Authorization: Bearer {token}
```

**响应**:
```json
{
  "code": 200,
  "data": {
    "export_id": "exp_987654",
    "project_id": "proj_789012",
    "format": "pdf",
    "status": "completed",  # pending, processing, completed, failed
    "file_name": "route_export_20240320_170000.pdf",
    "file_url": "https://cdn.example.com/exports/exp_987654.pdf",
    "file_size": 2457600,
    "completed_at": "2024-03-20T17:00:08Z",
    "created_at": "2024-03-20T17:00:00Z"
  }
}
```

### 9.3 批量导出
```http
POST /projects/{project_id}/exports/batch
Authorization: Bearer {token}
Content-Type: application/json

{
  "formats": ["pdf", "svg", "excel"],
  "options": {
    "page_size": "A4",
    "orientation": "landscape"
  }
}
```

### 9.4 获取导出历史
```http
GET /projects/{project_id}/exports?page=1&limit=10
Authorization: Bearer {token}
```

### 9.5 下载导出文件
```http
GET /exports/{export_id}/download
Authorization: Bearer {token}
```

返回二进制文件流。

## 10. 协作 API

### 10.1 获取项目成员
```http
GET /projects/{project_id}/members
Authorization: Bearer {token}
```

### 10.2 添加项目成员
```http
POST /projects/{project_id}/members
Authorization: Bearer {token}
Content-Type: application/json

{
  "user_id": "usr_789012",
  "role": "editor",  # owner, editor, viewer
  "permissions": ["read", "write", "delete"]
}
```

### 10.3 更新成员权限
```http
PUT /projects/{project_id}/members/{user_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "role": "viewer",
  "permissions": ["read"]
}
```

### 10.4 移除项目成员
```http
DELETE /projects/{project_id}/members/{user_id}
Authorization: Bearer {token}
```

### 10.5 WebSocket实时协作
```
wss://api.routegen.com/v1/ws/projects/{project_id}
Authorization: Bearer {token}
```

**消息格式**:
```json
{
  "type": "cursor_move",
  "user_id": "usr_123456",
  "data": {
    "x": 500,
    "y": 300
  },
  "timestamp": "2024-03-20T17:05:00Z"
}
```

消息类型:
- `cursor_move`: 光标移动
- `element_select`: 元素选中
- `element_update`: 元素更新
- `element_create`: 元素创建
- `element_delete`: 元素删除
- `user_join`: 用户加入
- `user_leave`: 用户离开

## 11. 系统 API

### 11.1 获取系统状态
```http
GET /system/health
```

**响应**:
```json
{
  "code": 200,
  "data": {
    "status": "healthy",
    "version": "1.2.3",
    "timestamp": "2024-03-20T17:10:00Z",
    "services": {
      "api": "up",
      "database": "up",
      "redis": "up",
      "algorithm_engine": "up"
    }
  }
}
```

### 11.2 获取服务器时间
```http
GET /system/time
```

### 11.3 获取API版本
```http
GET /system/version
```

## 12. 错误处理

### 12.1 错误响应格式
```json
{
  "code": 400,
  "message": "请求参数错误",
  "errors": [
    {
      "field": "email",
      "message": "邮箱格式不正确"
    }
  ],
  "request_id": "req_abc123xyz",
  "timestamp": "2024-03-20T17:15:00Z"
}
```

### 12.2 错误码表

| 状态码 | 错误码 | 说明 |
|--------|--------|------|
| 400 | BAD_REQUEST | 请求参数错误 |
| 401 | UNAUTHORIZED | 未授权 |
| 403 | FORBIDDEN | 禁止访问 |
| 404 | NOT_FOUND | 资源不存在 |
| 409 | CONFLICT | 资源冲突 |
| 422 | VALIDATION_ERROR | 验证错误 |
| 429 | RATE_LIMITED | 请求过于频繁 |
| 500 | INTERNAL_ERROR | 服务器内部错误 |
| 503 | SERVICE_UNAVAILABLE | 服务不可用 |

## 13. 分页与过滤

### 13.1 分页参数
- `page`: 页码（从1开始）
- `limit`: 每页数量（默认20，最大100）

### 13.2 响应格式
```json
{
  "code": 200,
  "data": {
    "items": [...],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 156,
      "total_pages": 8,
      "has_next": true,
      "has_prev": false
    }
  }
}
```

### 13.3 过滤参数
- `sort`: 排序字段（如 `-created_at` 表示按创建时间倒序）
- `fields`: 返回字段（如 `id,name,status`）
- 其他字段根据API具体支持

## 14. 限流策略

| 接口类型 | 限制 |
|----------|------|
| 认证接口 | 5次/分钟 |
| 普通API | 1000次/分钟 |
| 路径计算 | 100次/分钟 |
| 批量计算 | 10次/分钟 |
| 导出任务 | 10次/小时 |

限流响应:
```json
{
  "code": 429,
  "message": "请求过于频繁，请稍后再试",
  "retry_after": 60
}
```
