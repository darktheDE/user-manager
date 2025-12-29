# User Manager - Backend Server

## Tổng quan

Ứng dụng quản lý người dùng Oracle Database được xây dựng bằng FastAPI và Oracle Database 23ai.

## Kiến trúc

Ứng dụng tuân theo **Kiến trúc 3 lớp (3-Layer Architecture)**:

- **Presentation Layer:** FastAPI routes + Jinja2 templates
- **Business Layer:** Service classes xử lý logic nghiệp vụ
- **Data Layer:** Truy cập Oracle database (oracledb driver)

## Công nghệ sử dụng

- **Python:** 3.11+
- **Web Framework:** FastAPI
- **Templates:** Jinja2
- **Database:** Oracle Database 23ai (qua Docker)
- **Database Driver:** oracledb (thư viện chính thức của Oracle cho Python)
- **Security:** bcrypt cho mã hóa mật khẩu

## Cấu trúc dự án

```
server/
├── app/
│   ├── main.py                 # Điểm khởi đầu FastAPI
│   ├── config.py               # Cấu hình
│   ├── presentation/           # Presentation Layer
│   │   ├── routes/             # FastAPI routes
│   │   ├── templates/          # Jinja2 templates
│   │   └── static/             # Static files (CSS, JS, images)
│   ├── business/               # Business Layer
│   │   ├── services/           # Business logic services
│   │   └── models/             # Pydantic models
│   └── data/                   # Data Layer
│       ├── oracle/             # Oracle DB access
│       └── repositories/       # Data repositories
├── scripts/setup/              # Database setup scripts
├── docker-compose.yml          # Oracle Database Docker setup
├── requirements.txt            # Python dependencies
└── README.md                   # File này
```

## Cài đặt và Chạy

### Yêu cầu

- Python 3.11 trở lên
- Docker và Docker Compose
- Tối thiểu 4GB RAM cho Oracle container

### Các bước cài đặt

1. **Tạo môi trường ảo:**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   # hoặc: source venv/bin/activate  # Linux/Mac
   ```

2. **Cài đặt dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Khởi động Oracle Database:**
   ```bash
   docker-compose up -d oracle-db
   ```

4. **Chờ Oracle khởi tạo (2-3 phút):**
   ```bash
   docker-compose logs -f oracle-db
   ```

5. **Chạy ứng dụng:**
   ```bash
   # Cách 1: Dùng uvicorn trực tiếp
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   
   # Cách 2: Dùng script run.py
   python run.py
   ```

6. **Truy cập ứng dụng:**
   - API: http://localhost:8000
   - Swagger Docs: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc
   - Health Check: http://localhost:8000/health

## Phát triển

### Kiểm tra Code

```bash
# Linting
ruff check .

# Format code
ruff format .

# Type checking
mypy app
```

## Cấu hình Database

Xem `scripts/setup/ORACLE_README.md` để biết hướng dẫn chi tiết về Oracle Database.

## Tính năng

- ✅ Quản lý User Oracle (CREATE/ALTER/DROP USER)
- ✅ Quản lý Profile
- ✅ Quản lý Role
- ✅ Quản lý Privilege (Grant/Revoke)
- ✅ VPD (Virtual Private Database)
- ✅ OLS (Oracle Label Security)
- ✅ Audit (Standard + FGA)

## Bảo mật

- Mã hóa mật khẩu bằng bcrypt
- Ngăn chặn SQL injection (bind variables)
- Validate input cho DDL statements
- Kiểm tra quyền Oracle
