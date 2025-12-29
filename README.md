# User Manager - Hệ thống Quản lý Người dùng Oracle Database

## Tổng quan

Ứng dụng web quản lý người dùng Oracle Database được xây dựng bằng FastAPI và Oracle Database 23ai theo kiến trúc 3 lớp.

## Yêu cầu hệ thống

- Python 3.11 trở lên
- Docker và Docker Compose
- Tối thiểu 4GB RAM cho Oracle container

## Cài đặt và Chạy dự án

### Bước 1: Đăng nhập Oracle Container Registry (chỉ cần 1 lần đầu tiên)

> **Lưu ý:** Bước này chỉ cần thực hiện 1 lần đầu tiên khi chưa có Oracle image. Nếu đã pull image rồi thì có thể bỏ qua.

```bash
docker login container-registry.oracle.com
```

Cần tài khoản Oracle (đăng ký miễn phí tại oracle.com) và chấp nhận license.

### Bước 2: Khởi động Oracle Database

```bash
cd server
docker compose up -d
```

Chờ 2-3 phút để Oracle khởi tạo hoàn tất.

### Bước 3: Kiểm tra Oracle đã chạy

```bash
docker-compose ps
```

Xem logs nếu cần:
```bash
docker-compose logs -f oracle-db
```

### Bước 4: Cài đặt Python dependencies

```bash
# Tạo môi trường ảo
python -m venv venv

# Kích hoạt môi trường ảo
venv\Scripts\activate  # Windows
# hoặc: source venv/bin/activate  # Linux/Mac

# Cài đặt dependencies
pip install -r requirements.txt
```

### Bước 5: Chạy ứng dụng

```bash
python run.py
```

Hoặc:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Bước 6: Truy cập ứng dụng

- **API:** http://localhost:8000
- **Swagger Docs:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/health

## Thông tin đăng nhập mặc định

### Oracle Database

- **Host:** localhost
- **Port:** 1521
- **Service Name:** FREEPDB1
- **Username:** system
- **Password:** oracle123
- **Username (SYSDBA):** sys
- **Password (SYSDBA):** oracle123

### Oracle Enterprise Manager Express

- **URL:** http://localhost:5500/em
- **Username:** system
- **Password:** oracle123

## Cấu trúc dự án

```
user-manager/
├── .claude/              # Claude Code configurations (không push lên git)
├── server/               # Backend server
│   ├── app/             # Application code
│   ├── scripts/         # Setup scripts
│   ├── docker-compose.yml
│   ├── requirements.txt
│   └── README.md        # Chi tiết về server
└── README.md            # File này
```

## Tài liệu thêm

- Chi tiết về server: `server/README.md`
- Hướng dẫn Oracle Database: `server/scripts/setup/ORACLE_README.md`

