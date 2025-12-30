-- =============================================
-- 05_create_audit.sql
-- Unified Auditing và Fine-Grained Auditing (FGA) cho PROJECTS
-- Audit các thao tác trên budget và dữ liệu nhạy cảm
-- =============================================

-- Kết nối với SYSTEM user

-- =============================================
-- 1. Unified Auditing Policy cho bảng PROJECTS
-- (Thay thế Traditional Audit cho Oracle 23c+)
-- =============================================

-- Xóa policy cũ nếu có
BEGIN
    EXECUTE IMMEDIATE 'DROP AUDIT POLICY audit_projects_dml';
EXCEPTION
    WHEN OTHERS THEN NULL;
END;
/

-- Tạo unified audit policy cho DML trên PROJECTS
CREATE AUDIT POLICY audit_projects_dml
    ACTIONS SELECT, INSERT, UPDATE, DELETE ON SYSTEM.PROJECTS;

-- Enable audit policy
AUDIT POLICY audit_projects_dml;

-- =============================================
-- 1b. Unified Auditing Policy cho User Management using ACTIONS
-- Audit CREATE/ALTER/DROP USER/ROLE/PROFILE
-- =============================================
BEGIN
    EXECUTE IMMEDIATE 'DROP AUDIT POLICY audit_user_admin';
EXCEPTION
    WHEN OTHERS THEN NULL;
END;
/

CREATE AUDIT POLICY audit_user_admin
    ACTIONS CREATE USER, ALTER USER, DROP USER,
            CREATE ROLE, ALTER ROLE, DROP ROLE,
            CREATE PROFILE, ALTER PROFILE, DROP PROFILE;

AUDIT POLICY audit_user_admin;

-- =============================================
-- 2. Fine-Grained Auditing (FGA) cho cột BUDGET
-- Audit khi có ai đọc/sửa budget
-- =============================================
BEGIN
    -- Xóa policy FGA cũ nếu có
    BEGIN
        DBMS_FGA.DROP_POLICY(
            object_schema => 'SYSTEM',
            object_name => 'PROJECTS',
            policy_name => 'AUDIT_BUDGET_ACCESS'
        );
    EXCEPTION
        WHEN OTHERS THEN NULL;
    END;
    
    -- FGA cho SELECT trên cột BUDGET
    DBMS_FGA.ADD_POLICY(
        object_schema => 'SYSTEM',
        object_name => 'PROJECTS',
        policy_name => 'AUDIT_BUDGET_ACCESS',
        audit_column => 'BUDGET',
        audit_condition => NULL,
        statement_types => 'SELECT',
        audit_trail => DBMS_FGA.DB + DBMS_FGA.EXTENDED,
        audit_column_opts => DBMS_FGA.ANY_COLUMNS
    );
END;
/

BEGIN
    -- Xóa policy FGA cũ nếu có
    BEGIN
        DBMS_FGA.DROP_POLICY(
            object_schema => 'SYSTEM',
            object_name => 'PROJECTS',
            policy_name => 'AUDIT_BUDGET_UPDATE'
        );
    EXCEPTION
        WHEN OTHERS THEN NULL;
    END;
    
    -- FGA cho UPDATE trên cột BUDGET
    DBMS_FGA.ADD_POLICY(
        object_schema => 'SYSTEM',
        object_name => 'PROJECTS',
        policy_name => 'AUDIT_BUDGET_UPDATE',
        audit_column => 'BUDGET',
        audit_condition => NULL,
        statement_types => 'UPDATE',
        audit_trail => DBMS_FGA.DB + DBMS_FGA.EXTENDED,
        audit_column_opts => DBMS_FGA.ANY_COLUMNS
    );
END;
/

-- =============================================
-- 3. FGA cho các thao tác trên projects có budget cao
-- =============================================
BEGIN
    BEGIN
        DBMS_FGA.DROP_POLICY(
            object_schema => 'SYSTEM',
            object_name => 'PROJECTS',
            policy_name => 'AUDIT_HIGH_BUDGET'
        );
    EXCEPTION
        WHEN OTHERS THEN NULL;
    END;
    
    -- Audit khi truy cập projects có budget > 100,000
    DBMS_FGA.ADD_POLICY(
        object_schema => 'SYSTEM',
        object_name => 'PROJECTS',
        policy_name => 'AUDIT_HIGH_BUDGET',
        audit_column => 'BUDGET',
        audit_condition => 'BUDGET > 100000',
        statement_types => 'SELECT,UPDATE,DELETE',
        audit_trail => DBMS_FGA.DB + DBMS_FGA.EXTENDED,
        audit_column_opts => DBMS_FGA.ANY_COLUMNS
    );
END;
/

COMMIT;

-- =============================================
-- 4. Kiểm tra các FGA policies đã tạo
-- =============================================
SELECT policy_name, object_name, policy_column, policy_text
FROM dba_audit_policies
WHERE object_name = 'PROJECTS';

-- Kiểm tra Unified Audit Policies
SELECT policy_name, enabled_option, audit_option
FROM audit_unified_policies
WHERE policy_name = 'AUDIT_PROJECTS_DML';
