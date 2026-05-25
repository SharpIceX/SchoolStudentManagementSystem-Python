-- 新建表
CREATE TABLE IF NOT EXISTS students (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,                                   -- 内部自增 ID
    student_id    TEXT NOT NULL UNIQUE,                                                -- 学号（不允许重复）
    name          TEXT NOT NULL,                                                       -- 学生名字
    sex           TEXT CHECK(sex IN ('男', '女')) NOT NULL,                             -- 性别
    birth_date    TEXT,                                                                -- 出生日期
    college       TEXT,                                                                -- 所属院系
    class         TEXT,                                                                -- 所在班级
    phone_number  TEXT UNIQUE,                                                         -- 手机号（不允许重复）
    status        TEXT CHECK(status IN ('在读', '休学', '毕业', '退学')) DEFAULT '在读',   -- 学生在校状态
    created_time  TEXT DEFAULT CURRENT_TIMESTAMP,                                      -- 字段创建时间
    updated_time  TEXT DEFAULT CURRENT_TIMESTAMP                                       -- 字段最后更新时间
);

-- 建立索引
CREATE INDEX IF NOT EXISTS idx_students_name ON students(name);                        -- 针对「按名字模糊搜索」
CREATE INDEX IF NOT EXISTS idx_students_class ON students(class);                      -- 针对「按班级筛选学生列表」

-- 自动更新 `updated_time` 字段
CREATE TRIGGER IF NOT EXISTS update_students_time
AFTER UPDATE ON students
BEGIN
    UPDATE students SET updated_time = CURRENT_TIMESTAMP WHERE id = old.id;
END;
