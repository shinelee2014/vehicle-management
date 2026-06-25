# 厂区车辆进出管理系统 · 项目说明书

**版本**：v1.0.0  
**发布日期**：2026-06-25  
**部署目标**：Synology NAS（DS1621+，内网 192.168.6.12）  
**技术栈**：FastAPI · Vue 3 · MariaDB · Docker · APScheduler

---

## 1. 项目概述

### 1.1 业务背景

公司为汽车零部件模具/注塑厂区，每天进出车辆 30-80 台次。原流程靠保安纸质登记本，存在以下问题：

- 审批流程无电子化，找人审批靠跑腿
- 进出记录无法追溯、无法导出报表
- 货车停留时长靠人脑估算
- 没有数据沉淀，年度汇报材料难做

### 1.2 目标

用 **3 周内**搭一套**内网自托管**的车辆进出管理系统，覆盖：

1. 保安现场拍照登记（带时间/岗亭/操作人水印）
2. 多级审批（保安录入 → 主管/审批人审批 → 车辆放行）
3. 自动通知（站内信 + 移动端推送预留接口）
4. 进出记录查询、导出、报表
5. 系统角色与权限可配置（admin 可动态调整）

### 1.3 v1.0.0 范围

| 模块 | 状态 | 备注 |
|---|---|---|
| 用户登录 / 角色权限 | ✅ | 4 角色，权限可配置 |
| 进场登记（含拍照水印） | ✅ | 手机浏览器即可拍照 |
| 出场登记 | ✅ | 关联进记录 |
| 审批流（通过/驳回） | ✅ | 站内信通知 |
| 待我审批 | ✅ | 红点徽标 |
| 记录查询 / 导出 Excel | ✅ | 多条件筛选 |
| 消息中心 | ✅ | 站内信 |
| 个人中心 | ✅ | 改密码 |
| 用户管理 | ✅ | admin CRUD |
| 岗亭管理 | ✅ | admin CRUD |
| 系统配置 | ✅ | admin |
| 角色权限管理 | ✅ | 模块级权限可视化 |
| 自定义模块 | ✅ | admin 可新增 |
| 批量删除记录 | ✅ | 软删除 + 审计 |
| 定时任务（超时审批/归档/日报） | ✅ | APScheduler |
| 移动端推送（微信/钉钉） | ❌ | v1.1 规划 |
| 高可用（多副本） | ❌ | 当前 1 节点够用 |

---

## 2. 系统架构

### 2.1 整体架构

```
┌─────────────────── 用户 ───────────────────┐
│  手机浏览器 / PC 浏览器 / Android WebView   │
└──────────────────────┬──────────────────────┘
                       │ HTTP/HTTPS (8080)
                       ▼
┌─────────── Synology NAS (DS1621+) ──────────┐
│  ┌──────── nginx (vehicle-frontend) ──────┐ │
│  │   · SPA 静态托管 (Vue 3)                │ │
│  │   · 反向代理 /api/* → backend:8000      │ │
│  │   · 反向代理 /photos/* → backend:8000   │ │
│  └───────────────┬────────────────────────┘ │
│                  │                            │
│  ┌───── FastAPI (vehicle-backend) ─────────┐ │
│  │   · REST API                            │ │
│  │   · JWT 鉴权                            │ │
│  │   · Pillow 照片水印                      │ │
│  │   · APScheduler 定时任务                  │ │
│  └─────────┬──────────────────┬────────────┘ │
│            │                  │              │
│  ┌─────────▼────┐  ┌─────────▼──────────┐  │
│  │  MariaDB     │  │  /photos 卷         │  │
│  │  (vehicle-db)│  │  docker volume      │  │
│  └──────────────┘  └────────────────────┘  │
└──────────────────────────────────────────────┘
```

### 2.2 技术栈

| 层 | 选型 | 理由 |
|---|---|---|
| 前端框架 | Vue 3 + Composition API | 学习曲线平缓，生态成熟 |
| UI 库 | Element Plus | 桌面端表单/表格场景最强 |
| 状态管理 | Pinia | Vue 官方推荐 |
| 路由 | Vue Router 4 | SPA 标配 |
| HTTP 客户端 | Axios | 拦截器统一处理 token / 错误 |
| 构建工具 | Vite | 快 |
| 后端框架 | FastAPI | Python 类型提示 + 自动 OpenAPI 文档 |
| ORM | SQLAlchemy 2.0 + PyMySQL | 标准 |
| 数据库 | MariaDB 10.11 | NAS 自带，免运维 |
| 鉴权 | JWT (python-jose) | 无状态 |
| 密码哈希 | passlib + bcrypt | 标准 |
| 图片处理 | Pillow | 水印必备 |
| 定时任务 | APScheduler | 轻量 |
| 部署 | Docker Compose | 3 个服务一键起 |
| 反向代理 | nginx (alpine) | 标准 |

### 2.3 端口与路径

| 服务 | 容器内端口 | 宿主机端口 | 用途 |
|---|---|---|---|
| vehicle-frontend | 80 | 8080 | 浏览器访问入口 |
| vehicle-backend | 8000 | 8000 | API（内网直连） |
| vehicle-db | 3306 | 3306 | MySQL（内网直连） |

容器间通过 `vehicle-net` 桥接网络互联。

---

## 3. 功能详解

### 3.1 角色与权限

**4 个内置角色**：

| 角色 | code | 默认权限 |
|---|---|---|
| 保安 | `security` | 首页、进出登记、记录查询、消息、个人 |
| **审批人** | `approver` | 首页、待我审批、记录查询、消息、个人 |
| 主管 | `supervisor` | 上述 + 报表中心、岗亭管理 |
| 管理员 | `admin` | 全部（含角色权限、用户、岗亭、系统配置） |

**权限机制**：

- **模块级**：`modules` 表定义功能模块（path/icon/category）；`role_modules` 表存「某角色能看到哪些模块 code」
- **API 级**：每个接口用 `Depends(get_current_user)` 校验 token，按 `current_user.role` 做权限判断
- **路由级**：前端路由守卫同时检查角色和模块可见性

**自定义模块**：admin 在「角色权限 → 模块管理」可以新增/删除模块，分配给任意角色，无需改代码。

### 3.2 进场登记流程

```
保安 (security) 登录
   │
   ▼
打开「进场登记」→ 表单
   │
   ├── 选岗亭（默认第一个）
   ├── 输车牌号（自动大写）
   ├── 选车辆类型（内部/外部/货车）
   ├── (货车) 填货物描述
   ├── 选审批人
   │
   ▼
拍照（手机浏览器调相机）
   │
   ├── 拍照 → 上传到 /api/v1/files/photo
   ├── 后端 Pillow 加水印（时间/岗亭/操作人）
   ├── 保存到 /photos/YYYY-MM-DD/ 目录
   ├── 返回 URL: /photos/2026-06-25/HHMMSS_xxxxxx.jpg
   │
   ▼
预览确认 → 点提交
   │
   ▼
POST /api/v1/records/in
   │
   ├── 创建 record（状态: pending / in_pending）
   ├── 写站内信给审批人（approval_request 类型）
   ├── 写审计日志
   │
   ▼
返回成功 → 跳到「记录查询」或「记录详情」
```

### 3.3 审批流

```
审批人 / 主管 收到站内信
   │
   ▼
打开「待我审批」页面 → 看到待审批列表（红点徽标）
   │
   ▼
点详情 → 看完整信息（包含水印照片）
   │
   ├── 通过 → POST /records/{id}/approve
   │     ├── record 状态 → approved / in_approved
   │     ├── 写站内信给保安（approval_result 类型）
   │     └── 写审计日志
   │
   └── 驳回 → POST /records/{id}/reject
         ├── 写驳回原因
         ├── record 状态 → rejected / in_rejected
         ├── 写站内信给保安
         └── 写审计日志

⏰ 超时处理（APScheduler 每分钟检查）
   - approval_timeout_minutes 默认 30
   - 超时后自动通过（可配置 auto_reject）
```

### 3.4 出场登记

类似进场，但需要先关联一条进记录：

```
保安 打开「出场登记」
   │
   ├── 输车牌号 → 系统查找最近一条「已通过 + 未匹配出场」的进记录
   │     （找不到就报错）
   │
   ├── 自动填充：车辆类型、岗亭、关联进记录
   ├── 填停留时长（自动算） + 出场备注
   ├── 选审批人
   │
   ▼
拍照 → 提交（流程同进场）
   │
   ▼
出记录创建成功 → 进记录的 companion_id 指向出记录
两记录通过 related_record_id / companion_id 互相关联
```

### 3.5 照片与水印

**上传**：

```
前端 <input type="file" accept="image/*" capture="environment">
   │
   ▼
FormData → POST /api/v1/files/photo (multipart/form-data)
   │
   ├── 后端校验：必须是 image/* 类型 + 大小 ≤ 10MB
   ├── Pillow 打开
   ├── 加水印：右下角白色文字 + 黑色阴影，模板 "{time} | {post} | {operator}"
   ├── 保存为 JPEG（quality=85, optimize=True）
   └── 返回 URL
```

**水印字体**：Docker 镜像内装了 `fonts-noto-cjk`（Google Noto CJK 字体包），保证中文不显示成方块。

**存储**：docker volume `vehicle-management_photos_data`，挂载到容器 `/photos`，每天一个子目录。

### 3.6 报表与导出

- **报表中心**（主管/管理员可见）：周报、月报、季报、年报，按业务编号/岗亭/时间聚合
- **Excel 导出**：`/api/v1/records/export/excel`，按当前筛选条件导出，支持 ≤5000 条

### 3.7 定时任务

APScheduler 跑在 backend 进程内，启动时 `lifespan` 注册 3 个 job：

| 任务 | 触发 | 作用 |
|---|---|---|
| 检查超时审批 | 每分钟 | 审批超时自动通过/驳回 |
| 归档 1 年前数据 | 每天 02:00 | 1 年前的已结记录移到 archived 状态 |
| 检查并发送定时报表 | 每天 08:00 | 生成昨日日报 → 站内信通知相关人 |

### 3.8 删除与恢复（v1.0.0 末尾加的功能）

**目的**：测试数据清理 + 误操作修复。

**机制**：

1. **软删除**：records 表加 `is_deleted / deleted_at / deleted_by / deleted_by_name / deleted_reason` 字段
2. **API**：`POST /api/v1/records/batch-delete`，仅 admin，必填原因
3. **审计快照**：删除前把整条记录 JSON 写到 `audit_logs.details.snapshot`，保证可还原
4. **核心记录保护**：已审批 + 已匹配出场的进记录默认拒绝删，强制删需 `force=true`
5. **可恢复**：`POST /api/v1/records/{id}/restore`

**UI**：admin 在「记录查询」页面顶部有「显示/隐藏已删」开关，删除的记录用灰色斜体显示。

---

## 4. 部署

### 4.1 环境要求

- Synology NAS DS1621+ 或同档（CPU x86_64，RAM ≥ 4GB）
- Container Manager（Docker）已装
- 至少 20GB 可用空间（照片 + 数据库）

### 4.2 部署步骤

完整步骤见 [`DEPLOYMENT.md`](./DEPLOYMENT.md)。简述：

```bash
# 1. 克隆代码到 NAS
git clone <repo> /volume1/docker/vehicle-management
# 或 scp 上传

# 2. 创建 .env（参考 .env.example）

# 3. 启动
cd /volume1/docker/vehicle-management
docker-compose up -d --build

# 4. 验证
curl http://localhost:8080/health
# 浏览器访问 http://<NAS-IP>:8080
# 默认 admin / admin123
```

### 4.3 数据备份

- **数据库**：`vehicle-db` 容器的 MariaDB，volume `vehicle-management_db_data`
- **照片**：`vehicle-management_photos_data` volume

**推荐**：用 Hyper Backup 把 `/volume1/@docker/volumes/vehicle-management_*/` 加进备份计划，每天备份。

---

## 5. 已知限制 / 后续规划

### 5.1 v1.0.0 已知问题

1. **无 HTTPS**：内网使用，可加 Let's Encrypt / 自签证书
2. **无操作日志查看 UI**：审计日志写在 `audit_logs` 表，但前端没做查看页面（v1.1 加）
3. **照片不做缩略图**：原图直传，加载大图慢（v1.1 加缩略图）
4. **无消息推送**：审批通知只靠站内信 + 浏览器轮询（30s 一次），需要客户端打开
5. **uploads 目录无自动清理**：照片按日期存档，永远不删（手动清理）
6. **SQLAlchemy ENUM 类型不一致**：用户表用 MySQL ENUM，记录表用 String，下版本统一

### 5.2 v1.1 规划（候选）

- [ ] 微信小程序订阅消息推送（审批结果）
- [ ] 钉钉 webhook 推送
- [ ] 审计日志查看页面
- [ ] 照片缩略图生成
- [ ] HTTPS + 自签证书
- [ ] 岗亭地图（可视化岗亭位置）
- [ ] 黑白名单车辆管理（自定义模块已加好接口）
- [ ] 数据导入/导出（Excel 模板）
- [ ] 多语言（i18n）

### 5.3 v2.0 远期规划

- [ ] 多租户（多个厂区共用一套系统）
- [ ] AI 车牌识别（自动录入车牌）
- [ ] 人脸识别 + 车辆识别联动
- [ ] 移动 App（iOS / Android 原生）
- [ ] 与 ERP/MES 系统对接

---

## 6. 联系方式

- **项目所有者**：CEO 秘书 / IT 管理员（用户）
- **开发协助**：Mavis AI 助手（通过 `docs/VERSIONING.md` 走迭代流程）
- **紧急支持**：SSH 登录 NAS（`admin@192.168.6.12`）+ `cd /volume1/docker/vehicle-management && docker-compose logs`

---

**附**：

- [技术路线图（开发流程）](./ROADMAP.md)
- [架构图（系统组件）](./ARCHITECTURE.md)
- [部署文档](./DEPLOYMENT.md)
- [版本管理规范](../../VERSIONING.md)
- [变更日志](../../../CHANGELOG.md)
