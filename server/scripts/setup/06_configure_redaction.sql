-- 06_configure_redaction.sql
-- Cấu hình Oracle Data Redaction cho bảng USER_INFO

DECLARE
    v_policy_exists NUMBER;
BEGIN
    -- 1. Grant quyền SELECT cho APP_ADMIN để demo user view
    EXECUTE IMMEDIATE 'GRANT SELECT ON SYSTEM.USER_INFO TO APP_ADMIN';
    
    -- 2. Drop policy cũ nếu tồn tại
    SELECT COUNT(*) INTO v_policy_exists 
    FROM redaction_policies 
    WHERE policy_name = 'REDACT_USER_INFO_POLICY' 
      AND object_owner = 'SYSTEM' 
      AND object_name = 'USER_INFO';

    IF v_policy_exists > 0 THEN
        DBMS_REDACT.DROP_POLICY(
            object_schema => 'SYSTEM',
            object_name   => 'USER_INFO',
            policy_name   => 'REDACT_USER_INFO_POLICY'
        );
    END IF;

    -- 1. Tạo Policy và che cột PHONE (FULL Redaction)
    DBMS_REDACT.ADD_POLICY(
        object_schema => 'SYSTEM',
        object_name   => 'USER_INFO',
        column_name   => 'PHONE',
        policy_name   => 'REDACT_USER_INFO_POLICY',
        function_type => DBMS_REDACT.FULL,
        expression    => '1=1', 
        policy_description => 'Che số điện thoại và email của người dùng'
    );
    
    -- 2. Thêm cột EMAIL vào policy (FULL Redaction)
    DBMS_REDACT.ALTER_POLICY(
        object_schema => 'SYSTEM',
        object_name   => 'USER_INFO',
        policy_name   => 'REDACT_USER_INFO_POLICY',
        action        => DBMS_REDACT.ADD_COLUMN,
        column_name   => 'EMAIL',
        function_type => DBMS_REDACT.FULL
    );

    COMMIT;
END;
/
