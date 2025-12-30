-- =============================================
-- 02_create_tables.sql
-- Tạo bảng PROJECTS và USER_INFO
-- PASSWORD sẽ được hash bằng Python script (bcrypt)
-- =============================================

-- =============================================
-- Bảng USER_INFO (lưu password đã hash bằng bcrypt)
-- =============================================
CREATE TABLE user_info (
    user_id         NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username        VARCHAR2(128) NOT NULL UNIQUE,
    password_hash   VARCHAR2(255) NOT NULL,
    full_name       VARCHAR2(200),
    email           VARCHAR2(200),
    phone           VARCHAR2(20),
    address         VARCHAR2(500),
    department      VARCHAR2(50),
    notes           VARCHAR2(1000),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_user_info_username ON user_info(username);

CREATE OR REPLACE TRIGGER trg_user_info_update
BEFORE UPDATE ON user_info
FOR EACH ROW
BEGIN
    :NEW.updated_at := CURRENT_TIMESTAMP;
END;
/

-- =============================================
-- Bảng PROJECTS
-- =============================================
CREATE TABLE projects (
    project_id      NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_name    VARCHAR2(100) NOT NULL,
    department      VARCHAR2(50) NOT NULL,
    budget          NUMBER(15, 2) DEFAULT 0,
    status          VARCHAR2(20) DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'COMPLETED', 'CANCELLED')),
    owner_username  VARCHAR2(128) NOT NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_projects_department ON projects(department);
CREATE INDEX idx_projects_owner ON projects(owner_username);

CREATE OR REPLACE TRIGGER trg_projects_update
BEFORE UPDATE ON projects
FOR EACH ROW
BEGIN
    :NEW.updated_at := CURRENT_TIMESTAMP;
END;
/

COMMIT;

-- =============================================
-- DỮ LIỆU MẪU: Chạy Python script: seed_database.py
-- =============================================
