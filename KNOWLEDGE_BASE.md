# KNOWLEDGE BASE (CƠ SỞ KIẾN THỨC & MAPPING) - ĐỒ ÁN User Management 23ai

Tài liệu này tổng hợp chi tiết nền tảng lý thuyết, kỹ thuật Oracle Security và ánh xạ vào source code của dự án.
**Mục tiêu:** Phục vụ bảo vệ đồ án, trả lời câu hỏi của ngày bảo vệ.

---

## 1. TỔNG QUAN DỰ ÁN
- **Công nghệ:** Oracle Database 23ai (Docker), Python (FastAPI), OracleDB Driver (Thin mode).
- **Mục tiêu chính:** Xây dựng ứng dụng quản lý User tập trung và Demo các tính năng bảo mật nâng cao của Oracle mà không cần code logic phức tạp ở Backend (Security inside DB).

---

## 2. PHẦN CỦA ĐINH TRỌNG ĐỨC ANH
**Trách nhiệm:** Quản lý User, Profile, Password Policy, Unified Auditing, Data Redaction.

### A. Quản lý User (User Lifecycle Management)
#### 1. Lý thuyết
- **Authentication (Xác thực):** Xác định "Bạn là ai?". Trong Oracle, user đăng nhập được kiểm tra qua Data Dictionary.
- **Tablespace:** Không gian lưu trữ vật lý của user.
    - `DEFAULT TABLESPACE`: Nơi lưu dữ liệu (bảng, index) user tạo ra. (Dự án dùng `USERS`).
    - `TEMPORARY TABLESPACE`: Nơi xử lý các tác vụ sắp xếp, hash tạm thời. (Dự án dùng `TEMP`).
- **Quota:** Giới hạn dung lượng user được phép dùng trên Tablespace (VD: 500M).

#### 2. Kỹ thuật & SQL
- **Tạo User:**
  ```sql
  CREATE USER nhanvien01 IDENTIFIED BY Password123
  DEFAULT TABLESPACE users TEMPORARY TABLESPACE temp
  QUOTA 500M ON users;
  ```
- **Khóa/Mở khóa:**
  ```sql
  ALTER USER nhanvien01 ACCOUNT LOCK;   -- Ngăn đăng nhập
  ALTER USER nhanvien01 ACCOUNT UNLOCK; -- Cho phép đăng nhập lại
  ```
- **View quản lý:** `DBA_USERS` (chứa `username`, `account_status`, `created`, `profile`...).

#### 3. Mapping Code (`server/app`)
- **Backend:** `business/services/user_service.py` -> `data/oracle/user_dao.py`.
- **Hàm DAO:** `create_user`, `update_user` (dùng `ALTER USER`), `delete_user` (dùng `DROP USER CASCADE`).

---

### B. Profile & Password Policy
#### 1. Lý thuyết
- **Profile:** Là tập hợp các giới hạn về Tài nguyên (Resource) và Mật khẩu (Password) gán cho User.
- **Resource Limits:**
    - `SESSIONS_PER_USER`: Giới hạn số kết nối đồng thời (Demo set = 1 để test login failure).
    - `CONNECT_TIME`: Giới hạn thời gian kết nối tối đa.
- **Password Limits:**
    - `FAILED_LOGIN_ATTEMPTS`: Số lần sai pass cho phép trước khi bị khóa (LOCKED).
    - `PASSWORD_LIFE_TIME`: Thời hạn dùng mật khẩu (VD: 30 ngày phải đổi).

#### 2. Kỹ thuật & SQL
- **Tạo Profile:**
  ```sql
  CREATE PROFILE PROF_LIMIT LIMIT
    SESSIONS_PER_USER 1
    FAILED_LOGIN_ATTEMPTS 3
    PASSWORD_LIFE_TIME 30;
  ```
- **Gán cho User:**
  ```sql
  ALTER USER nhanvien01 PROFILE PROF_LIMIT;
  ```
- **View quản lý:** `DBA_PROFILES`.

#### 3. Mapping Code
- **Backend:** `business/services/profile_service.py` -> `data/oracle/profile_dao.py`.
- **Logic:** API cho phép tạo Profile với các tham số trên và query gán profile cho user.

---

### C. Unified Auditing (Giám sát toàn diện)
#### 1. Lý thuyết
- **Legacy Audit (Cũ):** Log nằm rải rác (`SYS.AUD$`, `FGA_LOG$`, OS files). Khó quản lý.
- **Unified Audit (Mới - 12c+):** Tất cả log dồn về một nơi duy nhất: `UNIFIED_AUDIT_TRAIL`. Hiệu năng cao hơn, an toàn hơn (chỉ ghi, không cho sửa/xóa dễ dàng).
- **Policy based:** Tạo chính sách audit và enable cho user/role nào đó.

#### 2. Kỹ thuật & SQL
- **Tạo Policy (Demo Audit cả DDL và DML):**
  ```sql
  -- Audit lệnh DDL (Tạo/Xóa User)
  CREATE AUDIT POLICY audit_user_admin
    ACTIONS CREATE USER, ALTER USER, DROP USER;
  
  -- Audit lệnh DML (Select/Update trên bảng Projects)
  CREATE AUDIT POLICY audit_projects_dml
    ACTIONS SELECT, INSERT, UPDATE, DELETE ON SYSTEM.PROJECTS;
  ```
- **Kích hoạt:** `AUDIT POLICY audit_user_admin;`
- **Xem Log:**
  ```sql
  SELECT event_timestamp, dbusername, action_name, sql_text 
  FROM unified_audit_trail WHERE object_name = 'PROJECTS';
  ```

#### 3. Mapping Code
- **Setup Script:** `scripts/setup/04_create_audit.sql`.
- **Backend:** `presentation/routes/security.py` -> query view `unified_audit_trail`.

---

### D. Oracle Data Redaction (Che giấu dữ liệu)
#### 1. Lý thuyết
- **Data Redaction:** Masking (làm mờ) dữ liệu nhạy cảm khi trả về cho ứng dụng, nhưng dữ liệu gốc trong đĩa vẫn nguyên vẹn.
- **Ưu điểm:** Không cần sửa code ứng dụng để che số điện thoại/email.
- **Các loại:**
    - `FULL`: Che toàn bộ (trả về null hoặc khoảng trắng).
    - `PARTIAL`: Che một phần (VD: `*****5678`).
    - `REGEXP`: Dùng biểu thức chính quy để che (VD: Email).

#### 2. Kỹ thuật & SQL
- **Dùng package:** `DBMS_REDACT`.
- **Tạo Policy:**
  ```sql
  BEGIN
    DBMS_REDACT.ADD_POLICY(
      object_schema => 'SYSTEM',
      object_name   => 'USER_INFO',
      column_name   => 'PHONE',
      function_type => DBMS_REDACT.PARTIAL,
      function_parameters => '9,1,3' -- Hiển thị 3 số cuối
    );
  END;
  ```
- **View quản lý:** `REDACTION_POLICIES`, `REDACTION_COLUMNS`.

#### 3. Mapping Code
- **Setup Script:** `scripts/setup/06_configure_redaction.sql`.
- **Backend:** `security.py` -> Kết nối DB bằng user thường để demo (vì user `SYS` hoặc chủ sở hữu bảng thường được miễn trừ policy - `EXEMPT REDACTION POLICY`).

---

## 3. PHẦN CỦA PHẠM PHÚC HƯNG
**Trách nhiệm:** Quản lý Role, Phân quyền (Grant/Revoke), VPD, FGA.

### A. Quản lý Role & Privileges
#### 1. Lý thuyết
- **Privilege (Quyền):**
    - `System Privilege`: Quyền hệ thống (VD: `CREATE SESSION`, `CREATE TABLE`).
    - `Object Privilege`: Quyền trên đối tượng cụ thể (VD: `SELECT ON HR.EMPLOYEES`).
- **Role (Vai trò):** Nhóm các quyền lại với nhau. Cấp quyền cho Role, rồi cấp Role cho User -> Dễ quản lý (RBAC - Role Based Access Control).

#### 2. Kỹ thuật & SQL
- **Tạo Role:** `CREATE ROLE ROLE_NHANVIEN;`
- **Cấp quyền cho Role:**
  ```sql
  GRANT CREATE SESSION TO ROLE_NHANVIEN;
  GRANT SELECT ON SYSTEM.PROJECTS TO ROLE_NHANVIEN;
  ```
- **Cấp Role cho User:** `GRANT ROLE_NHANVIEN TO nhanvien01;`

#### 3. Mapping Code
- **Backend:** `business/services/role_service.py` (CRUD Role), `privilege_service.py` (Grant/Revoke).
- **DAO:** `data/oracle/role_dao.py`.

---

### B. VPD (Virtual Private Database) - Row Level Security
#### 1. Lý thuyết
- **Vấn đề:** Làm sao để User A chỉ thấy dữ liệu của phòng ban A, User B thấy phòng ban B trên cùng 1 bảng?
- **Giải pháp VPD:** Oracle tự động "tiêm" thêm mệnh đề `WHERE` vào sau mọi câu SQL của user.
    - User A query: `SELECT * FROM PROJECTS` -> Oracle tự đổi thành: `SELECT * FROM PROJECTS WHERE DEPARTMENT = 'IT'`.
- **Components:**
    - `Application Context`: Biến môi trường session (VD: Lưu user này thuộc phòng nào).
    - `Policy Function`: Hàm PL/SQL trả về chuỗi `WHERE` (predicate).
    - `Policy`: Gắn hàm vào bảng.

#### 2. Kỹ thuật & SQL
- **Hàm Policy (Mô phỏng):**
  ```sql
  CREATE FUNCTION vpd_function (schema_p VARCHAR2, table_p VARCHAR2)
  RETURN VARCHAR2 IS
  BEGIN
    -- Nếu là Manager IT, chỉ thấy dự án IT
    IF SYS_CONTEXT('USERENV', 'SESSION_USER') = 'MANAGER_IT' THEN
      RETURN 'DEPARTMENT = ''IT''';
    END IF;
    RETURN '1=1'; -- Mặc định thấy hết hoặc chặn hết tùy logic
  END;
  ```
- **Gắn Policy:**
  ```sql
  BEGIN
    DBMS_RLS.ADD_POLICY(
      object_schema => 'SYSTEM',
      object_name   => 'PROJECTS',
      policy_name   => 'vpd_projects',
      policy_function => 'vpd_function'
    );
  END;
  ```

#### 3. Mapping Code
- **Setup Script:** `scripts/setup/03_create_vpd_policy.sql` (Tạo Context, Package set context, Policy function).
- **Backend:** `presentation/routes/security.py`. API login giả lập set context để demo.

---

### C. FGA (Fine-Grained Auditing)
#### 1. Lý thuyết
- **Khác gì với Standard/Unified Audit?**
    - Standard Audit: Audit "Thô" (VD: Audit lệnh SELECT bảng Lương -> Ai select cũng ghi, ghi rất nhiều).
    - FGA: Audit "Tinh" (Chỉ ghi khi thỏa mãn điều kiện WHERE hoặc truy cập cột nhạy cảm).
- **Ví dụ:** Chỉ Audit khi user `UPDATE` cột `SALARY` mà giá trị mới > 100 triệu.

#### 2. Kỹ thuật & SQL
- **Dùng package:** `DBMS_FGA`.
- **Tạo Policy:**
  ```sql
  BEGIN
    DBMS_FGA.ADD_POLICY(
      object_schema   => 'SYSTEM',
      object_name     => 'PROJECTS',
      policy_name     => 'AUDIT_HIGH_BUDGET',
      audit_condition => 'BUDGET > 1000000000', -- Chỉ audit dự án > 1 tỷ
      audit_column    => 'BUDGET',                -- Chỉ audit khi đụng vào cột tiền
      statement_types => 'INSERT,UPDATE'
    );
  END;
  ```
- **Log:** Cũng xem trong `UNIFIED_AUDIT_TRAIL` (hoặc `DBA_FGA_AUDIT_TRAIL` cũ).

#### 3. Mapping Code
- **Setup Script:** `scripts/setup/04_create_audit.sql` (Phần FGA policies).
- **Backend:** `security.py` (Chung API get logs với Unified Audit nhưng lọc theo policy name).

---

## 4. TÀI NGUYÊN THAM KHẢO (TRONG SOURCE)
- `docs/04_odb.md`: Bài lab chi tiết về VPD.
- `docs/08_audit.md`: Lý thuyết Standard Audit.
- `docs/09_audit.md`: Lý thuyết & Lab FGA.
