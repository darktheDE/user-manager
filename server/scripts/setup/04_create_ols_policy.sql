-- =============================================
-- 04_create_ols_policy.sql
-- Oracle Label Security (OLS) cho PROJECTS
-- Phân loại projects theo mức bảo mật
-- =============================================

-- Kết nối với SYSTEM user (phải có LBAC_DBA role)

-- =============================================
-- 1. Tạo OLS Policy
-- =============================================
BEGIN
    -- Xóa policy cũ nếu có
    BEGIN
        SA_SYSDBA.DROP_POLICY(policy_name => 'PROJECT_SEC_POLICY', drop_column => TRUE);
    EXCEPTION
        WHEN OTHERS THEN NULL;
    END;
    
    -- Tạo policy mới
    SA_SYSDBA.CREATE_POLICY(
        policy_name => 'PROJECT_SEC_POLICY',
        column_name => 'SEC_LABEL',
        default_options => 'READ_CONTROL,WRITE_CONTROL'
    );
END;
/

-- =============================================
-- 2. Tạo các Levels (cấp độ bảo mật)
-- =============================================
BEGIN
    SA_COMPONENTS.CREATE_LEVEL(
        policy_name => 'PROJECT_SEC_POLICY',
        level_num => 10,
        short_name => 'PUB',
        long_name => 'PUBLIC'
    );
    
    SA_COMPONENTS.CREATE_LEVEL(
        policy_name => 'PROJECT_SEC_POLICY',
        level_num => 20,
        short_name => 'INT',
        long_name => 'INTERNAL'
    );
    
    SA_COMPONENTS.CREATE_LEVEL(
        policy_name => 'PROJECT_SEC_POLICY',
        level_num => 30,
        short_name => 'CONF',
        long_name => 'CONFIDENTIAL'
    );
    
    SA_COMPONENTS.CREATE_LEVEL(
        policy_name => 'PROJECT_SEC_POLICY',
        level_num => 40,
        short_name => 'SECRET',
        long_name => 'TOP_SECRET'
    );
END;
/

-- =============================================
-- 3. Tạo Labels từ Levels
-- =============================================
BEGIN
    SA_LABEL_ADMIN.CREATE_LABEL(
        policy_name => 'PROJECT_SEC_POLICY',
        label_tag => 1000,
        label_value => 'PUB'
    );
    
    SA_LABEL_ADMIN.CREATE_LABEL(
        policy_name => 'PROJECT_SEC_POLICY',
        label_tag => 2000,
        label_value => 'INT'
    );
    
    SA_LABEL_ADMIN.CREATE_LABEL(
        policy_name => 'PROJECT_SEC_POLICY',
        label_tag => 3000,
        label_value => 'CONF'
    );
    
    SA_LABEL_ADMIN.CREATE_LABEL(
        policy_name => 'PROJECT_SEC_POLICY',
        label_tag => 4000,
        label_value => 'SECRET'
    );
END;
/

-- =============================================
-- 4. Áp dụng Policy cho bảng PROJECTS
-- =============================================
BEGIN
    SA_POLICY_ADMIN.APPLY_TABLE_POLICY(
        policy_name => 'PROJECT_SEC_POLICY',
        schema_name => 'SYSTEM',
        table_name => 'PROJECTS',
        table_options => 'READ_CONTROL,WRITE_CONTROL'
    );
END;
/

-- =============================================
-- 5. Gán labels mặc định cho user
-- =============================================
-- User levels:
-- ADMIN: SECRET (có thể đọc tất cả)
-- Manager: CONFIDENTIAL
-- Staff: INTERNAL
-- Guest: PUBLIC

-- Ví dụ gán label cho user:
-- BEGIN
--     SA_USER_ADMIN.SET_USER_LABELS(
--         policy_name => 'PROJECT_SEC_POLICY',
--         user_name => 'ADMIN',
--         max_read_label => 'SECRET',
--         max_write_label => 'SECRET',
--         min_write_label => 'PUB',
--         def_label => 'SECRET',
--         row_label => 'SECRET'
--     );
-- END;
-- /

COMMIT;

-- =============================================
-- LƯU Ý: OLS cần được enable trong Oracle Database
-- Kiểm tra: SELECT * FROM V$OPTION WHERE PARAMETER = 'Oracle Label Security';
-- Nếu chưa có, chạy: @?/rdbms/admin/catols.sql
-- =============================================
