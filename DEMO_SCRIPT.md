# KỊCH BẢN DEMO CHI TIẾT (DEMO SCRIPT)

Tài liệu này hướng dẫn chi tiết các bước demo sản phẩm, bao gồm thao tác trên giao diện Web và các lệnh kiểm chứng trực tiếp trong Database (sử dụng Terminal/PowerShell).

**Phân Công:**
- **Anh Huy:** Quản lý User, Profile, Password; Unified Audit; Data Redaction.
- **Anh Hưng:** Quản lý Role, Quyền hạn (Grant/Revoke); VPD (Phân quyền dòng); FGA (Giám sát thay đổi tiền).

---

## 1. Chuẩn bị (Pre-demo) - Dành cho cả 2
1.  **Mở Web:** Truy cập `http://localhost:8000`
2.  **Mở Terminal (VSCode/PowerShell):** Để chạy lệnh kiểm chứng.
3.  **Login Admin:** Đăng nhập web bằng tài khoản `sys_admin` / `password`.

---

## 2. Phần của ANH HUY

### Kịch bản 1: Quản lý Vòng đời User (Tạo - Sửa - Khóa)
*Mục tiêu: Chứng minh ứng dụng có thể quản lý user Oracle thật.*

1.  **Tạo User mới:**
    -   Vào menu **Quản lý Người dùng**.
    -   Bấm nút **Tạo Người dùng**.
    -   Nhập: Username `nhanvien01`, Password `Password123`, Profile `DEFAULT`, Default Tablespace `USERS`, Temporary Tablespace `TEMP`.
    -   Bấm **Lưu**.
    -   *Trên Web:* Thấy `nhanvien01` xuất hiện trong danh sách.

2.  **Sửa & Khóa User:**
    -   Bấm vào user `nhanvien01` vừa tạo.
    -   Bấm nút **Khóa tài khoản**.
    -   *Trên Web:* Trạng thái chuyển sang biểu tượng khóa (Locked).

3.  **Kiểm chứng (Terminal):**
    Copy và chạy lệnh sau để xem trạng thái thực trong Database:
    ```powershell
    docker exec -it oracle-db-23ai sqlplus -s system/oracle123@FREEPDB1 "SELECT username, account_status, created FROM dba_users WHERE username = 'NHANVIEN01';"
    ```
    *Kết quả mong đợi:* Cột `ACCOUNT_STATUS` phải là `LOCKED`.

### Kịch bản 2: Quản lý Profile & Password
*Mục tiêu: Chứng minh việc áp dụng chính sách mật khẩu và giới hạn tài nguyên.*

1.  **Tạo Profile giới hạn:**
    -   Vào menu **Quản lý Profile**.
    -   Tạo Profile mới tên: `PROF_LIMIT`.
    -   Cấu hình: `Sessions/User = 1` (Chỉ cho phép 1 kết nối), `Connect Time = 15` (phút).
    -   Bấm **Lưu**.

2.  **Gán Profile cho User:**
    -   Vào **Quản lý Người dùng** -> Chọn `nhanvien01`.
    -   Bấm **Sửa**, đổi Profile sang `PROF_LIMIT`.
    -   Bấm **Cập nhật**.

3.  **Kiểm chứng (Terminal):**
    Kiểm tra xem User đã nhận Profile mới chưa:
    ```powershell
    docker exec -it oracle-db-23ai sqlplus -s system/oracle123@FREEPDB1 "SELECT username, profile FROM dba_users WHERE username = 'NHANVIEN01';"
    ```
    *Kết quả mong đợi:* Cột `PROFILE` phải là `PROF_LIMIT`.

### Kịch bản 3: Unified Audit (Giám sát toàn diện)
*Mục tiêu: Đảm bảo mọi hành động tác động dữ liệu (DML) VÀ cấu trúc (DDL) đều được ghi lại.*

1.  **Thực hiện hành động để Audit:**
    -   **DML:** Đăng nhập, đăng xuất với user `system`.
    -   **DDL (Quan trọng):** Dùng `sys_admin` xóa thử 1 user cũ, hoặc tạo một user mới rồi xóa. (Hệ thống đã cấu hình Audit các lệnh CREATE, ALTER, DELETE User/Role/Profile).

2.  **Xem Log trên Web:**
    -   Vào menu **Bảo mật Oracle** -> **Audit (Giám sát)**.
    -   Tab **Unified Audit Trail**.
    -   Chỉ ra dòng log DDL mới nhất: `CREATE USER`, `DROP USER`...
    -   Chỉ ra dòng log DML (nếu có): `SELECT`, `UPDATE`...

3.  **Kiểm chứng (Terminal - Tùy chọn):**
    Xem trực tiếp log trong DB:
    ```powershell
    docker exec -it oracle-db-23ai sqlplus -s system/oracle123@FREEPDB1 "SELECT dbusername, action_name, object_name, event_timestamp FROM unified_audit_trail ORDER BY event_timestamp DESC FETCH FIRST 10 ROWS ONLY;"
    ```

### Kịch bản 4: Data Redaction (Che giấu dữ liệu)
*Mục tiêu: Bảo vệ thông tin nhạy cảm (SĐT, Email) khỏi nhân viên thường.*

1.  **Truy cập trang Demo:**
    -   Login với user `sys_admin`.
    -   Vào menu **Bảo mật Oracle** -> **Data Redaction**.

2.  **Giải thích màn hình:**
    -   Phần trên: Hiển thị Policy `REDACT_USER_INFO_POLICY` đang **Active** cho bảng `USER_INFO`.
    -   Cột `PHONE` và `EMAIL` được cấu hình che toàn bộ (Full Redaction).

3.  **Live Demo (Quan trọng):**
    -   Kéo xuống phần **Live Demo: User View**.
    -   Giải thích: "Đây là dữ liệu khi một user thường (app_admin) truy vấn vào Database".
    -   *Kết quả:* Cột **Email** và **Phone** hiển thị toàn dấu sao `*****` hoặc khoảng trắng (tùy cấu hình), không hiện số thật.
    -   So sánh với dữ liệu thật trong trang "Quản lý User" (nếu cần).

---

## 3. Phần của ANH HƯNG

### Kịch bản 5: Quản lý Role & Phân quyền (Grant/Revoke)
*Mục tiêu: Tạo nhóm quyền và cấp cho user.*

1.  **Tạo Role:**
    -   Vào menu **Quản lý Role**.
    -   Tạo Role mới: `ROLE_NHANVIEN`.
    -   Bấm **Lưu**.

2.  **Cấp Quyền cho Role:**
    -   Vào menu **Quản lý Quyền** -> **Quyền Hệ thống**.
    -   Grantee (Người nhận): Chọn `ROLE_NHANVIEN`.
    -   Privilege: Chọn `CREATE SESSION`.
    -   Bấm **Cấp quyền**.

3.  **Gán Role cho User:**
    -   Vào **Quản lý Người dùng** -> Chọn `nhanvien01`.
    -   Phần Role (nếu có chức năng gán role) hoặc thực hiện Grant Role qua menu Quyền.
    -   (Nếu UI chưa có phần gán Role cho User ở trang Edit): Vào **Quản lý Quyền** -> **Quyền Role** -> Grant `ROLE_NHANVIEN` cho `nhanvien01`.

4.  **Kiểm chứng (Terminal):**
    Kiểm tra Role đã có quyền session chưa:
    ```powershell
    docker exec -it oracle-db-23ai sqlplus -s system/oracle123@FREEPDB1 "SELECT * FROM dba_sys_privs WHERE grantee = 'ROLE_NHANVIEN';"
    ```

### Kịch bản 6: VPD (Virtual Private Database - Phân quyền dòng)
*Mục tiêu: Demo 2 quản lý khác nhau nhìn thấy dữ liệu khác nhau trên cùng 1 bảng.*

1.  **Vào trang Demo:**
    -   Vào menu **Bảo mật Oracle** -> **VPD (Row Level Security)**.

2.  **Demo luồng:**
    -   **Bước 1:** Đăng nhập giả lập `manager_it`. (Trên giao diện có thể có dropdown chọn user demo hoặc login lại).
        -   *Kết quả:* Danh sách Dự án chỉ hiện các dòng có Department là `IT`.
    -   **Bước 2:** Đăng nhập giả lập `manager_sales`.
        -   *Kết quả:* Danh sách Dự án chỉ hiện các dòng có Department là `SALES`.

3.  **Giải thích kỹ thuật:**
    -   "Oracle tự động thêm mệnh đề `WHERE department = 'IT'` vào câu SQL của manager_it mà ứng dụng không cần sửa code query."

### Kịch bản 7: FGA (Fine-Grained Auditing - Giám sát sửa tiền)
*Mục tiêu: Chỉ audit khi có người sửa vào cột Nhạy cảm (Budget) hoặc thao tác dữ liệu giá trị lớn.*

1.  **Thực hiện hành động nhạy cảm:**
    -   Vào menu **Quản lý Dự án** (Hoặc trang chi tiết dự án).
    -   Sửa **Ngân sách (Budget)** của một dự án bất kỳ (Ví dụ: từ 1000 lên 500000).
    -   Bấm **Lưu**.

2.  **Xem Log FGA:**
    -   Vào menu **Bảo mật Oracle** -> **Audit (Giám sát)**.
    -   Tab **FGA Logs** (Nếu tách riêng) hoặc tìm trong danh sách Audit.
    -   Chỉ ra dòng log: "User ... đã UPDATE bảng PROJECTS, cột BUDGET".
    -   Nhấn mạnh: "Nếu chỉ `SELECT` bình thường thì không ghi log (đỡ rác log), chỉ khi đụng vào tiền mới ghi".

3.  **Kiểm chứng (Terminal):**
    Chạy lệnh xem policy FGA đang kích hoạt:
    ```powershell
    docker exec -it oracle-db-23ai sqlplus -s system/oracle123@FREEPDB1 "SELECT policy_name, policy_column FROM dba_audit_policies WHERE object_name = 'PROJECTS';"
    ```
