-- =============================================
-- 02_create_tables.sql
-- Tạo bảng PROJECTS để demo VPD/OLS/Audit
-- =============================================

-- Kết nối với user SYSTEM hoặc user có quyền CREATE TABLE

-- =============================================
-- Bảng PROJECTS
-- =============================================
CREATE TABLE projects (
    project_id      NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_name    VARCHAR2(100) NOT NULL,
    department      VARCHAR2(50) NOT NULL,
    budget          NUMBER(15, 2) DEFAULT 0,
    status          VARCHAR2(20) DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'COMPLETED', 'CANCELLED')),
    owner_username  VARCHAR2(128) NOT NULL,  -- Oracle username của owner
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index theo department cho VPD performance
CREATE INDEX idx_projects_department ON projects(department);
CREATE INDEX idx_projects_owner ON projects(owner_username);

-- Trigger cập nhật updated_at
CREATE OR REPLACE TRIGGER trg_projects_update
BEFORE UPDATE ON projects
FOR EACH ROW
BEGIN
    :NEW.updated_at := CURRENT_TIMESTAMP;
END;
/

-- =============================================
-- Dữ liệu mẫu
-- =============================================
INSERT INTO projects (project_name, department, budget, status, owner_username) VALUES
    ('Website Redesign', 'IT', 50000, 'ACTIVE', 'ADMIN');
INSERT INTO projects (project_name, department, budget, status, owner_username) VALUES
    ('Mobile App Development', 'IT', 150000, 'ACTIVE', 'ADMIN');
INSERT INTO projects (project_name, department, budget, status, owner_username) VALUES
    ('Marketing Campaign Q1', 'MARKETING', 25000, 'COMPLETED', 'ADMIN');
INSERT INTO projects (project_name, department, budget, status, owner_username) VALUES
    ('HR System Upgrade', 'HR', 75000, 'ACTIVE', 'ADMIN');
INSERT INTO projects (project_name, department, budget, status, owner_username) VALUES
    ('Financial Audit 2024', 'FINANCE', 100000, 'ACTIVE', 'ADMIN');

COMMIT;

-- Grant quyền cho users
-- GRANT SELECT, INSERT, UPDATE, DELETE ON projects TO <username>;
