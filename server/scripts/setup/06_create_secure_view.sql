-- =============================================
-- 06_create_secure_view.sql
-- View che giấu dữ liệu nhạy cảm (thay thế OLS)
-- =============================================

-- Tạo context để lưu thông tin user
CREATE OR REPLACE CONTEXT MY_SEC_CTX USING set_user_context ACCESSED GLOBALLY;
/

-- Procedure để set context
CREATE OR REPLACE PROCEDURE set_user_context(
    p_user_role VARCHAR2 DEFAULT NULL
) AS
BEGIN
    DBMS_SESSION.SET_CONTEXT('MY_SEC_CTX', 'USER_ROLE', NVL(p_user_role, 'STAFF'));
    DBMS_SESSION.SET_CONTEXT('MY_SEC_CTX', 'USERNAME', SYS_CONTEXT('USERENV', 'SESSION_USER'));
END;
/

GRANT EXECUTE ON set_user_context TO PUBLIC;
/

-- =============================================
-- View PROJECTS_SECURE
-- Ẩn BUDGET với user không có quyền xem
-- =============================================
CREATE OR REPLACE VIEW projects_secure AS
SELECT 
    project_id,
    project_name,
    department,
    -- Chỉ ADMIN, SYSTEM, hoặc user có role MANAGER mới thấy BUDGET
    CASE 
        WHEN SYS_CONTEXT('USERENV', 'SESSION_USER') IN ('SYS', 'SYSTEM', 'ADMIN') THEN budget
        WHEN SYS_CONTEXT('MY_SEC_CTX', 'USER_ROLE') = 'MANAGER' THEN budget
        ELSE NULL  -- Ẩn budget với nhân viên thường
    END AS budget,
    -- Hiển thị dấu hiệu dữ liệu bị ẩn
    CASE 
        WHEN SYS_CONTEXT('USERENV', 'SESSION_USER') IN ('SYS', 'SYSTEM', 'ADMIN') THEN 'FULL'
        WHEN SYS_CONTEXT('MY_SEC_CTX', 'USER_ROLE') = 'MANAGER' THEN 'FULL'
        ELSE 'RESTRICTED'
    END AS access_level,
    status,
    owner_username,
    created_at,
    updated_at
FROM projects;
/

-- Grant SELECT on secure view to all users
GRANT SELECT ON projects_secure TO PUBLIC;
/

-- =============================================
-- Test:
-- 1. Login với user thường: BUDGET hiển thị NULL
-- 2. Login với ADMIN/SYSTEM: Thấy BUDGET đầy đủ
-- 3. Set role MANAGER: EXEC set_user_context('MANAGER'); 
--    => Thấy BUDGET
-- =============================================

-- Cột CONFIDENTIAL_DATA demo (optional)
-- Nếu muốn thêm cột mật, có thể dùng logic tương tự

COMMIT;
