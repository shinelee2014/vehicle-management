# 厂区车辆进出管理系统

> 部署于群晖 NAS（局域网），手机/电脑浏览器访问。进出记录自动存档、拍照带水印、多级审批、统计报表。

![version](https://img.shields.io/badge/version-1.0.0-blue)
![python](https://img.shields.io/badge/python-3.11-blue)
![vue](https://img.shields.io/badge/vue-3-green)
![mariadb](https://img.shields.io/badge/mariadb-10.11-orange)

## ✨ 核心功能

- 🚗 **车辆进出登记**（内部车 / 外部车 / 货车）
- 📸 **拍照取证**（自动加水印：时间 / 岗亭 / 操作人）
- ✅ **多级审批**（保安 → 审批人 / 主管 → 通过 / 驳回）
- 🔔 **站内信通知**（待审批 + 审批结果）
- 👥 **4 角色权限**（保安 / 审批人 / 主管 / 管理员），**可动态配置可见模块**
- 🧩 **自定义功能模块**（admin 可加任意模块，分配给角色，无需改代码）
- 📊 **手动查询 + Excel 导出**
- 📅 **定时任务**（日报、周报、归档、超时审批）
- 🗑️ **数据治理**（admin 批量软删除 + 恢复 + 完整审计）

## 📂 项目结构

```
vehicle-management/
├── README.md                    # ← 你在这里
├── CHANGELOG.md                 # 所有版本变更日志
├── docker-compose.yml           # 当前开发版本编排
├── .env.example                 # 当前开发版本环境变量模板
│
├── backend/                     # 当前开发版本 · 后端源码
├── frontend/                    # 当前开发版本 · 前端源码
├── deploy/                      # 当前开发版本 · 部署文件（init.sql）
│
├── docs/                        # 📚 文档（按版本组织）
│   ├── README.md                # 文档入口
│   ├── VERSIONING.md            # 版本管理规范
│   └── v1.0.0/                  # 当前版本文档
│       ├── PROJECT_GUIDE.md     # 项目说明书
│       ├── ROADMAP.md           # 技术路线图（开发流程）
│       ├── ARCHITECTURE.md      # 架构图
│       └── DEPLOYMENT.md        # 部署文档
│
└── versions/                    # 📦 历史版本源码快照
    ├── README.md
    ├── _artifacts/              # 开发过程临时文件
    └── v1.0.0/                  # v1.0.0 完整源码快照
```

## 🚀 快速开始

### 用户（浏览器访问）

打开浏览器访问：`http://192.168.1.100:8080`

默认账号：
| 账号 | 密码 | 角色 |
|---|---|---|
| `admin` | `admin123` | 管理员（首次登录后改密） |
| `spr1` | `123456` | 审批人（v1.0.0 新增） |
| `supervisor1` | `123456` | 主管 |
| `security1` | `123456` | 保安 |

### 开发者

详细部署步骤见 [`docs/v1.0.0/DEPLOYMENT.md`](docs/v1.0.0/DEPLOYMENT.md)。

## 📚 文档导航

| 文档 | 用途 |
|---|---|
| [项目说明书](./docs/v1.0.0/PROJECT_GUIDE.md) | 业务背景、功能清单、角色权限、接口列表 |
| [技术路线图](./docs/v1.0.0/ROADMAP.md) | 从 0 到 1 的开发过程 + 关键决策 |
| [架构图](./docs/v1.0.0/ARCHITECTURE.md) | 部署架构 / 数据流图 / ER 图 |
| [部署文档](./docs/v1.0.0/DEPLOYMENT.md) | 首次部署 / 日常运维 / 故障排查 / 备份 |
| [版本管理规范](./docs/VERSIONING.md) | 版本号规则、发布流程、回滚 |
| [变更日志](./CHANGELOG.md) | 所有版本的 changelog |

## 🛠️ 技术栈

| 层 | 选型 |
|---|---|
| 前端 | Vue 3 + Vite + Element Plus + Pinia + Vue Router 4 + Axios |
| 后端 | Python 3.11 + FastAPI + SQLAlchemy 2.0 + Pydantic + APScheduler |
| 数据库 | MariaDB 10.11（utf8mb4） |
| 图片处理 | Pillow（加水印） + Noto CJK 字体（中文支持） |
| 鉴权 | JWT (HS256) + bcrypt |
| 反向代理 | nginx (alpine) |
| 部署 | Docker Compose（3 服务） |
| 目标环境 | Synology NAS DS1621+ (192.168.1.100) |

## 📜 版本

**当前**：v1.0.0（2026-06-25）

详细变更见 [CHANGELOG.md](./CHANGELOG.md)

---

**内部使用**
