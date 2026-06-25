# 版本快照目录

每个发版时，会把当时的源码完整快照复制到 `versions/v<版本>/`。

## 当前版本

| 版本 | 发布日期 | 源码 |
|---|---|---|
| v1.0.0 | 2026-06-25 | [versions/v1.0.0/](./v1.0.0/) |

## 临时产物

开发过程临时文件（zip 包、b64 临时脚本、临时日志）放在 `_artifacts/`，**不污染主源码**。定期清理。

## 如何切换版本

```bash
# 查看当前
ls versions/

# 切到 v1.0.0 源码
cp -r versions/v1.0.0/* /volume1/docker/vehicle-management/

# 重新部署
cd /volume1/docker/vehicle-management
docker-compose up -d --build
```

## 归档策略

- 3 个最新版本保留解压目录
- 老版本可压缩成 `v1.0.0-archived.tar.gz` 后删除解压目录
- 大版本下架后整系列打包

详见 [../docs/VERSIONING.md §9](../docs/VERSIONING.md)
