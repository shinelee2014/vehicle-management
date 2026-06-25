# 厂区车辆进出管理系统 · 架构图

## 1. 部署架构（生产环境）

```
                    ┌─────────────────────────────┐
                    │   用户浏览器/手机            │
                    │   - Chrome/Edge/Safari       │
                    │   - 微信内置浏览器            │
                    │   - Android WebView          │
                    └──────────┬──────────────────┘
                               │ HTTP/HTTPS
                               │ (Port 8080)
                               ▼
        ┌──────────────────────────────────────────────┐
        │           Synology NAS DS1621+              │
        │           192.168.6.12 (内网)                │
        │                                              │
        │  ┌──────────────────────────────────────┐   │
        │  │   vehicle-frontend (nginx:alpine)    │   │
        │  │   - Port 8080 → 80                   │   │
        │  │   - SPA 静态文件                      │   │
        │  │   - 反向代理: /api/* → backend:8000  │   │
        │  │   - 反向代理: /photos/* → backend    │   │
        │  │   - no-cache: /, /index.html         │   │
        │  └────────┬─────────────────────────────┘   │
        │           │                                    │
        │  ┌────────▼─────────────────────────────┐   │
        │  │   vehicle-backend (python:3.11-slim) │   │
        │  │   - Port 8000                         │   │
        │  │   - 2 workers                         │   │
        │  │   - FastAPI + uvicorn                 │   │
        │  │   - Pillow (水印) + APScheduler        │   │
        │  │   - Noto CJK 字体                     │   │
        │  └────┬─────────────────────┬──────────┘   │
        │       │                     │               │
        │  ┌────▼──────────┐   ┌──────▼─────────┐     │
        │  │ vehicle-db    │   │  /photos 卷    │     │
        │  │ MariaDB 10.11 │   │  docker volume │     │
        │  │ Port 3306     │   │  (持久化)       │     │
        │  │ Volume:       │   └────────────────┘     │
        │  │ db_data       │                            │
        │  └───────────────┘                            │
        │                                               │
        │  容器网络: vehicle-net (bridge)                │
        └──────────────────────────────────────────────┘
                               │
                               │ (Hyper Backup 备份)
                               ▼
        ┌──────────────────────────────────────────────┐
        │           外接备份 (Hyper Backup)             │
        │   - /volume1/@docker/volumes/                  │
        │     - vehicle-management_db_data/             │
        │     - vehicle-management_photos_data/          │
        │   - /volume1/docker/vehicle-management/        │
        │     (源码 + 配置)                              │
        └──────────────────────────────────────────────┘
```

---

## 2. 应用架构（逻辑分层）

```
┌─────────────────────────────────────────────────────────┐
│                    前端 (Vue 3 SPA)                       │
│  ┌────────────────────────────────────────────────────┐ │
│  │  视图层 (Views)                                     │ │
│  │   - Login / Dashboard / RecordIn / RecordOut       │ │
│  │   - RecordList / Approval / Reports / Messages      │ │
│  │   - Profile / AdminUsers / AdminPosts / Configs     │ │
│  │   - AdminRoleModules                                 │ │
│  └────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────┐ │
│  │  组件层 (Components)                                │ │
│  │   - Layout (动态菜单)                               │ │
│  │   - CustomModule (占位页)                           │ │
│  └────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────┐ │
│  │  状态层 (Pinia stores)                              │ │
│  │   - auth (token, user, visibleModules)              │ │
│  └────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────┐ │
│  │  API 层 (Axios + 拦截器)                            │ │
│  │   - request.js (统一 baseURL / token / 错误处理)     │ │
│  │   - auth.js / records.js / users.js / posts.js ...  │ │
│  └────────────────────────────────────────────────────┘ │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTPS (内网 HTTP)
                       ▼
┌─────────────────────────────────────────────────────────┐
│                  后端 (FastAPI)                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │  API 路由层 (app/api/)                              │ │
│  │   - auth (login/logout/me/password)                 │ │
│  │   - users / posts / records / files                  │ │
│  │   - messages / dashboard / reports                  │ │
│  │   - role_modules / modules                          │ │
│  │   - approvers / configs / audit_logs                 │ │
│  └────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────┐ │
│  │  中间件层                                            │ │
│  │   - CORS (CORSMiddleware)                           │ │
│  │   - JWT 鉴权 (HTTPBearer)                            │ │
│  │   - 全局错误处理 (RequestValidationError → 422)      │ │
│  └────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────┐ │
│  │  服务层 (app/services/)                              │ │
│  │   - bootstrap (启动初始化)                           │ │
│  │   - scheduler (APScheduler)                         │ │
│  │   - audit (审计日志)                                │ │
│  │   - approval_timeout (超时审批)                      │ │
│  │   - report (报表)                                   │ │
│  │   - archive (归档)                                  │ │
│  └────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────┐ │
│  │  数据层 (app/models/ + app/database.py)              │ │
│  │   - User / Post / Record / Message                   │ │
│  │   - SystemConfig / ReportConfig / AuditLog           │ │
│  │   - RoleModule / Module                              │ │
│  │   - SQLAlchemy 2.0 ORM                               │ │
│  └────────────────────────────────────────────────────┘ │
└──────────────────────┬──────────────────────────────────┘
                       │ TCP 3306
                       ▼
┌─────────────────────────────────────────────────────────┐
│                  数据库 (MariaDB 10.11)                   │
│  - utf8mb4 字符集                                          │
│  - 9 张核心表 + 2 张权限表                                 │
│  - 视图: 无（直接查表）                                    │
│  - 存储过程: 无                                            │
│  - 触发器: 无（业务逻辑全在应用层）                          │
└─────────────────────────────────────────────────────────┘
```

---

## 3. 数据流图（核心场景）

### 3.1 进场登记数据流

```
[保安浏览器]                 [前端]                  [后端 API]              [数据库]
     │                         │                          │                     │
     │ 1. 打开进场登记          │                          │                     │
     │─────────────────────────>                          │                     │
     │                         │ 2. 加载岗亭列表          │                     │
     │                         │ GET /posts               │                     │
     │                         │──────────────────────────>                     │
     │                         │                          │ 3. SELECT posts    │
     │                         │                          │────────────────────>│
     │                         │                          │<────────────────────│
     │                         │<──────────────────────────│                     │
     │                         │                          │                     │
     │                         │ 4. 加载审批人列表         │                     │
     │                         │ GET /approvers            │                     │
     │                         │──────────────────────────>                     │
     │                         │                          │ 5. SELECT users    │
     │                         │                          │   WHERE is_approver│
     │                         │                          │────────────────────>│
     │                         │                          │<────────────────────│
     │                         │<──────────────────────────│                     │
     │                         │                          │                     │
     │ 6. 选岗亭/输车牌/...     │                          │                     │
     │─────────────────────────>                          │                     │
     │                         │                          │                     │
     │ 7. 点拍照 → 手机相机     │                          │                     │
     │<─────── 相机 ──────────>│                          │                     │
     │                         │                          │                     │
     │ 8. 点上传照片            │                          │                     │
     │                         │ 9. POST /files/photo     │                     │
     │                         │  FormData {file, post_id}│                     │
     │                         │──────────────────────────>                     │
     │                         │                          │ 10. 校验类型/大小   │
     │                         │                          │ 11. 加水印         │
     │                         │                          │ 12. 保存到 /photos │
     │                         │                          │────────────────────>│
     │                         │                          │<────────────────────│
     │                         │                          │ 13. 返回 url      │
     │                         │<──────────────────────────│                     │
     │<────────────────────────│  {url: "/photos/..."}    │                     │
     │                         │                          │                     │
     │ 14. 点提交              │                          │                     │
     │                         │ 15. POST /records/in     │                     │
     │                         │   {plate, type, photos}  │                     │
     │                         │──────────────────────────>                     │
     │                         │                          │ 16. INSERT records │
     │                         │                          │────────────────────>│
     │                         │                          │ 17. INSERT message │
     │                         │                          │   (给审批人)       │
     │                         │                          │────────────────────>│
     │                         │                          │ 18. INSERT audit_log│
     │                         │                          │────────────────────>│
     │                         │                          │ 19. COMMIT         │
     │                         │<──────────────────────────│                     │
     │<────────────────────────│                          │                     │
     │ 20. 跳到详情页           │                          │                     │
```

### 3.2 审批数据流

```
[审批人浏览器]               [前端]                  [后端 API]              [数据库]
     │                         │                          │                     │
     │ 1. 打开「待我审批」      │                          │                     │
     │─────────────────────────>                          │                     │
     │                         │ 2. GET /records/pending  │                     │
     │                         │──────────────────────────>                     │
     │                         │                          │ 3. SELECT records  │
     │                         │                          │   WHERE approver_id│
     │                         │                          │   AND status=pending│
     │                         │                          │────────────────────>│
     │                         │                          │<────────────────────│
     │                         │<──────────────────────────│                     │
     │<────────────────────────│  [{id, plate, ...}]     │                     │
     │                         │                          │                     │
     │ 4. 看详情, 点通过       │                          │                     │
     │─────────────────────────>                          │                     │
     │                         │ 5. POST /records/{id}/approve│                 │
     │                         │   {remark: "OK"}         │                     │
     │                         │──────────────────────────>                     │
     │                         │                          │ 6. UPDATE records  │
     │                         │                          │   SET approval_status│
     │                         │                          │   = 'approved'    │
     │                         │                          │────────────────────>│
     │                         │                          │ 7. INSERT message  │
     │                         │                          │   (给保安)         │
     │                         │                          │────────────────────>│
     │                         │                          │ 8. INSERT audit_log│
     │                         │                          │────────────────────>│
     │                         │                          │ 9. COMMIT          │
     │                         │<──────────────────────────│                     │
     │<────────────────────────│  {code: 0, msg: "已通过"} │                     │
```

---

## 4. 数据库 ER 图

```
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│    users     │       │    posts     │       │   records    │
├──────────────┤       ├──────────────┤       ├──────────────┤
│ id (PK)      │       │ id (PK)      │       │ id (PK)      │
│ username     │       │ name         │       │ record_no    │
│ password_hash│       │ code         │       │ plate_number │
│ real_name    │       │ location     │       │ vehicle_type │
│ role         │◄──────│ is_active    │       │ direction    │
│ post_id (FK) │       │ created_at   │       │ post_id (FK) │
│ is_approver  │       └──────────────┘       │ operator_id  │
│ phone/email  │                              │ in_time      │
│ is_active    │       ┌──────────────┐       │ in_photos    │
└──────┬───────┘       │   messages   │       │ out_time     │
       │               ├──────────────┤       │ out_photos   │
       │               │ id (PK)      │       │ cargo_info   │
       │               │ recipient_id │       │ approver_id  │
       │               │ sender_id    │       │ approval_*   │
       │               │ type         │       │ related_*    │
       │               │ title        │       │ status       │
       │               │ content      │       │ created_at   │
       │               │ is_read      │       │ is_deleted   │
       │               │ related_id   │       │ deleted_*    │
       │               └──────────────┘       └──────────────┘
       │                       ▲                       ▲
       │                       │                       │
       │               ┌───────┴──────────┐    ┌────────┴─────────┐
       │               │   audit_logs     │    │   role_modules   │
       │               ├──────────────────┤    ├──────────────────┤
       └──────────────>│ user_id          │    │ role             │
                       │ username         │    │ modules (JSON)   │
                       │ action           │    │ created_at       │
                       │ target_type      │    └──────────────────┘
                       │ target_id        │
                       │ details (JSON)   │    ┌──────────────────┐
                       │ ip_address       │    │    modules       │
                       │ status           │    ├──────────────────┤
                       │ error_message    │    │ id (PK)          │
                       │ created_at       │    │ code (unique)    │
                       └──────────────────┘    │ name             │
                                                │ path             │
                                                │ icon             │
                                                │ category         │
                                                │ sort_order       │
                                                │ is_builtin       │
                                                │ is_active        │
                                                └──────────────────┘
```

**外键关系**：

- `records.post_id → posts.id`（岗亭）
- `records.operator_id → users.id`（操作人）
- `records.approver_id → users.id`（审批人）
- `records.related_record_id → records.id`（进记录关联出记录）
- `records.companion_id → records.id`（反向）
- `messages.recipient_id / sender_id → users.id`
- `messages.related_record_id → records.id`

---

## 5. 安全架构

### 5.1 认证

```
[浏览器]              [nginx]              [FastAPI]
   │                     │                     │
   │ POST /auth/login     │                     │
   │ {username, pwd}     │                     │
   │────────────────────>│                     │
   │                     │ proxy_pass          │
   │                     │────────────────────>│
   │                     │                     │ 验证 bcrypt
   │                     │                     │ 生成 JWT
   │                     │<────────────────────│
   │<────────────────────│  {access_token}   │
   │                     │                     │
   │ 后续请求:           │                     │
   │ Authorization:      │                     │
   │ Bearer <token>      │                     │
   │────────────────────>│                     │
   │                     │────────────────────>│
   │                     │                     │ decode JWT
   │                     │                     │ 查 user (active)
   │                     │                     │ 注入 current_user
   │                     │<────────────────────│
```

### 5.2 权限层级

```
┌─────────────────────────────────────────────┐
│ Layer 1: 路由守卫                            │
│   - 检查 token 是否有效                       │
│   - 检查路由 meta.module 是否在用户可见模块   │
└─────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────┐
│ Layer 2: API 依赖 get_current_user           │
│   - JWT decode → user 对象                   │
└─────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────┐
│ Layer 3: 业务层权限检查                       │
│   - if current_user.role != 'admin': 403     │
│   - security 角色只看自己的 records           │
│   - supervisor/admin 看全部                  │
└─────────────────────────────────────────────┘
```

### 5.3 数据安全

| 措施 | 说明 |
|---|---|
| 密码哈希 | bcrypt (passlib) + 12 rounds |
| JWT 签名 | HS256 + JWT_SECRET（环境变量配置） |
| JWT 过期 | 8 小时 |
| 软删除 | records.is_deleted 标记 + 审计快照 |
| 审计 | 所有写操作记 audit_logs（含 IP + 操作人 + 详情 JSON） |
| CORS | 默认仅内网访问，nginx 不暴露到公网 |
| 输入校验 | Pydantic schema + Literal 限制取值 |

---

## 6. 部署架构清单

### 6.1 服务清单

| 服务 | 镜像 | 资源占用（峰值） | 端口 |
|---|---|---|---|
| vehicle-frontend | nginx:alpine + 自定义 dist | CPU 5% / RAM 20MB | 8080→80 |
| vehicle-backend | python:3.11-slim + 自定义 | CPU 30% / RAM 400MB | 8000 |
| vehicle-db | mariadb:10.11 | CPU 10% / RAM 250MB | 3306 |

**NAS 总占用**：CPU 45% / RAM 670MB / Disk 5-10GB（照片） + 50MB（DB）

### 6.2 数据持久化

| 卷 | 内容 | 备份策略 |
|---|---|---|
| vehicle-management_db_data | MariaDB 数据 | Hyper Backup 每天 |
| vehicle-management_photos_data | /photos 照片 | Hyper Backup 每天 |
| /volume1/docker/vehicle-management | 源码 + 配置 | git 仓库 + Hyper Backup |

---

## 7. 性能与扩展性

### 7.1 当前瓶颈

- 单 backend 节点 → 上限约 100 并发请求
- 单 db 节点 → 上限约 50 QPS
- 文件存储 → NAS 内部 IOPS ~5000

### 7.2 容量预估

| 指标 | 当前 | 1 年后预估 | 极限 |
|---|---|---|---|
| 记录数 | ~10 条（测试） | ~30,000 条/年 | 100 万条无压力 |
| 照片数 | ~15 张 | ~30,000 张/年 | MariaDB + 文件系统都能撑 |
| 用户数 | 6 个 | ~50 个 | 无明显瓶颈 |
| 日活 | 1 人（测试） | ~10 人 | 单机够用 |

### 7.3 扩展路径

**v1.1 - 横向扩展**：
- backend 加 1 个副本 + nginx 负载均衡
- MariaDB 改主从（NAS 资源够）

**v2.0 - 微服务**：
- 认证服务独立
- 报表服务独立（用 ClickHouse）
- 文件服务用 MinIO
