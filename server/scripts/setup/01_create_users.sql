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

-- Thoát
EXIT;
