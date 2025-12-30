-- =============================================
-- 03_create_vpd_policy.sql
-- Virtual Private Database (VPD) Policy cho PROJECTS
-- Users chỉ thấy projects của mình (hoặc cùng department)
-- =============================================

-- Kết nối với SYSTEM user

-- =============================================
-- 1. Tạo context để lưu APP USER (user đăng nhập từ ứng dụng)
-- =============================================
CREATE OR REPLACE CONTEXT app_user_ctx USING set_app_user_proc;
/

-- =============================================
-- 2. Procedure để set app user context
-- Gọi procedure này sau khi user đăng nhập vào ứng dụng
-- =============================================
CREATE OR REPLACE PROCEDURE set_app_user_proc (
    p_username IN VARCHAR2
) AS
BEGIN
    DBMS_SESSION.SET_CONTEXT('app_user_ctx', 'current_user', UPPER(p_username));
END;
/

-- Grant execute cho tất cả users
GRANT EXECUTE ON set_app_user_proc TO PUBLIC;

-- =============================================
-- 3. Context cho department (legacy - vẫn giữ cho tương thích)
-- =============================================
CREATE OR REPLACE CONTEXT user_dept_ctx USING set_user_dept_proc;
/

CREATE OR REPLACE PROCEDURE set_user_dept_proc (
    p_department IN VARCHAR2
) AS
BEGIN
    DBMS_SESSION.SET_CONTEXT('user_dept_ctx', 'department', p_department);
END;
/

GRANT EXECUTE ON set_user_dept_proc TO PUBLIC;

-- =============================================
-- 4. VPD Policy Function
-- Kiểm tra app_user_ctx trước, sau đó mới SESSION_USER
-- =============================================
CREATE OR REPLACE FUNCTION vpd_projects_policy (
    schema_name IN VARCHAR2,
    table_name IN VARCHAR2
) RETURN VARCHAR2 AS
    v_app_user VARCHAR2(128);
    v_session_user VARCHAR2(128);
    v_department VARCHAR2(50);
BEGIN
    -- Lấy app user từ application context
    v_app_user := SYS_CONTEXT('app_user_ctx', 'current_user');
    v_session_user := SYS_CONTEXT('USERENV', 'SESSION_USER');
    
    -- Nếu có app user trong context, dùng nó để filter
    IF v_app_user IS NOT NULL THEN
        -- ADMIN và SYSTEM có thể thấy tất cả
        IF v_app_user IN ('ADMIN', 'SYSTEM') THEN
            RETURN NULL; -- No restriction
        END IF;
        
        -- Lấy department từ context (nếu có)
        v_department := SYS_CONTEXT('user_dept_ctx', 'department');
        
        IF v_department IS NOT NULL THEN
            -- Filter theo department HOẶC owner
            RETURN 'department = ''' || v_department || ''' OR owner_username = ''' || v_app_user || '''';
        ELSE
            -- Chỉ thấy projects của mình
            RETURN 'owner_username = ''' || v_app_user || '''';
        END IF;
    END IF;
    
    -- Fallback: Nếu không có app context
    -- Cho phép SYS/SYSTEM truy cập (dùng cho maintenance)
    IF v_session_user IN ('SYS', 'SYSTEM') THEN
        RETURN NULL;
    END IF;
    
    -- Mặc định: chỉ thấy projects của session user
    RETURN 'owner_username = ''' || v_session_user || '''';
END;
/

-- =============================================
-- 5. Áp dụng VPD Policy cho bảng PROJECTS
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

COMMIT;

-- Kiểm tra policy đã tạo
SELECT * FROM dba_policies WHERE object_name = 'PROJECTS';

-- =============================================
-- Hướng dẫn sử dụng trong ứng dụng:
-- =============================================
-- 1. Sau khi user đăng nhập, gọi:
--    EXEC set_app_user_proc('HR_USER');
--
-- 2. (Tùy chọn) Set department context:
--    EXEC set_user_dept_proc('HR');
--
-- 3. Sau đó mọi query trên PROJECTS sẽ tự động được filter
--    theo owner_username = app_user
-- =============================================
