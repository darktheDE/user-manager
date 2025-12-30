# HƯỚNG DẪN CÀI ĐẶT (SETUP GUIDE)

Hướng dẫn ngắn gọn để chạy dự án trên Windows (PowerShell).

## 1. Yêu cầu hệ thống (Prerequisites)
-   **Docker Desktop**: Đã cài đặt và đang chạy.
-   **Python 3.10+**: Đã cài đặt.
-   **Visual Studio Code**.

## 2. Cài đặt Môi trường & Database

### Bước 1: Chuẩn bị Source Code
1.  Tải file `.zip` source code về và giải nén.
2.  Mở thư mục dự án bằng **VSCode**.
3.  Mở Terminal (Ctrl + J), chọn **PowerShell**.

### Bước 2: Tạo Môi trường Python (Virtual Environment)
```powershell
# Tạo môi trường ảo tên là 'venv'
python -m venv venv

# Kích hoạt môi trường
.\venv\Scripts\activate
```

### Bước 3: Cài đặt thư viện (Requirements)
*Lưu ý: Nếu gặp lỗi cài đặt, xem phần Troubleshooting bên dưới.*
```powershell
# Nâng cấp pip trước để tránh lỗi
pip install --upgrade pip setuptools wheel

# Cài đặt các thư viện cần thiết
pip install -r server/requirements.txt
```

### Bước 4: Chạy Database (Docker)
```powershell
# Di chuyển vào thư mục chứa docker-compose.yml (nếu cần, thường là root)
docker compose up -d

# Kiểm tra container đã chạy chưa
docker ps
```
*Đợi khoảng 2-5 phút để Oracle Database khởi động hoàn toàn (trạng thái healthy).*

### Bước 5: Nạp dữ liệu mẫu & Setup Schema (Tự động)
```powershell
# Từ thư mục gốc (nơi chứa file run.py và folder server)
cd server
python scripts/seed_database.py
```
*Lệnh này sẽ tự động chạy các script SETUP (tạo bảng, user, policy) và tạo dữ liệu mẫu.*

### Bước 6: Chạy Website
```powershell
# Tại thư mục server
python run.py
```
Truy cập web tại: `http://localhost:8000`

---

## 3. Khắc phục lỗi (Troubleshooting)

### Lỗi 1: Không chạy được Docker do trùng Port 1521
*Hiện tượng:* Lỗi "Bind for 0.0.0.0:1521 failed: port is already allocated".
*Nguyên nhân:* Máy bạn đã cài Oracle Database native hoặc có tiến trình khác chiếm cổng 1521.
*Cách fix:*
```powershell
# 1. Tìm PID của tiến trình chiếm port 1521
netstat -ano | findstr :1521

# 2. Kill tiến trình đó (Thay 1234 bằng PID tìm được ở trên)
taskkill /F /PID 1234

# 3. Chạy lại docker
docker compose up -d
```

### Lỗi 2: Lỗi "Microsoft Visual C++ 14.0 is required" khi pip install
*Hiện tượng:* Lỗi khi cài `oracledb` hoặc `pydantic-core`.
*Nguyên nhân:* Thiếu trình biên dịch C++ để build thư viện.
*Cách fix nhanh (Không cần cài Visual Studio nặng nề):*
Sử dụng bản binary (đã build sẵn) bằng lệnh sau:
```powershell
pip install "pydantic>=2.7,<3" --only-binary=:all:
pip install oracledb --only-binary=:all:

# Sau đó chạy lại lệnh cài đặt đầy đủ
pip install -r requirements.txt
```

### Lỗi 3: Lỗi Rust Compiler
*Hiện tượng:* Lỗi liên quan đến `cargo` hoặc `rust auth` khi cài `pydantic-core`.
*Cách fix:* Tương tự như trên, ép dùng bản binary:
```powershell
pip install pydantic-core --only-binary=:all:
```
## 4. Truy cập database trên Powershell của VSCode
```powershell
docker exec -it oracle-db-23ai sqlplus -s system/oracle123@FREEPDB1
```

Tại đầy, bạn có thể truy cập database và thực hiện các lệnh SQL để kiểm tra dữ liệu.

## 5. Tài khoản Demo
Sau khi chạy script `seed_database.py`, các tài khoản sau sẽ được tạo sẵn với password tương ứng:

| Username | Password | Vai trò | Chức vụ |
| :--- | :--- | :--- | :--- |
| **system** | `oracle123` | Admin App | User đặc biệt của ứng dụng (nếu có trong config) |
| **ADMIN** | `admin123` | ADMIN_ROLE | System Administrator |
| **HR_USER** | `hr123` | HR_ROLE | HR Manager |
| **IT_USER** | `it123` | IT_ROLE | IT Developer |
| **FINANCE_USER** | `finance123` | FINANCE_ROLE | Finance Analyst |
| **MARKETING_USER** | `marketing123` | MARKETING_ROLE | Marketing Manager |
| **nhanvien01** | `Password123` | (None/Default) | User demo chức năng cơ bản |

*Lưu ý:* Các user trên (trừ `sys_admin`) đều là User thật trong Oracle Database và cũng có thể dùng để đăng nhập vào Web App.