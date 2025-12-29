-- Oracle Database Initialization Script
-- Script này chạy thủ công sau khi Oracle container đã khởi động
-- Chạy lệnh: docker exec -i oracle-db-23ai sqlplus system/oracle123@FREEPDB1 < scripts/setup/01_create_users.sql

-- Tạo tablespace cho ứng dụng (nếu cần)
-- CREATE TABLESPACE users_data
--   DATAFILE 'users_data01.dbf' SIZE 100M
--   AUTOEXTEND ON NEXT 10M MAXSIZE 1G;

-- Tạo user cho ứng dụng
CREATE USER app_admin IDENTIFIED BY "app_admin123";

-- Cấp quota cho user
ALTER USER app_admin QUOTA UNLIMITED ON USERS;

-- Cấp các quyền cần thiết
GRANT CONNECT, RESOURCE TO app_admin;
GRANT CREATE SESSION TO app_admin;
GRANT CREATE TABLE TO app_admin;
GRANT CREATE VIEW TO app_admin;
GRANT CREATE PROCEDURE TO app_admin;

-- Cấp quyền SELECT trên các DBA views (cần thiết cho authentication module)
-- Lưu ý: Để query DBA_USERS, cần có quyền SELECT_CATALOG_ROLE hoặc DBA role
-- User SYSTEM đã có quyền này, nhưng nếu muốn dùng app_admin thì cần grant:
-- GRANT SELECT_CATALOG_ROLE TO app_admin;
-- Hoặc grant trực tiếp:
-- GRANT SELECT ON SYS.DBA_USERS TO app_admin;
-- GRANT SELECT ON SYS.DBA_SYS_PRIVS TO app_admin;
-- GRANT SELECT ON SYS.DBA_ROLE_PRIVS TO app_admin;
-- GRANT SELECT ON SYS.DBA_PROFILES TO app_admin;
-- GRANT SELECT ON SYS.DBA_ROLES TO app_admin;
-- GRANT SELECT ON SYS.DBA_TAB_PRIVS TO app_admin;
-- GRANT SELECT ON SYS.DBA_FGA_AUDIT_TRAIL TO app_admin;

-- Thoát
EXIT;
