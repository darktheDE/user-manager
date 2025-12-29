-- =============================================
-- 03_create_vpd_policy.sql
-- Virtual Private Database (VPD) Policy cho PROJECTS
-- Users chỉ thấy projects của department họ thuộc về
-- =============================================

-- Kết nối với SYSTEM user

-- =============================================
-- 1. Tạo context để lưu department của user
-- =============================================
CREATE OR REPLACE CONTEXT user_dept_ctx USING set_user_dept_proc;
/

-- =============================================
-- 2. Procedure để set department context
-- =============================================
CREATE OR REPLACE PROCEDURE set_user_dept_proc (
    p_department IN VARCHAR2
) AS
BEGIN
    DBMS_SESSION.SET_CONTEXT('user_dept_ctx', 'department', p_department);
END;
/

-- =============================================
-- 3. VPD Policy Function
-- Trả về predicate để filter projects theo department
-- =============================================
CREATE OR REPLACE FUNCTION vpd_projects_policy (
    schema_name IN VARCHAR2,
    table_name IN VARCHAR2
) RETURN VARCHAR2 AS
    v_department VARCHAR2(50);
    v_user VARCHAR2(128);
BEGIN
    v_user := SYS_CONTEXT('USERENV', 'SESSION_USER');
    
    -- SYSTEM và ADMIN users có thể thấy tất cả
    IF v_user IN ('SYS', 'SYSTEM', 'ADMIN') THEN
        RETURN NULL; -- No restriction
    END IF;
    
    -- Lấy department từ context
    v_department := SYS_CONTEXT('user_dept_ctx', 'department');
    
    IF v_department IS NULL THEN
        -- Nếu không có context, chỉ thấy projects của chính mình
        RETURN 'owner_username = ''' || v_user || '''';
    ELSE
        -- Filter theo department
        RETURN 'department = ''' || v_department || ''' OR owner_username = ''' || v_user || '''';
    END IF;
END;
/

-- =============================================
-- 4. Áp dụng VPD Policy cho bảng PROJECTS
-- =============================================
BEGIN
    -- Xóa policy cũ nếu có
    BEGIN
        DBMS_RLS.DROP_POLICY(
            object_schema => 'SYSTEM',
            object_name => 'PROJECTS',
            policy_name => 'PROJECTS_VPD_POLICY'
        );
    EXCEPTION
        WHEN OTHERS THEN NULL;
    END;
    
    -- Tạo policy mới
    DBMS_RLS.ADD_POLICY(
        object_schema => 'SYSTEM',
        object_name => 'PROJECTS',
        policy_name => 'PROJECTS_VPD_POLICY',
        function_schema => 'SYSTEM',
        policy_function => 'VPD_PROJECTS_POLICY',
        statement_types => 'SELECT, UPDATE, DELETE',
        policy_type => DBMS_RLS.DYNAMIC
    );
END;
/

-- =============================================
-- 5. Cách sử dụng trong ứng dụng
-- =============================================
-- Sau khi user login, gọi procedure để set context:
-- EXEC set_user_dept_proc('IT');
-- 
-- Sau đó mọi query trên PROJECTS sẽ tự động được filter

COMMIT;

-- Kiểm tra policy đã tạo
SELECT * FROM dba_policies WHERE object_name = 'PROJECTS';
