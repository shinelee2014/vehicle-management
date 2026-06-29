# 厂区车辆进出管理系统 · 部署文档

## 1. 环境要求

### 1.1 硬件

| 项 | 最低 | 推荐 |
|---|---|---|
| NAS | Synology DS218+ 或更高 | DS1621+ / DS1821+ |
| CPU | x86_64 双核 | 四核及以上 |
| RAM | 4 GB | 8 GB |
| 存储可用空间 | 10 GB | 50 GB（含照片增长） |

### 1.2 软件

| 项 | 版本 |
|---|---|
| DSM | 7.2 或更高 |
| Container Manager | 内置最新版 |
| SSH 访问 | 启用 |

### 1.3 网络

- NAS 固定 IP（推荐 `192.168.1.100`）
- 客户端与 NAS 同网段

---

## 2. 首次部署

### 2.1 创建项目目录

```bash
# SSH 到 NAS
ssh admin@192.168.1.100

# 创建目录
sudo mkdir -p /volume1/docker/vehicle-management
sudo chown admin:users /volume1/docker/vehicle-management
```

### 2.2 上传代码

**方式 A：Git 克隆（推荐）**

```bash
cd /volume1/docker/vehicle-management
git clone <repo-url> .
```

**方式 B：scp 上传**

```powershell
# Windows 本地
scp -r C:\path\to\vehicle-management admin@192.168.1.100:/volume1/docker/
```

### 2.3 配置环境变量

```bash
cd /volume1/docker/vehicle-management
cp .env.example .env
nano .env
```

`.env` 内容（生产环境示例）：

```ini
# 数据库
DB_HOST=db
DB_PORT=3306
DB_NAME=vehicle_mgmt
DB_USER=vehicle
DB_PASSWORD=<强密码，建议 16+ 位随机>
DB_ROOT_PASSWORD=<另一个强密码>

# JWT（必须改！）
JWT_SECRET=<用 openssl rand -hex 32 生成>
JWT_EXPIRE_HOURS=8

# 应用
APP_NAME=厂区车辆进出管理系统
APP_ENV=production
LOG_LEVEL=INFO

# 业务
PHOTO_BASE_DIR=/photos
PHOTO_MAX_SIZE_MB=10
ARCHIVE_MONTHS=12
APPROVAL_TIMEOUT_MINUTES=30
APPROVAL_TIMEOUT_ACTION=auto_approve

# 时区
TZ=Asia/Shanghai
```

生成 JWT secret：

```bash
openssl rand -hex 32
# 输出: 8a3f9c1b2d5e...  ← 复制到 JWT_SECRET=
```

### 2.4 启动

```bash
cd /volume1/docker/vehicle-management
sudo docker-compose up -d --build
```

首次启动会：
1. 拉取 MariaDB 10.11 镜像
2. 构建 backend 镜像（含 Pillow、APScheduler、Noto CJK 字体）
3. 构建 frontend 镜像（含 Vue dist）
4. 启动 db，等 healthcheck 通过
5. 启动 backend，等 bootstrap 完成
6. 启动 frontend，nginx 服务监听 8080

**总耗时**：约 5-10 分钟（取决于网络）

### 2.5 验证

```bash
# 看容器状态
docker-compose ps
# 应该 3 个都是 healthy 或 running

# 看启动日志
docker-compose logs backend | tail -50

# 测试 API
curl http://localhost:8080/health
# 返回 {"code":0,"message":"ok","data":{"status":"healthy"}}

# 测试登录
curl -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

### 2.6 浏览器访问

打开 `http://192.168.1.100:8080`

默认账号：
- `admin / admin123` （管理员）
- `security1 / 123456` （保安）
- `supervisor1 / 123456` （主管）

**⚠️ 首次登录后立即修改密码！**

---

## 3. 日常运维

### 3.1 查看日志

```bash
# 所有服务最近 100 行
cd /volume1/docker/vehicle-management
docker-compose logs --tail=100

# 实时跟踪某个服务
docker-compose logs -f backend

# 只看错误
docker-compose logs backend | grep -i error
```

### 3.2 重启服务

```bash
# 重启单个
docker-compose restart backend

# 重启全部
docker-compose restart

# 完全停掉
docker-compose down

# 启动（用已构建的镜像）
docker-compose up -d
```

### 3.3 更新代码

```bash
cd /volume1/docker/vehicle-management

# 拉新代码
git pull

# 重新构建并启动
docker-compose up -d --build
```

⚠️ **生产环境建议**：先在测试环境验证，再上线。

### 3.4 数据库操作

```bash
# 进入 db 容器
docker-compose exec db bash

# 连接 MySQL
mysql -uvehicle -pvehicle123 vehicle_mgmt

# 查看表
SHOW TABLES;

# 查看用户
SELECT id, username, real_name, role FROM users;

# 退出
\q
exit
```

### 3.5 照片备份

照片存在 docker volume `vehicle-management_photos_data`，NAS 上挂载在 `/volume1/@docker/volumes/vehicle-management_photos_data/_data/`。

```bash
# 直接打包
tar czf photos_backup_$(date +%Y%m%d).tar.gz \
    /volume1/@docker/volumes/vehicle-management_photos_data/_data/

# 或用 Hyper Backup 整盘备份（推荐）
# DSM → 控制面板 → 计划备份 → 添加 → 选定 volume
```

### 3.6 清理空间

照片按 `YYYY-MM-DD` 子目录组织，**默认永不删除**。手动清理建议：

```bash
# 看占用
du -sh /volume1/@docker/volumes/vehicle-management_photos_data/_data/*

# 删 1 年前的（谨慎！）
# 建议先备份，再确认无引用，最后删
find /volume1/@docker/volumes/vehicle-management_photos_data/_data/ \
     -maxdepth 2 -type d -mtime +365 -exec rm -rf {} +
```

---

## 4. 故障排查

### 4.1 后端启动失败

```bash
docker-compose logs backend
```

常见错误：
- `Table 'xxx' doesn't exist` → 数据库表未创建。检查 `deploy/init.sql` 是否挂载成功。
- `Duplicate entry` → bootstrap 双 worker race。已修复，重 build 即可。
- `Address already in use` → 端口被占。`netstat -tlnp | grep 8000` 找占用进程。

### 4.2 前端 502

```bash
# 看 nginx 容器
docker-compose logs frontend

# 测试后端能不能访问
docker-compose exec frontend wget -O- http://backend:8000/health
```

如果 backend 不可达：
- 检查 `vehicle-net` 网络：`docker network inspect vehicle-management_vehicle-net`

### 4.3 拍照上传失败

- **症状 1**：照片选择后无反应
  - 看浏览器 DevTools Network → 上传请求 status code
  - 401 → token 过期，重新登录
  - 413 → 照片超过 10MB

- **症状 2**：照片上传后显示 404
  - 检查 nginx 是否代理 `/photos/` 到 backend
  - 检查后端是否 mount 了 `/photos` 目录

### 4.4 水印不显示中文

- 容器里没装字体。重新 build backend 镜像（Dockerfile 里有 `apt-get install fonts-noto-cjk`）

### 4.5 浏览器缓存老 JS

- **症状**：更新代码后看不到新功能
- **解决**：用 `Ctrl + Shift + R` 强制刷新，或开**无痕窗口**
- **预防**：nginx 已配 `Cache-Control: no-cache` 给 `/` 和 `/index.html`

---

## 5. 数据迁移与备份

### 5.1 完整备份

```bash
# 1. 停服务
docker-compose down

# 2. 备份数据库
docker run --rm \
  -v vehicle-management_db_data:/source \
  -v /volume1/backup:/backup \
  alpine sh -c "cd /source && tar czf /backup/db_$(date +%Y%m%d).tar.gz ."

# 3. 备份照片
tar czf /volume1/backup/photos_$(date +%Y%m%d).tar.gz \
    /volume1/@docker/volumes/vehicle-management_photos_data/_data/

# 4. 启动
docker-compose up -d
```

### 5.2 恢复到新 NAS

```bash
# 假设新 NAS IP 是 192.168.6.20

# 1. 部署代码（同首次部署）

# 2. 停 backend（避免 bootstrap 提前跑）
docker-compose up -d db frontend

# 3. 导入数据库
docker run --rm \
  -v vehicle-management_db_data:/target \
  -v /path/to/backup:/backup \
  alpine sh -c "cd /target && tar xzf /backup/db_20260101.tar.gz"

# 4. 导入照片
mkdir -p /volume1/@docker/volumes/vehicle-management_photos_data/_data
tar xzf /path/to/backup/photos_20260101.tar.gz -C /

# 5. 启动 backend
docker-compose up -d backend
```

---

## 6. 升级流程

### 6.1 升级到新版本（v1.0.0 → v1.x.y）

```bash
# 1. 备份（必做！）
docker-compose down
tar czf db_pre_v1x.tar.gz /volume1/@docker/volumes/vehicle-management_db_data/_data
tar czf photos_pre_v1x.tar.gz /volume1/@docker/volumes/vehicle-management_photos_data/_data

# 2. 拉新代码
cd /volume1/docker/vehicle-management
git fetch origin
git checkout v1.x.y

# 3. 跑数据库迁移（如果有）
# 见 CHANGELOG.md 的「升级说明」

# 4. 重 build + 启动
docker-compose up -d --build

# 5. 验证
curl http://localhost:8080/health
docker-compose logs backend | tail -20
```

### 6.2 回滚

```bash
# 切回旧代码
git checkout v1.0.0

# 重 build
docker-compose up -d --build

# 如果数据库结构变了，回滚数据
docker-compose down
rm -rf /volume1/@docker/volumes/vehicle-management_db_data/_data/*
tar xzf db_pre_v1x.tar.gz -C /volume1/@docker/volumes/vehicle-management_db_data/_data/
docker-compose up -d
```

---

## 7. 安全建议

### 7.1 内网限制

默认 nginx 监听 NAS 所有网卡。生产环境建议：

```nginx
# nginx.conf 加 server 配置，只监听内网 IP
listen 192.168.1.100:8080 default_server;
# 或加白名单
allow 192.168.6.0/24;
deny all;
```

### 7.2 加 HTTPS（可选）

```bash
# 1. 在 DSM 控制面板 → 安全性 → 证书 → 添加新证书
# 2. 选 Let's Encrypt 或自签证书
# 3. 反代到 nginx container

# 简单方案：用 DSM 自带的反向代理 + Let's Encrypt 证书
# DSM → 控制面板 → 登录门户 → 高级 → 反向代理服务器
# 添加：来源 https://vehicle.your-domain.com 目的地 http://192.168.1.100:8080
```

### 7.3 定期改密码

```bash
# 管理员每月改一次 JWT_SECRET，重启 backend 让所有 token 失效
# 用户每月改一次密码
```

### 7.4 防火墙

DSM 防火墙只允许内网段访问 NAS 的 8080 / 3306 / 8000 端口。

---

## 8. 常见运维命令速查

```bash
# 进入 backend 容器
docker-compose exec backend bash

# 进入 db 容器
docker-compose exec db bash

# 看所有容器资源占用
docker stats

# 清理 Docker 缓存（释放磁盘）
docker system prune -a

# 看 NAS 磁盘占用
df -h /volume1

# 看照片目录大小
du -sh /volume1/@docker/volumes/vehicle-management_photos_data/_data

# 导出数据库
docker-compose exec db mysqldump -uvehicle -pvehicle123 vehicle_mgmt > backup.sql

# 导入数据库
cat backup.sql | docker-compose exec -T db mysql -uvehicle -pvehicle123 vehicle_mgmt
```

---

## 9. 联系与升级

- **项目位置**：`/volume1/docker/vehicle-management`
- **文档**：`docs/` 目录
- **版本**：`docs/CHANGELOG.md`
- **遇到问题**：参考 `docs/v1.0.0/PROJECT_GUIDE.md` 第 6 节「已知限制」
