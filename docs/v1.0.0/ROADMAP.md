# 厂区车辆进出管理系统 · 技术开发路线图

**版本**：v1.0.0  
**总开发周期**：约 2 周（2026-06 中旬 ~ 2026-06-25）  
**开发模式**：单人 + AI 辅助编程（vibe coding）

---

## 总览（甘特图式）

```
Day  1  ████████████ 基础设施 + 部署
Day  2  ████████████ 数据模型 + 认证
Day  3  ████████████ 核心 API（进出 + 审批 + 文件）
Day  4  ████████████ 核心前端（5 个业务页）
Day  5  ████████████ 照片水印 + 报表 + 定时任务
Day  6  ████████████ Bug 修复轮（CORS/Enum/照片 404）
Day  7  ████████████ 角色权限系统 + 自定义模块
Day  8  ████████████ 删除/恢复功能 + 文档整理
```

---

## 阶段 1：基础设施（Day 1）

### 1.1 选型决策

| 决策点 | 选项 | 最终选 | 理由 |
|---|---|---|---|
| 前端框架 | Vue 2 / Vue 3 / React | **Vue 3 + Composition API** | 学习曲线好，AI 辅助生成代码方便 |
| 后端框架 | Django / Flask / FastAPI / Spring Boot | **FastAPI** | Python 类型提示、自动 OpenAPI、性能好 |
| 数据库 | MySQL / MariaDB / PostgreSQL | **MariaDB 10.11** | NAS DSM 自带镜像 |
| 部署 | Docker Compose / K8s | **Docker Compose** | 单机部署，3 个服务够用 |
| 反向代理 | nginx / Traefik / Caddy | **nginx (alpine)** | 简单可靠 |
| 包管理 | npm / yarn / pnpm | **npm** | 标配 |
| 镜像源 | 官方 / 阿里云 | **阿里云（前端 npm）+ 官方（Docker Hub）** | 国内快 |

### 1.2 目录结构

```
vehicle-management/
├── backend/                 # FastAPI
│   ├── app/
│   │   ├── api/            # 路由
│   │   ├── core/           # 安全/权限
│   │   ├── models/         # ORM
│   │   ├── schemas/        # Pydantic
│   │   ├── services/       # 业务逻辑
│   │   ├── utils/          # 工具（水印）
│   │   ├── config.py       # 配置
│   │   └── database.py     # DB 连接
│   ├── Dockerfile
│   ├── requirements.txt
│   └── main.py
├── frontend/               # Vue 3
│   ├── src/
│   │   ├── api/           # 接口封装
│   │   ├── components/    # 公共组件
│   │   ├── router/
│   │   ├── stores/        # Pinia
│   │   ├── views/         # 页面
│   │   ├── utils/
│   │   ├── App.vue
│   │   └── main.js
│   ├── index.html
│   ├── vite.config.js
│   ├── nginx.conf         # 反代 + SPA fallback
│   ├── Dockerfile
│   └── package.json
├── deploy/
│   └── init.sql           # 数据库建表
├── docker-compose.yml
├── .env.example
└── docs/
    ├── v1.0.0/            # 当前版本文档
    └── VERSIONING.md
```

### 1.3 docker-compose.yml 关键设计

```yaml
services:
  db:
    image: mariadb:10.11
    volumes:
      - db_data:/var/lib/mysql
      - ./deploy/init.sql:/docker-entrypoint-initdb.d/init.sql:ro

  backend:
    build: ./backend
    environment:
      - PHOTO_BASE_DIR=/photos  # 容器内照片路径
    volumes:
      - photos_data:/photos      # docker volume 持久化

  frontend:
    build:
      context: ./frontend
      args:
        VITE_API_BASE: /api
    ports:
      - "8080:80"               # 用户访问入口
```

**关键决策**：
- `db` 容器用 `healthcheck` 保证 backend 启动时 db 已就绪
- backend 通过 `depends_on: condition: service_healthy` 等待 db
- 照片用 docker volume 而不是 bind mount，方便备份和迁移

---

## 阶段 2：数据模型 + 认证（Day 1-2）

### 2.1 关键模型

```python
# User
- id, username, password_hash, real_name
- role (security/supervisor/approver/admin)
- post_id (岗亭关联)
- is_approver (bool, 早期用，后面独立成 approver 角色)
- phone, email, is_active, last_login_at, created_at, updated_at

# Post (岗亭)
- id, name, code, location, is_active, ...

# Record (进出记录)
- id, record_no (IN-20260625-00001)
- plate_number, vehicle_type, direction (in/out)
- post_id, operator_id, operator_name
- in_time, in_photos (JSON), in_remark
- out_time, out_photos, out_remark
- cargo_info (货车专用)
- loading_start_at, loading_end_at, loading_duration
- approver_id, approval_status (pending/approved/rejected/timeout)
- related_record_id, companion_id (进出配对)
- status (in_pending/in_approved/...)
- archived_at (1 年后归档)

# Message (站内信)
- recipient_id, sender_id, type (system/approval_request/approval_result)
- title, content, related_record_id, is_read, read_at

# AuditLog (审计)
- user_id, username, action, target_type, target_id
- details (JSON), ip_address, status, error_message
```

### 2.2 数据库建表

`deploy/init.sql` 写完整建表 SQL（用 MySQL ENUM 类型存储固定值）。

> **后续教训**：MySQL ENUM 类型与 Python enum 成员名映射容易冲突，详见阶段 6。

### 2.3 认证流程

```
POST /api/v1/auth/login {username, password}
   │
   ├── 验证密码 (bcrypt)
   ├── 生成 JWT (HS256, 8 小时过期)
   ├── payload: {user_id, username, role}
   └── 返回 {access_token, user}

后续请求：
Authorization: Bearer <token>
   │
   ▼
get_current_user() 依赖
   │
   ├── decode JWT
   ├── 查 user 表（status=active）
   └── 注入到路由函数
```

### 2.4 路由级权限

```python
# users.py
@router.post("/")
async def create_user(...):
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(status_code=403, ...)
```

早期只用 role 判断，后期演变成「role + 模块可见性」双重判断（见阶段 7）。

---

## 阶段 3：核心 API（Day 2-3）

### 3.1 路由结构

```
/api/v1/
├── auth/         # 登录/登出/me/改密
├── users/        # 用户管理 (admin)
├── posts/        # 岗亭管理 (admin)
├── records/      # 进出记录核心
│   ├── POST /in         # 进场登记
│   ├── POST /out        # 出场登记
│   ├── POST /{id}/approve
│   ├── POST /{id}/reject
│   ├── GET  /           # 列表
│   ├── GET  /pending    # 待我审批
│   ├── GET  /{id}       # 详情
│   ├── GET  /export/excel
│   └── GET  /unbilled-list
├── files/        # 文件上传
│   └── POST /photo      # 拍照 + 水印
├── messages/     # 站内信
├── dashboard/    # 仪表盘
├── approvers/    # 审批人列表（保安填表用）
├── reports/      # 报表
└── system/       # 系统配置
```

### 3.2 记录编号生成

```python
def _gen_record_no(direction: str) -> str:
    prefix = "IN" if direction == "in" else "OUT"
    date_str = datetime.now().strftime("%Y%m%d")
    return f"{prefix}-{date_str}-{int(datetime.now().timestamp()) % 100000:05d}"
```

格式：`IN-20260625-49751`，按日期分前缀 + 时间戳后 5 位。

### 3.3 文件上传 + 水印

```python
# files.py
@router.post("/photo")
async def upload_photo(file, post_id):
    # 1. 校验类型 + 大小
    # 2. 读字节
    # 3. 加水印
    watermarked = add_watermark(
        content,
        time_str=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        post_name=post.name,
        operator_name=current_user.real_name,
    )
    # 4. 保存
    rel_path = save_photo(watermarked)
    # 5. 返回 URL
    return {"url": f"/photos/{rel_path}"}
```

水印模板 `{time} | {post} | {operator}` 在 config.py 配置。

### 3.4 站内信通知

```python
# records.py create_in
_send_approval_message(db, req.approver_id, record)
db.add(msg)  # 类型：approval_request
db.commit()
```

后续审批通过/驳回时：
- 给**操作人保安**发 approval_result 类型站内信
- 让保安能在「消息中心」看到结果

---

## 阶段 4：核心前端（Day 3-4）

### 4.1 路由

```js
const routes = [
  { path: '/login', component: Login },
  {
    path: '/',
    component: Layout,
    children: [
      { path: 'dashboard', component: Dashboard },
      { path: 'records/in', component: RecordIn },
      { path: 'records/out', component: RecordOut },
      { path: 'records', component: RecordList },
      { path: 'records/:id', component: RecordDetail },
      { path: 'approval', component: Approval },
      { path: 'reports', component: Reports },
      { path: 'messages', component: Messages },
      { path: 'profile', component: Profile },
      { path: 'admin/users', component: AdminUsers },
      { path: 'admin/posts', component: AdminPosts },
      { path: 'admin/configs', component: AdminConfigs },
    ],
  },
]
```

### 4.2 Layout 结构

```
┌──────────────────────────────────────────────┐
│ Logo    菜单区                                  │
│ 首页       ┌─────────────────────────────┐   │
│ 进场登记   │                              │   │
│ 出场登记   │   router-view 内容          │   │
│ 记录查询   │                              │   │
│ 待我审批   │                              │   │
│ ...        └─────────────────────────────┘   │
│ 个人中心                                     │
│ 管理后台 ▼                                   │
│   用户管理                                   │
│   岗亭管理                                   │
└──────────────────────────────────────────────┘
顶部：☰ 折叠  | 用户头像 + 下拉
```

### 4.3 拍照上传（浏览器端）

```vue
<el-upload
  :http-request="uploadFront"
  :before-upload="beforePhotoUpload"
  accept="image/*"
  capture="environment"  <!-- 手机端调起后置摄像头 -->
>
  <div class="photo-placeholder">
    <el-icon><Camera /></el-icon>
    <span>点击拍照</span>
  </div>
</el-upload>
```

`capture="environment"` 是关键 —— HTML5 属性，手机浏览器会调起后置摄像头；PC 浏览器是普通文件选择。

### 4.4 状态管理（Pinia）

```js
// stores/auth.js
export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('vehicle_token') || '')
  const user = ref(JSON.parse(localStorage.getItem('vehicle_user') || 'null'))

  async function login(username, password) {
    const res = await loginApi(username, password)
    token.value = res.data.access_token
    user.value = res.data.user
    localStorage.setItem('vehicle_token', token.value)
    localStorage.setItem('vehicle_user', JSON.stringify(user.value))
  }

  return { token, user, isLoggedIn, isAdmin, isSupervisor, login, logout }
})
```

---

## 阶段 5：照片水印 + 报表（Day 4-5）

### 5.1 水印库选型

- **Pillow**（PIL fork）→ 标准选择，中文支持要额外装字体

### 5.2 中文字体方案

**问题**：容器里没字体 → `find_chinese_font()` 全部 fallback → `ImageFont.load_default()` 只能画 ASCII → 中文显示成方块。

**解决**：在 Dockerfile 里 `apt-get install fonts-noto-cjk`（Google Noto CJK 字体包，~50MB）。

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc default-libmysqlclient-dev pkg-config curl \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*
```

### 5.3 水印实现

```python
def add_watermark(image_bytes, time_str, post_name, operator_name):
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    width, height = img.size
    
    font_size = max(20, int(width * 0.02))
    font = find_chinese_font(font_size)
    
    watermark_text = settings.watermark_format.format(
        time=time_str, post=post_name, operator=operator_name
    )
    
    draw = ImageDraw.Draw(img)
    bbox = draw.textbbox((0, 0), watermark_text, font=font)
    text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    
    padding = 20
    x = width - text_w - padding
    y = height - text_h - padding
    
    # 阴影 + 主文字
    draw.text((x + 2, y + 2), watermark_text, font=font, fill=(0, 0, 0, 200))
    draw.text((x, y), watermark_text, font=font, fill=(255, 255, 255))
    
    output = io.BytesIO()
    img.save(output, format="JPEG", quality=settings.photo_quality, optimize=True)
    return output.getvalue()
```

### 5.4 报表

```python
@router.get("/export/excel")
async def export_excel(...):
    query = db.query(Record).filter(...)  # 按筛选条件
    
    wb = Workbook()
    ws = wb.active
    ws.title = "车辆进出记录"
    ws.append(["业务编号", "车牌", "类型", ...])  # 表头
    
    for r in items:
        ws.append([r.record_no, r.plate_number, ...])
    
    wb.save("/tmp/xxx.xlsx")
    return FileResponse("/tmp/xxx.xlsx", filename=...)
```

前端用 `Blob` + `<a download>` 触发浏览器下载。

---

## 阶段 6：Bug 修复轮（Day 6，多轮迭代）

> 单独成节是因为这阶段几乎全是「测试 → 发现 bug → 改 → 部署 → 再测」的循环。

### 6.1 CORS + trailing-slash

**症状**：浏览器报 `Access to XMLHttpRequest... blocked by CORS policy`

**根因**：
1. FastAPI 默认开启 `redirect_slashes=True` → 307 重定向不携带 CORS 头
2. nginx 反代没把 OPTIONS 预检单独处理

**修复**：

```python
# main.py
app = FastAPI(redirect_slashes=False)  # 关闭自动重定向
```

```nginx
# nginx.conf
location /api/ {
    if ($request_method = 'OPTIONS') {
        add_header Access-Control-Allow-Origin '*';
        return 204;
    }
    if ($uri ~ "^/api/v1/[^/]+$") {
        rewrite ^(.*)$ $1/ last;  # nginx 补斜杠
    }
    proxy_pass http://backend:8000;
}
```

### 6.2 SQLAlchemy ENUM 映射冲突

**症状**：`LookupError: 'admin' is not among the defined enum values`

**根因**：SQLAlchemy `Enum(SomeEnum)` 默认按 **Python 成员名**（大写）查，但数据库存的是 **值**（小写）。

**修复**：所有 `Column(Enum(...))` 改成 `Column(String(20))`，enum 类型只在 Python 内存里用。

> 这是大手术：用户表 / 记录表 / 各种 enum 字段都改了。

### 6.3 照片 404

**症状**：上传成功，URL 返回 404。

**根因**：nginx 把 `/photos/*` proxy 到 backend，但后端没 mount 静态文件目录。

**修复**：

```python
# main.py
import os
_PHOTOS_DIR = os.environ.get("PHOTO_BASE_DIR", "/photos")
if os.path.isdir(_PHOTOS_DIR):
    app.mount("/photos", StaticFiles(directory=_PHOTOS_DIR), name="photos")
```

### 6.4 双 worker bootstrap race condition

**症状**：偶尔后端启动失败 `Duplicate entry 'dashboard'`

**根因**：Dockerfile 用 `--workers 2`，两个 uvicorn worker 同时跑 `bootstrap.py`，都看到 modules 表为空，都尝试 insert，第二个 commit 失败。

**修复**：bootstrap 改成 `try insert; except IntegrityError: rollback + continue` 的幂等模式。

### 6.5 前端 chunk 缓存

**症状**：更新代码后浏览器还在用旧版 JS

**根因**：vite build 输出带 hash 的 chunk 文件名，nginx 默认缓存，旧 index.html 引用旧 hash。

**修复**：nginx 给 `/` 和 `/index.html` 加 `Cache-Control: no-cache, no-store, must-revalidate`。

### 6.6 清理旧 chunk 文件

**症状**：服务器上有多个版本的 chunk 同时存在，浏览器可能拿到旧的。

**修复**：部署前 `rm -rf /usr/share/nginx/html/*`，再 `cp frontend_dist/. frontend:/usr/share/nginx/html/`。

---

## 阶段 7：角色权限系统 + 自定义模块（Day 7）

### 7.1 设计动机

最初只用 `if current_user.role == 'admin'` 硬编码判断，扩展性差。新增需求：

- 不同角色看不同菜单
- 主管能看哪些 / 审批人能看哪些 要可配置
- 管理员能加自定义功能模块

### 7.2 数据模型升级

新增 2 张表：

```sql
-- 模块定义（内置 + 自定义）
modules (id, code, name, path, icon, category, sort_order,
         is_builtin, is_active, ...)

-- 角色-模块映射
role_modules (id, role, modules JSON, ...)
```

### 7.3 API 设计

```python
# auth.py
GET /auth/login  → 返回 visible_modules（对象数组）

# role_modules.py
GET /role-modules           # 全部角色配置
PUT /role-modules/{role}    # admin 编辑某角色

# modules.py
GET    /modules
POST   /modules
PUT    /modules/{id}
DELETE /modules/{id}        # 仅自定义能删
```

### 7.4 前端动态菜单

```vue
<!-- Layout.vue -->
<el-menu-item v-for="m in visibleModules" :index="m.path">
  <el-icon><component :is="iconMap[m.icon]" /></el-icon>
  <template #title>{{ m.name }}</template>
</el-menu-item>
```

完全从 `authStore.visibleModules` 渲染，加模块改数据库就生效，不用改前端。

### 7.5 路由守卫升级

```js
router.beforeEach((to, from, next) => {
  // 模块检查
  if (to.meta.module && !authStore.hasModule(to.meta.module)) {
    return next('/dashboard')
  }
})
```

### 7.6 自定义模块 catch-all 路由

```js
// router/index.js (children 最后)
{ path: ':pathMatch(.*)*', component: CustomModule }
```

用户新建「黑名单管理」模块，path=/admin/blacklist —— 自动落到 CustomModule 占位页（显示模块信息），不用改前端。

---

## 阶段 8：删除/恢复 + 文档整理（Day 7 末尾）

### 8.1 软删除设计

```sql
ALTER TABLE records ADD COLUMN is_deleted TINYINT(1) DEFAULT 0,
                       deleted_at DATETIME, deleted_by INT,
                       deleted_by_name VARCHAR(50), deleted_reason VARCHAR(200);
```

为什么不直接物理删除？

- 业务连续性：删错了能恢复
- 合规：审计要求保留历史
- 数据完整性：避免外键悬挂

### 8.2 API

```python
@router.post("/batch-delete")
async def batch_delete(payload, ...):
    # 1. 校验权限（仅 admin）
    # 2. 校验 reason 必填
    # 3. 遍历每条记录：
    #    - 不存在 → skip
    #    - 已删 → skip
    #    - 已审批+已匹配出场 且 !force → skip
    #    - 写 audit_logs.details.snapshot（删前快照）
    #    - 设 is_deleted=1 + 删除信息
    # 4. db.commit()
    # 5. 返回 {deleted, skipped, deleted_count, skipped_count}
```

### 8.3 前端 UI

RecordList.vue 加：
- 多选列（仅 admin）
- 顶部「显示/隐藏已删」开关
- 「删除选中」红色按钮（弹原因对话框）
- 已删行用灰色斜体显示
- 「恢复选中」按钮（在「显示已删」模式下）

### 8.4 文档整理

写 docs/v1.0.0/ 下的：
- PROJECT_GUIDE.md（项目说明书）
- ROADMAP.md（本文）
- ARCHITECTURE.md（架构图）
- DEPLOYMENT.md（部署文档）
- CHANGELOG.md（变更日志）
- VERSIONING.md（版本管理规范）

---

## 关键设计决策回顾

### 决策 1：内网自托管 vs 云服务

**选择**：内网自托管  
**理由**：
- 数据不出厂（合规要求）
- 不需要付费订阅
- NAS 资源够用

**代价**：
- 无公网访问（员工回家后看不到）
- 无 CDN 加速
- 运维需要 IT 自己来

### 决策 2：单体 vs 微服务

**选择**：单体 3 服务（db / backend / frontend）  
**理由**：
- 流量小（单厂区 < 100 车次/天）
- 单机能支撑
- 微服务会增加运维复杂度

**未来扩展**：如果上多厂区，可以把 backend 拆分成「认证」「业务」「报表」3 个微服务。

### 决策 3：Pillow 水印 vs 前端 canvas 水印

**选择**：后端 Pillow  
**理由**：
- 前端加 → 用户截图后能 P 掉 → 失去防伪意义
- 后端加 → 照片入库时就带水印，无法绕过
- Pillow 中文支持稳定（装 Noto CJK 即可）

### 决策 4：动态模块 vs 硬编码菜单

**选择**：动态模块（数据库存）  
**理由**：
- admin 改菜单不用改代码 + 重 build + 部署
- 后续如果加「车辆统计」「黑名单」「门禁卡」等模块，后端加 API + 前端占位即可

**代价**：
- 前端图标必须用 Element Plus 全局注册的图标名（string）
- 自定义模块没有专属页面 → 暂时用 CustomModule 占位

### 决策 5：软删除 vs 硬删除

**选择**：软删除 + 审计快照  
**理由**：
- 误删可恢复（IT 误操作很常见）
- 审计要求保留历史
- 照片文件不动（避免文件系统不一致）

---

## 附录：关键文件清单

| 文件 | 行数 | 作用 |
|---|---|---|
| backend/main.py | ~150 | 应用入口 + 路由注册 + StaticFiles |
| backend/app/api/records.py | ~550 | 进出记录核心 API |
| backend/app/api/files.py | ~65 | 照片上传 + 水印 |
| backend/app/models/record.py | ~130 | 记录 ORM |
| backend/app/utils/watermark.py | ~125 | 水印工具 |
| backend/app/services/bootstrap.py | ~85 | 启动初始化（密码/模块/权限） |
| frontend/src/views/RecordList.vue | ~370 | 记录查询页（最复杂） |
| frontend/src/views/admin/RoleModules.vue | ~370 | 角色权限 + 模块管理 |
| frontend/src/components/Layout.vue | ~270 | 动态菜单 Layout |

---

## 时间线汇总

| 日期 | 事件 |
|---|---|
| 2026-06 中旬 | 启动项目，搭建基础设施 |
| 2026-06-23 | 拍照 + 上传 + 水印全链路跑通 |
| 2026-06-24 | 加 nginx 反代 + 修 CORS + 修 307 重定向 |
| 2026-06-24 下午 | 前端 chunk 缓存坑 |
| 2026-06-25 上午 | 角色权限 + 自定义模块系统 |
| 2026-06-25 上午末 | 删除/恢复功能 + 用户管理 approver 角色修复 |
| 2026-06-25 中午 | **v1.0.0 正式发布** |

---

**附**：完整功能 / 角色 / 部署细节见 [`PROJECT_GUIDE.md`](./PROJECT_GUIDE.md)。
