# 版本管理规范

本文档规范厂区车辆进出管理系统（vehicle-management）的版本发布、回滚、迭代流程。

---

## 1. 版本号规则

采用 [语义化版本](https://semver.org/lang/zh-CN/)：`主版本.次版本.修订号`（如 `1.2.3`）

### 1.1 何时递增

| 变更类型 | 递增位 | 示例 |
|---|---|---|
| 不兼容的架构变更 | **主版本** | 0.x → 1.0, 1.x → 2.0 |
| 向后兼容的新功能 | **次版本** | 1.0 → 1.1, 1.1 → 1.2 |
| 向后兼容的 bug 修复 | **修订号** | 1.2.0 → 1.2.1 |
| 文档/工具/部署优化 | **次版本** | 1.2 → 1.3 |

### 1.2 预发布版本

可选后缀（按需）：

- `1.3.0-alpha.1` - 内部测试
- `1.3.0-beta.1` - 公开测试
- `1.3.0-rc.1` - 候选发布

正式版不带后缀。

---

## 2. 目录结构

### 2.1 项目根布局

```
vehicle-management/
├── backend/                 # 当前开发版本的源码
├── frontend/                # 当前开发版本的源码
├── deploy/                  # 当前版本的部署文件
├── docker-compose.yml       # 当前版本的编排
├── .env.example
├── README.md                # 项目入口
├── CHANGELOG.md             # 所有版本变更记录
│
├── docs/                    # 所有版本文档
│   ├── README.md            # 文档入口
│   ├── VERSIONING.md        # 本文件
│   └── v1.0.0/              # v1.0.0 版本文档
│       ├── PROJECT_GUIDE.md
│       ├── ROADMAP.md
│       ├── ARCHITECTURE.md
│       └── DEPLOYMENT.md
│
└── versions/                # 历史版本源码快照
    ├── README.md
    ├── _artifacts/          # 开发过程临时文件（zip、b64 临时脚本）
    └── v1.0.0/              # v1.0.0 源码完整快照
        ├── backend/
        ├── frontend/
        ├── deploy/
        ├── docker-compose.yml
        └── .env.example
```

### 2.2 命名约定

- **源码目录**：`versions/v<主版本>.<次版本>.<修订号>/`，如 `versions/v1.0.0/`
- **文档目录**：`docs/v<主版本>.<次版本>.<修订号>/`，如 `docs/v1.0.0/`
- **快照打包**（可选）：`versions/v1.0.0/v1.0.0-source.tar.gz`

---

## 3. 发布流程

### 3.1 完整流程图

```
开发新功能 / 修 bug
    │
    ▼
在主分支（main / master）提交代码
    │
    ▼
本地测试通过 → 提交 commit
    │
    ▼
更新 CHANGELOG.md → 加到 [Unreleased] 段
    │
    ▼
NAS 测试环境部署验证
    │
    ▼
决定版本号
    │
    ├── bug fix: 修订号 +1
    ├── 新功能: 次版本 +1
    └── 破坏性变更: 主版本 +1
    │
    ▼
执行发布脚本（见 §4）
    │
    ▼
【核心动作】把当前源码快照复制到 versions/v<新版本号>/
    │
    ▼
【核心动作】把当前 docs 复制到 docs/v<新版本号>/
    │
    ▼
更新 CHANGELOG.md → 把 [Unreleased] 重命名为 [新版本号] + 日期
    │
    ▼
git commit "release v1.x.y"
    │
    ▼
git tag v1.x.y
    │
    ▼
推送 tag → 触发自动部署（如配置了 CI）
    │
    ▼
生产环境更新部署（参考 DEPLOYMENT.md §6）
```

### 3.2 发布 checklist

每次发布前检查：

- [ ] 所有新功能 / 修复已 commit 到 main
- [ ] CHANGELOG.md 已更新（[Unreleased] → [新版本] + 日期）
- [ ] 当前源码已备份到 `versions/v<新版本>/`
- [ ] 当前文档已备份到 `docs/v<新版本>/`
- [ ] 数据库迁移 SQL 已写好（如有 schema 变更）
- [ ] `docker-compose build` 成功
- [ ] NAS 测试环境验证通过
- [ ] README.md 项目版本号已更新
- [ ] .env.example 字段如有变更已同步

---

## 4. 发布命令模板

### 4.1 复制源码到版本快照

```bash
cd /path/to/vehicle-management

NEW_VER="v1.1.0"

# 1. 复制源码
mkdir -p versions/$NEW_VER
cp -r backend frontend deploy versions/$NEW_VER/
cp docker-compose.yml .env.example versions/$NEW_VER/

# 2. 复制文档
mkdir -p docs/$NEW_VER
cp docs/v<旧版本>/*.md docs/$NEW_VER/  # 复制上一版文档作底
# 然后修改 PROJECT_GUIDE.md / ROADMAP.md 等

# 3. 更新 CHANGELOG.md
# 编辑 CHANGELOG.md，把 [Unreleased] 改成 [1.1.0] - YYYY-MM-DD

# 4. git
git add .
git commit -m "release $NEW_VER"
git tag $NEW_VER
git push origin main --tags
```

### 4.2 发布后立即清理

- [ ] 把 `_artifacts/` 里 v<新版本> 的临时部署脚本（zip / b64）删掉或归档
- [ ] 如果有破坏性变更，更新 README.md 的「当前版本」标识

---

## 5. 迭代开发流程

### 5.1 推荐工作流

```
main 分支 ─ 稳定可发布
   │
   ├── feat/xxx ─ 单个功能分支
   │     │
   │     └── 完成后 → PR → merge 到 main
   │
   └── hotfix/xxx ─ 紧急修复
         │
         └── 完成后 → PR → merge → 立即发修订号
```

### 5.2 一次完整迭代示例（v1.0.0 → v1.1.0）

**目标**：加微信小程序订阅消息推送

```
1. 创建分支
   git checkout -b feat/wechat-push

2. 开发
   - backend/app/services/wechat.py（新文件）
   - backend/app/services/scheduler.py（注册 push job）
   - backend/app/api/configs.py（加 wechat config）
   - frontend/src/views/admin/Configs.vue（加 UI）
   - docs/v1.1.0/PROJECT_GUIDE.md（更新功能列表）
   - docs/v1.1.0/ROADMAP.md（追加路线图）

3. 本地测试 + NAS 测试环境验证

4. merge 到 main
   git checkout main
   git merge feat/wechat-push

5. 更新 CHANGELOG.md
   ## [1.1.0] - YYYY-MM-DD
   ### 新增
   - 微信小程序订阅消息推送（审批结果）

6. 复制源码到 versions/v1.1.0/
   (按 §4.1 操作)

7. 部署到生产
   (按 DEPLOYMENT.md §6)

8. 删 feat 分支
   git branch -d feat/wechat-push
```

---

## 6. 回滚流程

### 6.1 紧急回滚（生产事故）

```bash
# 1. SSH 到 NAS
ssh admin@192.168.1.100

# 2. 停当前服务
cd /volume1/docker/vehicle-management
docker-compose down

# 3. 切换代码
git checkout v1.0.0  # 上一稳定版
# 或: git checkout <commit-hash>

# 4. 恢复数据（如有数据库迁移破坏）
# 见 DEPLOYMENT.md §5.1 / §6.2

# 5. 重启
docker-compose up -d --build

# 6. 验证
curl http://localhost:8080/health
```

### 6.2 部分回滚（只回退某个功能）

不建议——v1.0.0 阶段代码耦合较低，单个功能回退成本高。**直接全版本回退**更稳。

---

## 7. 备份策略

### 7.1 源码备份

| 备份对象 | 方式 | 频率 |
|---|---|---|
| 当前开发版本 | git 仓库（NAS 主机 + GitHub/Gitee 远程） | 每次 commit |
| 历史版本快照 | `versions/v<版本>/` 目录 | 每次发版时 |
| 部署包 | `versions/v<版本>/v<版本>-source.tar.gz` | 每次发版时 |

### 7.2 数据备份

| 备份对象 | 方式 | 频率 |
|---|---|---|
| 数据库 | NAS Hyper Backup → 外接存储 / 云 | 每天 |
| 照片 | 同上 | 每天 |
| .env | git 仓库 + 单独加密备份 | 改了就备份 |

### 7.3 备份验证

每季度做一次「灾难恢复演练」：

1. 在另一台机器按文档全新部署
2. 从备份恢复数据库 + 照片
3. 验证功能正常
4. 记录演练结果到 `docs/DR_RUNBOOK.md`

---

## 8. 与 AI 协作时的版本管理

本项目大量使用 Mavis AI 辅助编程。AI 协作时的额外规则：

### 8.1 提示词规范

每次让 AI 改代码前，明确说：

```
我现在在做 [feat/fix]，目标是 vX.Y.Z
- 不要改 [文件A]
- 不要改数据库 schema（除非明确说）
- 完成后告诉我改了哪些文件
```

### 8.2 AI 输出物归档

AI 生成的临时脚本（zip、b64、python 部署脚本）放 `versions/_artifacts/vX.Y.Z/`，**不污染主源码目录**。

### 8.3 AI 错误回滚

如果 AI 改坏了某文件，直接：

```bash
git checkout HEAD -- path/to/file
```

---

## 9. 长期归档策略

### 9.1 一年以上的版本

如果某版本已经下线 1 年以上，考虑：

- 把 `versions/v<老版本>/` 打包成 `versions/v<老版本>-archived.tar.gz`
- 删除解压后的目录（保留压缩包）
- 在 `docs/` 里只保留最新 3 个版本的小版本文档，老版本打 zip 存档

### 9.2 大版本归档

`v1.x` 整个系列下架后，把整个 `versions/v1/` 目录归档为 `v1-series-archived.tar.gz`。

---

## 10. 速查表

| 场景 | 命令 |
|---|---|
| 看当前版本 | 看 `docker-compose.yml` 里 `app` 镜像 tag，或 CHANGELOG.md 最新条目 |
| 切到指定版本 | `git checkout v1.0.0` |
| 发新版本 | 改代码 → 更新 CHANGELOG → 复制源码到 versions/v<新版本>/ → git tag |
| 回滚 | `git checkout <旧版本> && docker-compose up -d --build` |
| 看历史 | 翻 `versions/` 目录或 `docs/` 目录，或 `git log --tags` |

---

**变更历史**：

- 2026-06-25 创建（v1.0.0 发布时）
