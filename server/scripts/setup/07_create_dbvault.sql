-- =============================================
-- 07_create_dbvault.sql
-- Database Vault Configuration (thay thế OLS)
-- =============================================
-- LƯU Ý: Database Vault cần được enable trước khi chạy script này
-- Kiểm tra: SELECT * FROM V$OPTION WHERE PARAMETER = 'Oracle Database Vault';
-- =============================================

-- =============================================
-- BƯỚC 1: Kiểm tra Database Vault đã được cài đặt
-- =============================================
-- Nếu chưa có DVSYS schema, cần cài đặt Database Vault trước

-- Kiểm tra DV status
SELECT * FROM DBA_DV_STATUS;

-- =============================================
-- BƯỚC 2: Tạo Realm bảo vệ bảng PROJECTS
-- =============================================
-- Realm: Vùng bảo vệ - ngăn chặn truy cập trái phép

BEGIN
    -- Xóa realm cũ nếu có
    BEGIN
        DVSYS.DBMS_MACADM.DELETE_REALM(realm_name => 'PROJECT_SECURITY_REALM');
    EXCEPTION
        WHEN OTHERS THEN NULL;
    END;
    
    -- Tạo Realm mới
    DVSYS.DBMS_MACADM.CREATE_REALM(
        realm_name    => 'PROJECT_SECURITY_REALM',
        description   => 'Bảo vệ bảng PROJECTS - chỉ user được ủy quyền mới access được',
        enabled       => DVSYS.DBMS_MACUTL.G_YES,
        audit_options => DVSYS.DBMS_MACUTL.G_REALM_AUDIT_FAIL
    );
    
    DBMS_OUTPUT.PUT_LINE('✓ Realm PROJECT_SECURITY_REALM đã được tạo');
END;
/

-- =============================================
-- BƯỚC 3: Thêm đối tượng vào Realm
-- =============================================
BEGIN
    -- Thêm bảng PROJECTS vào realm
    DVSYS.DBMS_MACADM.ADD_OBJECT_TO_REALM(
        realm_name   => 'PROJECT_SECURITY_REALM',
        object_owner => 'SYSTEM',
        object_name  => 'PROJECTS',
        object_type  => 'TABLE'
    );
    
    -- Thêm bảng USER_INFO vào realm (bảo vệ thông tin user)
    DVSYS.DBMS_MACADM.ADD_OBJECT_TO_REALM(
        realm_name   => 'PROJECT_SECURITY_REALM',
        object_owner => 'SYSTEM',
        object_name  => 'USER_INFO',
        object_type  => 'TABLE'
    );
    
    DBMS_OUTPUT.PUT_LINE('✓ Đã thêm PROJECTS và USER_INFO vào realm');
END;
/

-- =============================================
-- BƯỚC 4: Ủy quyền cho các user được phép truy cập
-- =============================================
BEGIN
    -- ADMIN được full access
    DVSYS.DBMS_MACADM.ADD_AUTH_TO_REALM(
        realm_name  => 'PROJECT_SECURITY_REALM',
        grantee     => 'ADMIN',
        rule_set_name => NULL,
        auth_options => DVSYS.DBMS_MACUTL.G_REALM_AUTH_OWNER
    );
    
    -- SYSTEM cũng được access
    DVSYS.DBMS_MACADM.ADD_AUTH_TO_REALM(
        realm_name  => 'PROJECT_SECURITY_REALM',
        grantee     => 'SYSTEM',
        rule_set_name => NULL,
        auth_options => DVSYS.DBMS_MACUTL.G_REALM_AUTH_OWNER
    );
    
    DBMS_OUTPUT.PUT_LINE('✓ Đã ủy quyền cho ADMIN và SYSTEM');
END;
/

-- =============================================
-- BƯỚC 5: Tạo Command Rule (hạn chế UPDATE BUDGET)
-- =============================================
-- Command Rule: Quy tắc kiểm soát các lệnh SQL

-- Tạo Rule Set trước
BEGIN
    BEGIN
        DVSYS.DBMS_MACADM.DELETE_RULE_SET(rule_set_name => 'BUDGET_UPDATE_RULESET');
    EXCEPTION
        WHEN OTHERS THEN NULL;
    END;
    
    DVSYS.DBMS_MACADM.CREATE_RULE_SET(
        rule_set_name    => 'BUDGET_UPDATE_RULESET',
        description      => 'Kiểm soát UPDATE trên BUDGET',
        enabled          => DVSYS.DBMS_MACUTL.G_YES,
        eval_options     => DVSYS.DBMS_MACUTL.G_RULESET_EVAL_ALL,
        audit_options    => DVSYS.DBMS_MACUTL.G_RULESET_AUDIT_FAIL,
        fail_options     => DVSYS.DBMS_MACUTL.G_RULESET_FAIL_SHOW,
        fail_message     => 'Bạn không có quyền cập nhật ngân sách dự án!',
        fail_code        => -20001,
        handler_options  => DVSYS.DBMS_MACUTL.G_RULESET_HANDLER_OFF
    );
    
    DBMS_OUTPUT.PUT_LINE('✓ Đã tạo BUDGET_UPDATE_RULESET');
END;
/

-- Tạo Rule
BEGIN
    BEGIN
        DVSYS.DBMS_MACADM.DELETE_RULE(rule_name => 'ALLOW_BUDGET_UPDATE');
    EXCEPTION
        WHEN OTHERS THEN NULL;
    END;
    
    -- Rule: Chỉ ADMIN hoặc user có role FINANCE_ROLE mới được UPDATE
    DVSYS.DBMS_MACADM.CREATE_RULE(
        rule_name  => 'ALLOW_BUDGET_UPDATE',
        rule_expr  => 'SYS_CONTEXT(''USERENV'', ''SESSION_USER'') IN (''ADMIN'', ''SYSTEM'') OR
                       DVSYS.DBMS_MACUTL.USER_HAS_ROLE(''FINANCE_ROLE'', SYS_CONTEXT(''USERENV'', ''SESSION_USER'')) = ''Y'''
    );
    
    -- Thêm rule vào ruleset
    DVSYS.DBMS_MACADM.ADD_RULE_TO_RULE_SET(
        rule_set_name => 'BUDGET_UPDATE_RULESET',
        rule_name     => 'ALLOW_BUDGET_UPDATE'
    );
    
    DBMS_OUTPUT.PUT_LINE('✓ Đã tạo rule ALLOW_BUDGET_UPDATE');
END;
/

-- =============================================
-- BƯỚC 6: Tạo Command Rule cho UPDATE trên PROJECTS
-- =============================================
BEGIN
    BEGIN
        DVSYS.DBMS_MACADM.DELETE_COMMAND_RULE(
            command      => 'UPDATE',
            object_owner => 'SYSTEM',
            object_name  => 'PROJECTS'
        );
    EXCEPTION
        WHEN OTHERS THEN NULL;
    END;
    
    DVSYS.DBMS_MACADM.CREATE_COMMAND_RULE(
        command         => 'UPDATE',
        rule_set_name   => 'BUDGET_UPDATE_RULESET',
        object_owner    => 'SYSTEM',
        object_name     => 'PROJECTS',
        enabled         => DVSYS.DBMS_MACUTL.G_YES
    );
    
    DBMS_OUTPUT.PUT_LINE('✓ Đã tạo command rule cho UPDATE PROJECTS');
END;
/

-- =============================================
-- VERIFICATION QUERIES
-- =============================================
-- Xem danh sách Realms
SELECT * FROM DVSYS.DBA_DV_REALM;

-- Xem objects trong realm
SELECT * FROM DVSYS.DBA_DV_REALM_OBJECT WHERE REALM_NAME = 'PROJECT_SECURITY_REALM';

-- Xem authorizations
SELECT * FROM DVSYS.DBA_DV_REALM_AUTH WHERE REALM_NAME = 'PROJECT_SECURITY_REALM';

-- Xem command rules
SELECT * FROM DVSYS.DBA_DV_COMMAND_RULE WHERE OBJECT_NAME = 'PROJECTS';

COMMIT;

-- =============================================
-- DEMO:
-- 1. Login với user không được ủy quyền
-- 2. Thử SELECT * FROM PROJECTS → Bị chặn
-- 3. Login với ADMIN → Access bình thường
-- 4. Thử UPDATE PROJECTS SET BUDGET = 999 → Bị chặn nếu không có FINANCE_ROLE
-- =============================================
