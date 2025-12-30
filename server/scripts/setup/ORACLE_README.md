# Hướng dẫn Setup Oracle Database

## Tổng quan

Dự án sử dụng **Oracle Database 23ai Free Edition** chạy trong Docker container.

## Yêu cầu

- Docker và Docker Compose đã cài đặt
- Tối thiểu 4GB RAM cho Oracle container
- Cổng 1521 và 5500 trống

## Bắt đầu nhanh

1. **Đăng nhập Oracle Container Registry (chỉ lần đầu):**
   ```bash
   docker login container-registry.oracle.com
   ```
   Cần tài khoản Oracle (đăng ký miễn phí tại oracle.com) và chấp nhận license.

2. **Khởi động Oracle Database:**
   ```bash
   cd server
   docker compose up -d
   ```

3. **Kiểm tra trạng thái container:**
   ```bash
   docker-compose ps
   ```

4. **Xem logs:**
   ```bash
   docker-compose logs -f oracle-db
   ```

5. **Chờ khởi tạo:**
   Oracle database mất 2-3 phút để khởi tạo hoàn toàn. Đợi đến khi container chạy ổn định.

6. **Chạy script khởi tạo (tùy chọn):**
   Sau khi database sẵn sàng, có thể chạy script setup:
   ```bash
cd server

Get-Content scripts\setup\01_create_users.sql |
docker exec -i oracle-db-23ai sqlplus system/oracle123@FREEPDB1

Get-Content scripts\setup\02_create_tables.sql |
docker exec -i oracle-db-23ai sqlplus system/oracle123@FREEPDB1
   ```

## Thông tin kết nối

- **Host:** localhost
- **Port:** 1521
- **Service Name:** FREEPDB1 (Pluggable Database)
- **SID:** FREE (cho root container)
- **User mặc định:**
  - `system` / `oracle123` (đổi mật khẩu khi production!)
  - `sys` / `oracle123` (với quyền SYSDBA)

## Oracle Enterprise Manager Express

Truy cập Oracle EM Express tại:
- **URL:** http://localhost:5500/em
- **Username:** system
- **Password:** oracle123

## Các thao tác thường dùng

### Kết nối bằng SQL*Plus

```bash
# Kết nối đến Pluggable Database (FREEPDB1)
docker exec -it oracle-db-23ai sqlplus system/oracle123@FREEPDB1

# Hoặc kết nối đến root container
docker exec -it oracle-db-23ai sqlplus sys/oracle123@FREE AS SYSDBA
```

### Kết nối bằng SQLcl

```bash
docker exec -it oracle-db-23ai sql system/oracle123@FREEPDB1
```

### Tạo User cho ứng dụng

```sql
-- Kết nối với quyền system đến FREEPDB1
sqlplus system/oracle123@FREEPDB1

-- Tạo user
CREATE USER app_user IDENTIFIED BY "mat_khau_an_toan";
ALTER USER app_user QUOTA UNLIMITED ON USERS;
GRANT CONNECT, RESOURCE TO app_user;
GRANT CREATE SESSION TO app_user;
```

### Dừng Database

```bash
docker-compose stop oracle-db
```

### Xóa Database (⚠️ Xóa toàn bộ dữ liệu!)

```bash
docker-compose down -v
```

## Lưu trữ dữ liệu

Dữ liệu database được lưu trong Docker volume tên `oracle-data`. Để xóa toàn bộ dữ liệu:

```bash
docker volume rm user-manager_oracle-data
```

## Xử lý lỗi

### Container không khởi động

1. Kiểm tra dung lượng đĩa: `docker system df`
2. Xem logs: `docker-compose logs oracle-db`
3. Đảm bảo cổng 1521 và 5500 không bị chiếm

### Lỗi kết nối

1. Chờ khởi tạo hoàn tất (kiểm tra logs)
2. Kiểm tra container đang chạy: `docker-compose ps`
3. Kiểm tra cổng: `docker-compose port oracle-db 1521`

### Vấn đề mật khẩu

Mật khẩu mặc định là `oracle123`. Để đổi:

```bash
docker exec -it oracle-db-23ai sqlplus sys/oracle123@FREE AS SYSDBA
ALTER USER system IDENTIFIED BY "mat_khau_moi";
```

## Tính năng Oracle 23ai

Phiên bản này bao gồm:
- Hỗ trợ JSON
- Tính năng bảo mật nâng cao
- Hiệu suất cải thiện
- VPD, Data Redaction và Audit (Unified Audit và FGA)
