-- ============================================================
-- 厂区车辆进出管理系统 - 数据库 Schema
-- 数据库：MariaDB 10.11 / MySQL 8.0
-- 字符集：utf8mb4（支持 emoji 和完整中文）
-- ============================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ============================================================
-- 1. 岗亭表
-- ============================================================
DROP TABLE IF EXISTS `posts`;
CREATE TABLE `posts` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(50) NOT NULL COMMENT '岗亭名称，如：1号门',
  `location` VARCHAR(200) DEFAULT NULL COMMENT '位置描述',
  `sort_order` INT NOT NULL DEFAULT 0 COMMENT '显示顺序',
  `is_active` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否启用',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='岗亭表';

-- ============================================================
-- 2. 用户表
-- ============================================================
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `username` VARCHAR(50) NOT NULL COMMENT '登录账号',
  `password_hash` VARCHAR(255) NOT NULL COMMENT 'bcrypt 加密密码',
  `real_name` VARCHAR(50) NOT NULL COMMENT '真实姓名',
  `role` ENUM('security', 'supervisor', 'admin') NOT NULL DEFAULT 'security' COMMENT '角色：security保安/supervisor主管/admin管理员',
  `post_id` INT UNSIGNED DEFAULT NULL COMMENT '所属岗亭（保安专属）',
  `is_approver` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否可作为审批人',
  `phone` VARCHAR(20) DEFAULT NULL COMMENT '手机号',
  `email` VARCHAR(100) DEFAULT NULL COMMENT '邮箱（用于推送）',
  `is_active` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否启用',
  `last_login_at` DATETIME DEFAULT NULL COMMENT '最后登录时间',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_username` (`username`),
  KEY `idx_role` (`role`),
  KEY `idx_post_id` (`post_id`),
  KEY `idx_is_approver` (`is_approver`),
  CONSTRAINT `fk_users_post` FOREIGN KEY (`post_id`) REFERENCES `posts` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- ============================================================
-- 3. 进出记录表（核心）
-- ============================================================
DROP TABLE IF EXISTS `records`;
CREATE TABLE `records` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `record_no` VARCHAR(30) NOT NULL COMMENT '业务编号：IN/OUT-YYYYMMDD-NNN',
  `plate_number` VARCHAR(20) NOT NULL COMMENT '车牌号',
  `vehicle_type` ENUM('internal', 'external', 'truck') NOT NULL COMMENT '车辆类型：internal内部/external外部/truck货车',
  `direction` ENUM('in', 'out') NOT NULL COMMENT '进出方向：in进场/out出场',
  `post_id` INT UNSIGNED NOT NULL COMMENT '岗亭',
  `operator_id` INT UNSIGNED NOT NULL COMMENT '操作人（保安）',
  `operator_name` VARCHAR(50) NOT NULL COMMENT '操作人姓名（冗余）',
  -- 进场信息
  `in_time` DATETIME DEFAULT NULL COMMENT '进场时间',
  `in_photos` JSON DEFAULT NULL COMMENT '进场照片 [{kind, url, watermark}]',
  `in_remark` TEXT DEFAULT NULL COMMENT '进场备注（事由/被访人）',
  -- 出场信息
  `out_time` DATETIME DEFAULT NULL COMMENT '出场时间',
  `out_photos` JSON DEFAULT NULL COMMENT '出场照片',
  `out_remark` TEXT DEFAULT NULL COMMENT '出场备注',
  -- 货车专属
  `cargo_info` VARCHAR(500) DEFAULT NULL COMMENT '货物描述（货车专属）',
  `loading_start_at` DATETIME DEFAULT NULL COMMENT '装卸货开始时间（货车专属）',
  `loading_end_at` DATETIME DEFAULT NULL COMMENT '装卸货结束时间（货车专属）',
  `loading_duration` INT DEFAULT NULL COMMENT '停留分钟数（自动算）',
  -- 审批
  `approver_id` INT UNSIGNED DEFAULT NULL COMMENT '审批人',
  `approver_name` VARCHAR(50) DEFAULT NULL COMMENT '审批人姓名（冗余）',
  `approval_status` ENUM('pending', 'approved', 'rejected', 'timeout') NOT NULL DEFAULT 'pending' COMMENT '审批状态',
  `approval_time` DATETIME DEFAULT NULL COMMENT '审批时间',
  `approval_remark` TEXT DEFAULT NULL COMMENT '审批意见',
  -- 关联
  `related_record_id` INT UNSIGNED DEFAULT NULL COMMENT '关联的进/出记录',
  `companion_id` INT UNSIGNED DEFAULT NULL COMMENT '配对的另一条记录ID（进-出配对）',
  -- 状态
  `status` ENUM(
    'in_pending', 'in_approved', 'in_rejected', 'in_timeout',
    'out_pending', 'out_approved', 'out_rejected', 'out_timeout',
    'completed'
  ) NOT NULL DEFAULT 'in_pending' COMMENT '记录整体状态',
  -- 通用
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `archived_at` DATETIME DEFAULT NULL COMMENT '归档时间（1年后）',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_record_no` (`record_no`),
  KEY `idx_plate_number` (`plate_number`),
  KEY `idx_post_id` (`post_id`),
  KEY `idx_operator_id` (`operator_id`),
  KEY `idx_approver_id` (`approver_id`),
  KEY `idx_status` (`status`),
  KEY `idx_approval_status` (`approval_status`),
  KEY `idx_in_time` (`in_time`),
  KEY `idx_out_time` (`out_time`),
  KEY `idx_created_at` (`created_at`),
  KEY `idx_related_record_id` (`related_record_id`),
  KEY `idx_companion_id` (`companion_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='进出记录表';

-- ============================================================
-- 4. 站内消息表
-- ============================================================
DROP TABLE IF EXISTS `messages`;
CREATE TABLE `messages` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `recipient_id` INT UNSIGNED NOT NULL COMMENT '接收人',
  `sender_id` INT UNSIGNED DEFAULT 0 COMMENT '发送人（0=系统）',
  `sender_name` VARCHAR(50) DEFAULT '系统' COMMENT '发送人姓名',
  `type` ENUM('approval_request', 'approval_result', 'system', 'announcement') NOT NULL COMMENT '消息类型',
  `title` VARCHAR(200) NOT NULL COMMENT '消息标题',
  `content` TEXT NOT NULL COMMENT '消息内容',
  `related_record_id` INT UNSIGNED DEFAULT NULL COMMENT '关联记录（点击跳转）',
  `is_read` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否已读',
  `read_at` DATETIME DEFAULT NULL COMMENT '阅读时间',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_recipient_id` (`recipient_id`),
  KEY `idx_recipient_unread` (`recipient_id`, `is_read`),
  KEY `idx_created_at` (`created_at`),
  KEY `idx_related_record_id` (`related_record_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='站内消息表';

-- ============================================================
-- 5. 定时推送配置表
-- ============================================================
DROP TABLE IF EXISTS `report_configs`;
CREATE TABLE `report_configs` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(50) NOT NULL COMMENT '配置名称',
  `frequency` ENUM('daily', 'weekly', 'monthly') NOT NULL COMMENT '推送频率',
  `run_time` TIME NOT NULL COMMENT '跑批时间，如 18:00:00',
  `run_weekday` TINYINT DEFAULT NULL COMMENT '周报星期几跑（1-7，weekly 时用）',
  `recipients` JSON NOT NULL COMMENT '收件人用户ID列表 [1, 3, 5]',
  `enabled` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否启用',
  `last_run_at` DATETIME DEFAULT NULL COMMENT '最后运行时间',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='定时推送配置表';

-- ============================================================
-- 6. 系统配置表
-- ============================================================
DROP TABLE IF EXISTS `system_configs`;
CREATE TABLE `system_configs` (
  `config_key` VARCHAR(50) NOT NULL,
  `config_value` TEXT NOT NULL,
  `description` VARCHAR(200) DEFAULT NULL,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`config_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统配置表';

-- ============================================================
-- 7. 审计日志表
-- ============================================================
DROP TABLE IF EXISTS `audit_logs`;
CREATE TABLE `audit_logs` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id` INT UNSIGNED DEFAULT NULL COMMENT '操作人（可空，系统操作）',
  `username` VARCHAR(50) DEFAULT NULL COMMENT '操作人账号（冗余）',
  `action` VARCHAR(50) NOT NULL COMMENT '操作类型：login/create_record/approve/reject/export/...',
  `target_type` VARCHAR(20) DEFAULT NULL COMMENT '对象类型：record/user/config/...',
  `target_id` INT UNSIGNED DEFAULT NULL COMMENT '对象ID',
  `details` JSON DEFAULT NULL COMMENT '操作详情',
  `ip_address` VARCHAR(50) DEFAULT NULL COMMENT '客户端IP',
  `user_agent` VARCHAR(500) DEFAULT NULL COMMENT 'UA',
  `status` ENUM('success', 'failed') NOT NULL DEFAULT 'success' COMMENT '操作结果',
  `error_message` TEXT DEFAULT NULL COMMENT '错误信息',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_action` (`action`),
  KEY `idx_target` (`target_type`, `target_id`),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='审计日志表';

-- ============================================================
-- 归档表（1 年前的数据自动迁移到此表）
-- ============================================================
DROP TABLE IF EXISTS `records_archive`;
CREATE TABLE `records_archive` (
  `id` INT UNSIGNED NOT NULL,
  `record_no` VARCHAR(30) NOT NULL,
  `plate_number` VARCHAR(20) NOT NULL,
  `vehicle_type` ENUM('internal', 'external', 'truck') NOT NULL,
  `direction` ENUM('in', 'out') NOT NULL,
  `post_id` INT UNSIGNED NOT NULL,
  `operator_id` INT UNSIGNED NOT NULL,
  `operator_name` VARCHAR(50) NOT NULL,
  `in_time` DATETIME DEFAULT NULL,
  `in_photos` JSON DEFAULT NULL,
  `in_remark` TEXT DEFAULT NULL,
  `out_time` DATETIME DEFAULT NULL,
  `out_photos` JSON DEFAULT NULL,
  `out_remark` TEXT DEFAULT NULL,
  `cargo_info` VARCHAR(500) DEFAULT NULL,
  `loading_start_at` DATETIME DEFAULT NULL,
  `loading_end_at` DATETIME DEFAULT NULL,
  `loading_duration` INT DEFAULT NULL,
  `approver_id` INT UNSIGNED DEFAULT NULL,
  `approver_name` VARCHAR(50) DEFAULT NULL,
  `approval_status` ENUM('pending', 'approved', 'rejected', 'timeout') NOT NULL,
  `approval_time` DATETIME DEFAULT NULL,
  `approval_remark` TEXT DEFAULT NULL,
  `related_record_id` INT UNSIGNED DEFAULT NULL,
  `companion_id` INT UNSIGNED DEFAULT NULL,
  `status` ENUM('in_pending','in_approved','in_rejected','in_timeout','out_pending','out_approved','out_rejected','out_timeout','completed') NOT NULL,
  `created_at` DATETIME NOT NULL,
  `updated_at` DATETIME NOT NULL,
  `archived_at` DATETIME NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_plate_number` (`plate_number`),
  KEY `idx_created_at` (`created_at`),
  KEY `idx_archived_at` (`archived_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='归档记录表';

SET FOREIGN_KEY_CHECKS = 1;

-- ============================================================
-- 种子数据
-- ============================================================

-- 岗亭
INSERT INTO `posts` (`id`, `name`, `location`, `sort_order`) VALUES
(1, '1号门', '厂区正门', 1),
(2, '2号门', '厂区侧门', 2),
(3, '仓库门', '仓库专用', 3);

-- 默认账号
-- 密码 hash 使用 __DEFAULT__ 占位，后端首次启动时自动重置为：
--   admin / admin123
--   security1 / 123456
--   supervisor1 / 123456
-- ⚠️ 首次登录后必须修改默认密码
INSERT INTO `users` (`id`, `username`, `password_hash`, `real_name`, `role`, `post_id`, `is_approver`, `phone`) VALUES
(1, 'admin',       '__DEFAULT__', '系统管理员', 'admin',      NULL, 1, '13800000000'),
(2, 'security1',   '__DEFAULT__', '张三',       'security',   1,    0, '13800000001'),
(3, 'security2',   '__DEFAULT__', '李四',       'security',   2,    0, '13800000002'),
(4, 'supervisor1', '__DEFAULT__', '王五',       'supervisor', NULL, 1, '13800000003'),
(5, 'supervisor2', '__DEFAULT__', '赵六',       'supervisor', NULL, 1, '13800000004');

-- 系统配置
INSERT INTO `system_configs` (`config_key`, `config_value`, `description`) VALUES
('archive_months', '12', '数据保留月数（1 年）'),
('approval_timeout_minutes', '30', '审批超时时间（分钟）'),
('approval_timeout_action', 'auto_approve', '超时动作：auto_approve/auto_reject'),
('watermark_format', '{time} | {post} | {operator}', '水印模板'),
('watermark_position', 'bottom_right', '水印位置：bottom_right/bottom_left'),
('photo_max_size_mb', '10', '照片最大尺寸（MB）'),
('photo_quality', '85', '照片压缩质量（1-100）'),
('login_max_attempts', '5', '登录最大失败次数'),
('login_lockout_minutes', '15', '登录锁定时间（分钟）'),
('company_name', 'YUSEI 模具注塑', '公司名称（用于报表抬头）');

-- 定时推送配置
INSERT INTO `report_configs` (`name`, `frequency`, `run_time`, `run_weekday`, `recipients`, `enabled`) VALUES
('每日日报', 'daily', '18:00:00', NULL, '[1, 4, 5]', 1),
('每周周报', 'weekly', '17:00:00', 5, '[1, 4, 5]', 1);

-- ============================================================
-- 视图：今日统计
-- ============================================================
DROP VIEW IF EXISTS `v_today_stats`;
CREATE VIEW `v_today_stats` AS
SELECT
  DATE(in_time) AS stat_date,
  COUNT(*) AS in_count,
  SUM(CASE WHEN vehicle_type = 'truck' THEN 1 ELSE 0 END) AS truck_count,
  SUM(CASE WHEN approval_status = 'pending' THEN 1 ELSE 0 END) AS pending_count
FROM records
WHERE DATE(in_time) = CURDATE() AND direction = 'in'
GROUP BY DATE(in_time);

-- ============================================================
-- 完成
-- ============================================================
SELECT '✓ 车辆管理系统数据库初始化完成' AS message;
SELECT CONCAT('✓ 共创建 ', COUNT(*), ' 张业务表') AS info FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name NOT LIKE 'v_%';
SELECT CONCAT('✓ 默认账号: admin/admin123, security1/123456, supervisor1/123456') AS accounts;
