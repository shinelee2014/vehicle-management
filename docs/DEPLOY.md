# 群晖 NAS 部署详细文档

> 适用型号：DS1621+（4 核 8 线程 / 20GB 内存）  
> DSM 版本：7.2.2 或更高  
> 预计部署时间：30-60 分钟

---

## 📋 部署前准备

### 硬件确认
- [ ] 群晖 NAS 已开机，DSM 7.2+ 可访问
- [ ] 至少 **2GB** 可用磁盘空间（应用 + 照片 1 年约 500GB）
- [ ] NAS 内存 ≥ 4GB（推荐 8GB+）

### 网络确认
- [ ] 记录 NAS 内网 IP（如 `192.168.6.12`）
- [ ] 厂区内网互通正常
- [ ] 厂区电脑/手机能访问该 IP

### 软件准备
- [ ] NAS 已安装 **Container Manager**（DSM 7.2 套件中心搜索安装）
- [ ] 准备一台开发电脑（用于上传代码）

---

## 🚀 部署步骤

### 第一步：启用 NAS SSH（可选，用于传文件）

1. DSM → **控制面板** → **终端机和 SNMP** → **终端机**
2. 勾选 **启用 SSH 功能**（端口默认 22）
3. 应用

> ⚠️ 部署完成后建议关闭 SSH

---

### 第二步：上传代码到 NAS

#### 方式 A：SCP 上传（推荐）

在开发电脑上执行：

```bash
# Windows PowerShell 用 scp 或者 WinSCP 工具
scp -r C:\Users\L\.minimax-agent-cn\projects\vehicle-management admin@192.168.6.12:/volume1/docker/
```

#### 方式 B：SMB 共享上传

1. DSM → **控制面板** → **共享文件夹** → 新建 `docker` 文件夹
2. 在电脑上访问 `\\192.168.6.12\docker`
3. 把 `vehicle-management` 文件夹拖进去

#### 方式 C：Git 拉取（最优雅）

在 NAS 终端上：
```bash
cd /volume1/docker
sudo git clone <your-repo-url> vehicle-management
```

---

### 第三步：配置环境变量

```bash
cd /volume1/docker/vehicle-management
cp .env.example .env
nano .env  # 或用 vim
```

**必须修改**：
```env
DB_PASSWORD=你的强密码
JWT_SECRET=一串随机字符（建议 32 位以上）
```

生成 JWT 密钥：
```bash
openssl rand -hex 32
```

---

### 第四步：创建照片存储目录

```bash
sudo mkdir -p /volume1/vehicle_photos
sudo chown -R 1026:100 /volume1/vehicle_photos
sudo chmod 755 /volume1/vehicle_photos
```

> 用户 `1026` 是 MariaDB 容器内的用户 ID（官方镜像）

---

### 第五步：启动服务

```bash
cd /volume1/docker/vehicle-management
sudo docker-compose up -d
```

**查看启动日志**：
```bash
sudo docker-compose logs -f backend
```

等待出现以下日志表示成功：
```
✓ 数据库连接成功
✓ 重置默认账号 admin 的密码为 admin123 ...
✓ 定时任务已启动（3 个任务）
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

### 第六步：验证服务

```bash
# 检查容器状态
sudo docker-compose ps

# 健康检查
curl http://192.168.6.12:8000/health
# 应返回：{"code":0,"message":"ok","data":{"status":"healthy"}}
```

---

### 第七步：配置 NAS 反向代理（可选）

如果想让用户用 `http://192.168.6.12:8080` 访问：

1. DSM → **控制面板** → **登录门户** → **高级** → **反向代理服务器**
2. 新增：
   - 来源：协议 HTTP、端口 `8080`、主机名 `localhost`
   - 目的地：协议 HTTP、端口 `8080`、主机名 `localhost`
3. 保存

或者直接用 `http://192.168.6.12:8080` 访问即可（推荐，简单）。

---

## 🔧 维护操作

### 查看日志
```bash
# 所有服务
sudo docker-compose logs -f

# 单独看后端
sudo docker-compose logs -f backend
```

### 重启服务
```bash
sudo docker-compose restart
```

### 停止服务
```bash
sudo docker-compose down
```

### 更新代码
```bash
cd /volume1/docker/vehicle-management
sudo git pull
sudo docker-compose down
sudo docker-compose build
sudo docker-compose up -d
```

### 数据备份（重要！）

**数据库备份**（每天凌晨 4 点自动备份到 `/volume1/backup/db/`）：

```bash
# 创建备份脚本
cat > /volume1/docker/backup_db.sh << 'EOF'
#!/bin/bash
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
docker exec vehicle-db mysqldump -u root -p${DB_ROOT_PASSWORD} vehicle_mgmt > /volume1/backup/db/backup_${TIMESTAMP}.sql
# 保留最近 30 天
find /volume1/backup/db -name "*.sql" -mtime +30 -delete
EOF
chmod +x /volume1/docker/backup_db.sh
```

**配置定时任务**：
```bash
sudo crontab -e
# 添加
0 4 * * * /volume1/docker/backup_db.sh
```

**照片备份**：
- 群晖 **Hyper Backup** → 新建备份任务 → 选 `vehicle_photos` 文件夹 → 备份到外接 USB 硬盘

---

## 🆘 故障排查

### 容器启动失败

```bash
# 看具体错误
sudo docker-compose logs backend

# 常见：数据库连接失败
# 检查 .env 中 DB_HOST 是否为 db（不是 localhost）
```

### 忘记管理员密码

```bash
# 进入数据库容器
sudo docker exec -it vehicle-db mysql -u root -p vehicle_mgmt

# 重置 admin 密码（密码 hash 重新生成）
# 推荐用 Python 生成 bcrypt hash
```

### 端口冲突

修改 `docker-compose.yml` 中 `ports`，比如 `8080:80` 改成 `8888:80`。

### 照片显示不出来

检查 `/volume1/vehicle_photos` 目录权限：
```bash
ls -la /volume1/vehicle_photos
sudo chown -R 1026:100 /volume1/vehicle_photos
```

---

## 📊 性能调优（可选）

### 增加后端 workers

编辑 `backend/Dockerfile` 最后一行：
```
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### 数据库连接池

编辑 `backend/app/database.py` 的 `pool_size`：
```python
pool_size=20,  # 默认 10
max_overflow=30,  # 默认 20
```

---

## 🎯 部署完成检查清单

- [ ] 后端 `/health` 返回 healthy
- [ ] 前端可以打开（`http://192.168.6.12:8080`）
- [ ] 用 `admin / admin123` 能登录
- [ ] 创建一条测试进场记录
- [ ] 审批流程跑通
- [ ] 照片能上传并加水印
- [ ] 修改默认管理员密码
- [ ] 配置每日数据库备份
- [ ] 关闭 SSH（可选）

全部勾选完即可正式使用！
