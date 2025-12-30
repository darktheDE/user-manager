# User Manager - Hệ thống Quản lý Người dùng Oracle Database Security

## Giới thiệu

**User Manager** là một ứng dụng web demo minh họa các tính năng bảo mật nâng cao của **Oracle Database 23ai**, được xây dựng với **FastAPI** (Python). Dự án này phục vụ mục đích học tập và nghiên cứu về cách tích hợp bảo mật cơ sở dữ liệu vào ứng dụng thực tế.

Dự án áp dụng kiến trúc 3 lớp (Presentation, Business, Data Access) và sử dụng Docker để đơn giản hóa việc triển khai.

## Chức năng Nổi bật

### 1. Quản lý Người dùng & Phân quyền
- **CRUD User**: Tạo, xem, sửa, xóa người dùng Oracle Database.
- **Profile Management**: Quản lý password policy (hết hạn mật khẩu, khóa tài khoản...).
- **Role & Privilege**: Cấp phát quyền hạn và vai trò cho người dùng.

### 2. Các Tính năng Bảo mật Oracle
Dự án demo trực quan các công nghệ bảo mật cốt lõi:
- **Unified Auditing**: Ghi nhật ký hành động người dùng (đăng nhập, thay đổi dữ liệu) tập trung.
- **Fine-Grained Auditing (FGA)**: Giám sát truy cập dữ liệu ở mức độ chi tiết (ví dụ: chỉ audit khi lương > 2000).
- **Virtual Private Database (VPD)**: Kiểm soát truy cập mức hàng (Row-level Security). Người dùng chỉ thấy dữ liệu họ được phép thấy (vd: Nhân viên chỉ thấy dự án của phòng ban mình).
- **Data Redaction**: Che giấu dữ liệu nhạy cảm (số điện thoại, email) ngay tại tầng database mà không cần thay đổi code ứng dụng.

## Công nghệ Sử dụng

- **Backend**: Python 3.11+, FastAPI, Uvicorn.
- **Database**: Oracle Database 23ai Free (Dockerized).
- **Driver**: python-oracledb (Thin mode).
- **Frontend**: Jinja2 Templates, Bootstrap 5, Vanilla JS (Giao diện đơn giản, tập trung vào chức năng).
- **Containerization**: Docker, Docker Compose.

## Yêu cầu Hệ thống

- **Hệ điều hành**: Windows 10/11, Linux, hoặc macOS.
- **Docker Desktop**: Đã cài đặt và đang chạy.
- **Python**: Phiên bản 3.10 trở lên.
- **RAM**: Tối thiểu 4GB (khuyến nghị 8GB) để chạy mượt mà Oracle Database container.

## Hướng dẫn Cài đặt & Chạy

### Bước 1: Chuẩn bị Môi trường
1.  Clone repository này về máy.
2.  Mở thư mục dự án trong VS Code.
3.  Mở Terminal (Powershell hoặc Bash).

### Bước 2: Khởi động Database
```bash
cd server
docker compose up -d
```
*Lưu ý: Lần đầu chạy sẽ mất vài phút để pull image và khởi tạo database. Đợi đến khi container `oracle-db-23ai` ở trạng thái "healthy".*

### Bước 3: Cài đặt Dependencies
Nên sử dụng môi trường ảo (virtual environment):
```bash
# Tạo môi trường ảo
python -m venv venv

# Kích hoạt (Windows)
.\venv\Scripts\activate
# Kích hoạt (Linux/Mac)
# source venv/bin/activate

# Cài đặt thư viện
pip install -r server/requirements.txt
```
*Nếu gặp lỗi cài đặt thư viện `oracledb` trên Windows, hãy đảm bảo bạn đã update pip (`python -m pip install --upgrade pip`) hoặc cài Visual C++ Build Tools.*

### Bước 4: Nạp Dữ liệu Mẫu (Seed Data)
Script này sẽ tạo các bảng, user, role và dữ liệu demo cần thiết:
```bash
# Đứng tại thư mục gốc (chứa run.py)
cd server
python scripts/seed_database.py
```

### Bước 5: Chạy Ứng dụng Web
```bash
# Tại thư mục server
python run.py
```
Truy cập ứng dụng tại: **http://localhost:8000**

## Tài khoản Demo

Sau khi chạy seed data, bạn có thể đăng nhập bằng các tài khoản sau:

| Username | Password | Vai trò | Mô tả |
| :--- | :--- | :--- | :--- |
| **system** | `oracle123` | **App Admin** | Quản trị viên hệ thống, toàn quyền quản lý user DB. |
| **ADMIN** | `admin123` | **Quản trị** | Admin nghiệp vụ, quản lý dự án. |
| **HR_USER** | `hr123` | **Nhân sự** | Quản lý thông tin nhân viên (thấy Số điện thoại full). |
| **IT_USER** | `it123` | **IT** | Nhân viên IT. |
| **nhanvien01** | `Password123` | **User thường** | Nhân viên bình thường (Số ĐT bị che sao *). |

*Lưu ý: Mật khẩu Oracle phân biệt hoa thường.*

## Cấu trúc Dự án

```
user-manager/
├── server/
│   ├── app/
│   │   ├── business/       # Xử lý nghiệp vụ (Services)
│   │   ├── data/           # Truy xuất dữ liệu (DAOs, Connection)
│   │   ├── models/         # Pydantic models & DTOs
│   │   ├── presentation/   # Routes, Templates, Static files
│   │   └── main.py         # App entry point
│   ├── scripts/            # SQL scripts & Seed data scripts
│   ├── docker-compose.yml  # Cấu hình Docker
│   ├── requirements.txt    # Python dependencies
│   └── run.py              # Script chạy server
├── README.md               # Tài liệu chính
└── SETUP_GUIDE.md          # Hướng dẫn setup chi tiết (dự phòng)
```

## Khắc phục Lỗi Thường gặp

1.  **Lỗi "Port 1521 already allocated"**:
    -   Máy bạn đang có một Oracle Database khác chạy chiếm cổng 1521. Hãy tắt nó hoặc đổi port trong `docker-compose.yml`.

2.  **Lỗi kết nối Database (ORA-12514, TNS:listener...)**:
    -   Database chưa khởi động xong. Hãy đợi thêm 1-2 phút và kiểm tra `docker logs oracle-db`.

3.  **Lỗi hiển thị tiếng Việt**:
    -   Dự án đã cấu hình UTF-8, tuy nhiên nếu gặp lỗi font trên terminal, hãy set encoding cho terminal của bạn.

## Tài liệu Tham khảo
- [Thông tin chi tiết về Oracle Database Setup](server/scripts/setup/ORACLE_README.md)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
