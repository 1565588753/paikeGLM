-- ============================================================
-- 智能排课系统 - 数据库初始化脚本
-- 兼容 MySQL 5.7+
-- ============================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- -----------------------------------------------------------
-- 用户表
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE COMMENT '工号',
    password_hash VARCHAR(255) NOT NULL,
    real_name VARCHAR(50) NOT NULL COMMENT '姓名',
    gender ENUM('male', 'female') DEFAULT 'male',
    phone VARCHAR(20) COMMENT '联系电话',
    role ENUM('admin', 'teacher') NOT NULL DEFAULT 'teacher',
    title VARCHAR(50) COMMENT '职称',
    subject_group VARCHAR(50) COMMENT '学科组',
    max_weekly_hours INT DEFAULT 20 COMMENT '每周最大课时',
    is_active TINYINT(1) DEFAULT 1,
    last_login_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_role (role),
    INDEX idx_subject_group (subject_group)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- -----------------------------------------------------------
-- 学年表
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS academic_years (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE COMMENT '学年名称如2024-2025',
    status ENUM('active', 'archived', 'pending') DEFAULT 'pending',
    is_current TINYINT(1) DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_status (status),
    INDEX idx_is_current (is_current)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学年表';

-- -----------------------------------------------------------
-- 学期表
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS semesters (
    id INT AUTO_INCREMENT PRIMARY KEY,
    academic_year_id INT NOT NULL,
    name VARCHAR(50) NOT NULL COMMENT '上学期/下学期',
    start_date DATE,
    end_date DATE,
    is_current TINYINT(1) DEFAULT 0,
    status ENUM('active', 'archived', 'pending') DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (academic_year_id) REFERENCES academic_years(id),
    UNIQUE KEY uk_year_semester (academic_year_id, name),
    INDEX idx_is_current (is_current)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学期表';

-- -----------------------------------------------------------
-- 年级表
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS grades (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL COMMENT '年级名称如高一',
    level INT NOT NULL COMMENT '年级层级1-12',
    academic_year_id INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (academic_year_id) REFERENCES academic_years(id),
    UNIQUE KEY uk_year_level (academic_year_id, level),
    INDEX idx_level (level)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='年级表';

-- -----------------------------------------------------------
-- 班级表
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS class_groups (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL COMMENT '班级名称',
    short_name VARCHAR(20) COMMENT '简称',
    grade_id INT NOT NULL,
    student_count INT DEFAULT 0,
    head_teacher_id INT COMMENT '班主任',
    class_type ENUM('普通班', '实验班', '特长班') DEFAULT '普通班',
    academic_year_id INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (grade_id) REFERENCES grades(id),
    FOREIGN KEY (head_teacher_id) REFERENCES users(id),
    FOREIGN KEY (academic_year_id) REFERENCES academic_years(id),
    INDEX idx_grade (grade_id),
    INDEX idx_academic_year (academic_year_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='班级表';

-- -----------------------------------------------------------
-- 科目表
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS subjects (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL COMMENT '科目名称',
    short_name VARCHAR(20) COMMENT '简称',
    subject_type ENUM('主科', '副科', '活动课') DEFAULT '副科',
    priority INT DEFAULT 5 COMMENT '优先级1-10',
    allow_consecutive TINYINT(1) DEFAULT 0 COMMENT '是否允许连堂',
    max_consecutive INT DEFAULT 1 COMMENT '最大连续节数',
    needs_special_room TINYINT(1) DEFAULT 0 COMMENT '是否需要特殊教室',
    max_per_day INT DEFAULT 2 COMMENT '每天最多节数',
    max_per_week INT DEFAULT 10 COMMENT '每周最多节数',
    supports_odd_even TINYINT(1) DEFAULT 0 COMMENT '是否支持单双周',
    academic_year_id INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (academic_year_id) REFERENCES academic_years(id),
    INDEX idx_type (subject_type),
    INDEX idx_academic_year (academic_year_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='科目表';

-- -----------------------------------------------------------
-- 教室表
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS classrooms (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL COMMENT '教室名称',
    room_type ENUM('普通教室', '多媒体教室', '实验室', '音乐室', '美术室', '体育馆', '其他') DEFAULT '普通教室',
    capacity INT DEFAULT 50,
    location VARCHAR(200) COMMENT '位置',
    equipment TEXT COMMENT '设备(JSON)',
    academic_year_id INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (academic_year_id) REFERENCES academic_years(id),
    INDEX idx_type (room_type),
    INDEX idx_academic_year (academic_year_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='教室表';

-- -----------------------------------------------------------
-- 作息时间模板表
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS schedule_templates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL COMMENT '模板名称',
    grade_id INT COMMENT '关联年级,NULL表示全校默认',
    academic_year_id INT NOT NULL,
    days_per_week INT DEFAULT 5 COMMENT '每周上课天数',
    is_default TINYINT(1) DEFAULT 0 COMMENT '是否默认模板',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (grade_id) REFERENCES grades(id),
    FOREIGN KEY (academic_year_id) REFERENCES academic_years(id),
    INDEX idx_grade (grade_id),
    INDEX idx_academic_year (academic_year_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='作息时间模板';

-- -----------------------------------------------------------
-- 时间段表
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS time_slots (
    id INT AUTO_INCREMENT PRIMARY KEY,
    schedule_template_id INT NOT NULL,
    day_of_week TINYINT NOT NULL COMMENT '星期1-7',
    period_number TINYINT NOT NULL COMMENT '节次',
    start_time TIME NOT NULL COMMENT '开始时间',
    end_time TIME NOT NULL COMMENT '结束时间',
    period_type ENUM('上课', '课间操', '眼保健操', '午休', '晚自习') DEFAULT '上课',
    label VARCHAR(50) COMMENT '标签如"第一节"',
    is_morning TINYINT(1) DEFAULT 0,
    is_afternoon TINYINT(1) DEFAULT 0,
    is_evening TINYINT(1) DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (schedule_template_id) REFERENCES schedule_templates(id),
    INDEX idx_template_day (schedule_template_id, day_of_week),
    INDEX idx_template_day_period (schedule_template_id, day_of_week, period_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='时间段表';

-- -----------------------------------------------------------
-- 任课安排表
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS teaching_assignments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    class_group_id INT NOT NULL,
    subject_id INT NOT NULL,
    teacher_id INT NOT NULL,
    weekly_hours INT NOT NULL DEFAULT 1 COMMENT '周课时数',
    odd_even_type ENUM('all', 'odd', 'even') DEFAULT 'all' COMMENT '单双周类型',
    academic_year_id INT NOT NULL,
    semester_id INT NOT NULL,
    is_combined_class TINYINT(1) DEFAULT 0 COMMENT '是否合班课',
    combined_class_ids JSON COMMENT '合班班级ID列表',
    notes TEXT COMMENT '备注',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (class_group_id) REFERENCES class_groups(id),
    FOREIGN KEY (subject_id) REFERENCES subjects(id),
    FOREIGN KEY (teacher_id) REFERENCES users(id),
    FOREIGN KEY (academic_year_id) REFERENCES academic_years(id),
    FOREIGN KEY (semester_id) REFERENCES semesters(id),
    INDEX idx_class (class_group_id),
    INDEX idx_teacher (teacher_id),
    INDEX idx_subject (subject_id),
    INDEX idx_semester (semester_id),
    INDEX idx_odd_even (odd_even_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='任课安排表';

-- -----------------------------------------------------------
-- 预排课程表
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS pre_scheduled_courses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    teaching_assignment_id INT NOT NULL,
    day_of_week TINYINT NOT NULL,
    period_number TINYINT NOT NULL,
    schedule_template_id INT NOT NULL,
    odd_even_type ENUM('all', 'odd', 'even') DEFAULT 'all',
    academic_year_id INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (teaching_assignment_id) REFERENCES teaching_assignments(id),
    FOREIGN KEY (schedule_template_id) REFERENCES schedule_templates(id),
    FOREIGN KEY (academic_year_id) REFERENCES academic_years(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='预排课程表';

-- -----------------------------------------------------------
-- 排课方案表
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS schedule_plans (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL COMMENT '方案名称',
    academic_year_id INT NOT NULL,
    semester_id INT NOT NULL,
    status ENUM('draft', 'published') DEFAULT 'draft',
    is_active TINYINT(1) DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (academic_year_id) REFERENCES academic_years(id),
    FOREIGN KEY (semester_id) REFERENCES semesters(id),
    INDEX idx_status (status),
    INDEX idx_semester (semester_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='排课方案表';

-- -----------------------------------------------------------
-- 课表条目表（核心表）
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS timetable_entries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    schedule_plan_id INT NOT NULL,
    teaching_assignment_id INT NOT NULL,
    class_group_id INT NOT NULL,
    subject_id INT NOT NULL,
    teacher_id INT NOT NULL,
    classroom_id INT COMMENT '教室ID',
    day_of_week TINYINT NOT NULL COMMENT '星期1-7',
    period_number TINYINT NOT NULL COMMENT '节次',
    schedule_template_id INT NOT NULL COMMENT '关联作息模板',
    start_time TIME NOT NULL COMMENT '实际开始时间(冗余存储加速冲突检测)',
    end_time TIME NOT NULL COMMENT '实际结束时间',
    odd_even_type ENUM('all', 'odd', 'even') DEFAULT 'all' COMMENT '单双周类型',
    is_locked TINYINT(1) DEFAULT 0 COMMENT '是否锁定',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (schedule_plan_id) REFERENCES schedule_plans(id),
    FOREIGN KEY (teaching_assignment_id) REFERENCES teaching_assignments(id),
    FOREIGN KEY (class_group_id) REFERENCES class_groups(id),
    FOREIGN KEY (subject_id) REFERENCES subjects(id),
    FOREIGN KEY (teacher_id) REFERENCES users(id),
    FOREIGN KEY (classroom_id) REFERENCES classrooms(id),
    FOREIGN KEY (schedule_template_id) REFERENCES schedule_templates(id),
    INDEX idx_plan (schedule_plan_id),
    INDEX idx_class_day (class_group_id, day_of_week),
    INDEX idx_teacher_day (teacher_id, day_of_week),
    INDEX idx_classroom_day (classroom_id, day_of_week),
    INDEX idx_time (day_of_week, start_time, end_time),
    INDEX idx_odd_even (odd_even_type),
    INDEX idx_teacher_day_time (teacher_id, day_of_week, start_time, end_time),
    INDEX idx_class_day_time (class_group_id, day_of_week, start_time, end_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='课表条目表(核心)';

-- -----------------------------------------------------------
-- 换课申请表
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS course_swap_requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    requester_id INT NOT NULL,
    target_id INT NOT NULL,
    requester_entry_id INT NOT NULL,
    target_entry_id INT COMMENT '目标课表条目ID(换课时)',
    target_day TINYINT COMMENT '目标星期(调课时)',
    target_period TINYINT COMMENT '目标节次(调课时)',
    target_template_id INT COMMENT '目标作息模板ID',
    swap_type ENUM('swap', 'move') DEFAULT 'swap' COMMENT '换课/调课',
    reason TEXT COMMENT '换课原因',
    status ENUM('pending', 'approved', 'rejected', 'cancelled') DEFAULT 'pending',
    responder_reason TEXT COMMENT '回复原因',
    academic_year_id INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    resolved_at DATETIME,
    FOREIGN KEY (requester_id) REFERENCES users(id),
    FOREIGN KEY (target_id) REFERENCES users(id),
    FOREIGN KEY (requester_entry_id) REFERENCES timetable_entries(id),
    FOREIGN KEY (target_entry_id) REFERENCES timetable_entries(id),
    FOREIGN KEY (academic_year_id) REFERENCES academic_years(id),
    INDEX idx_requester (requester_id),
    INDEX idx_target (target_id),
    INDEX idx_status (status),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='换课申请表';

-- -----------------------------------------------------------
-- 通知表
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    type ENUM('swap_request', 'swap_result', 'schedule_published', 'year_switch', 'staff_update', 'system') DEFAULT 'system',
    title VARCHAR(200) NOT NULL,
    content TEXT,
    is_read TINYINT(1) DEFAULT 0,
    related_id INT COMMENT '关联ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX idx_user_read (user_id, is_read),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='通知表';

-- -----------------------------------------------------------
-- 人事表
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS staff_table_entries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    grade_id INT NOT NULL,
    class_group_id INT NOT NULL,
    subject_id INT NOT NULL,
    teacher_id INT NOT NULL,
    weekly_hours INT NOT NULL DEFAULT 1,
    odd_even_type ENUM('all', 'odd', 'even') DEFAULT 'all',
    notes TEXT,
    academic_year_id INT NOT NULL,
    semester_id INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (grade_id) REFERENCES grades(id),
    FOREIGN KEY (class_group_id) REFERENCES class_groups(id),
    FOREIGN KEY (subject_id) REFERENCES subjects(id),
    FOREIGN KEY (teacher_id) REFERENCES users(id),
    FOREIGN KEY (academic_year_id) REFERENCES academic_years(id),
    FOREIGN KEY (semester_id) REFERENCES semesters(id),
    INDEX idx_grade (grade_id),
    INDEX idx_class (class_group_id),
    INDEX idx_teacher (teacher_id),
    INDEX idx_semester (semester_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='人事表';

-- -----------------------------------------------------------
-- 操作日志表
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS operation_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    action VARCHAR(100) NOT NULL COMMENT '操作类型',
    target_type VARCHAR(50) COMMENT '目标类型',
    target_id INT COMMENT '目标ID',
    detail TEXT COMMENT '操作详情',
    ip_address VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX idx_user (user_id),
    INDEX idx_action (action),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='操作日志表';

-- -----------------------------------------------------------
-- 备份记录表
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS backup_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size BIGINT DEFAULT 0,
    backup_type ENUM('manual', 'auto') DEFAULT 'manual',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_type (backup_type),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='备份记录表';

-- -----------------------------------------------------------
-- 语数外匹配小课表
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS subject_sub_mappings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    subject_id INT NOT NULL COMMENT '主科ID(语数外)',
    sub_subject_id INT NOT NULL COMMENT '小课ID(综合实践/劳动/校本/自习)',
    academic_year_id INT NOT NULL,
    enabled TINYINT(1) DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subject_id) REFERENCES subjects(id),
    FOREIGN KEY (sub_subject_id) REFERENCES subjects(id),
    FOREIGN KEY (academic_year_id) REFERENCES academic_years(id),
    UNIQUE KEY uk_mapping (subject_id, sub_subject_id, academic_year_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='语数外匹配小课表';

-- -----------------------------------------------------------
-- 教师不可授课时间表
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS teacher_unavailable_times (
    id INT AUTO_INCREMENT PRIMARY KEY,
    teacher_id INT NOT NULL,
    day_of_week TINYINT NOT NULL,
    period_number TINYINT,
    start_time TIME,
    end_time TIME,
    reason VARCHAR(200) COMMENT '原因(开会/教研/病假等)',
    academic_year_id INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (teacher_id) REFERENCES users(id),
    FOREIGN KEY (academic_year_id) REFERENCES academic_years(id),
    INDEX idx_teacher (teacher_id),
    INDEX idx_day (day_of_week)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='教师不可授课时间表';

-- -----------------------------------------------------------
-- 年级科目课时设置表
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS grade_subject_hours (
    id INT AUTO_INCREMENT PRIMARY KEY,
    grade_id INT NOT NULL,
    subject_id INT NOT NULL,
    weekly_hours INT NOT NULL DEFAULT 1 COMMENT '每周标准课时',
    academic_year_id INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (grade_id) REFERENCES grades(id),
    FOREIGN KEY (subject_id) REFERENCES subjects(id),
    FOREIGN KEY (academic_year_id) REFERENCES academic_years(id),
    UNIQUE KEY uk_grade_subject (grade_id, subject_id, academic_year_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='年级科目课时设置表';

SET FOREIGN_KEY_CHECKS = 1;
