"""Các route tính năng bảo mật Oracle - VPD, Audit, Database Vault."""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse

from app.presentation.middleware import get_session
from app.presentation.templates import templates
from app.data.oracle.connection import db
from app.config import settings
import oracledb

router = APIRouter()


def require_auth(request: Request) -> str:
    """Yêu cầu xác thực và trả về username."""
    session = get_session(request)
    username = session.get("username")
    if not username:
        raise HTTPException(status_code=401, detail="Chưa xác thực")
    return username


@router.get("/security", response_class=HTMLResponse)
async def security_index(request: Request):
    """Trang tổng quan tính năng bảo mật."""
    username = require_auth(request)
    
    return templates.TemplateResponse(
        "security/index.html",
        {
            "request": request,
            "username": username,
        }
    )


@router.get("/security/vpd", response_class=HTMLResponse)
async def vpd_page(request: Request):
    """VPD - hiển thị các dự án được lọc theo phòng ban của user."""
    username = require_auth(request)
    
    try:
        conn = await db.get_connection()
        cursor = conn.cursor()
        
        # Thiết lập context user cho VPD
        try:
            await cursor.execute("BEGIN set_user_dept_proc(:username); END;", username=username)
        except Exception:
            pass
        
        # Truy vấn projects (VPD sẽ tự động lọc nếu policy đang hoạt động)
        await cursor.execute("""
            SELECT project_id, project_name, department, budget, status, owner_username
            FROM projects
            ORDER BY project_id
        """)
        
        columns = [desc[0].lower() for desc in cursor.description]
        rows = await cursor.fetchall()
        projects = [dict(zip(columns, row)) for row in rows]
        
        # Lấy thông tin VPD policy
        await cursor.execute("""
            SELECT policy_name, function, enable, sel, ins, upd, del
            FROM dba_policies
            WHERE object_name = 'PROJECTS'
        """)
        policy_cols = [desc[0].lower() for desc in cursor.description]
        policy_rows = await cursor.fetchall()
        vpd_policies = [dict(zip(policy_cols, row)) for row in policy_rows]
        
        await db.release_connection(conn)
        
        return templates.TemplateResponse(
            "security/vpd.html",
            {
                "request": request,
                "username": username,
                "projects": projects,
                "vpd_policies": vpd_policies,
                "error": None,
            }
        )
    except Exception as e:
        return templates.TemplateResponse(
            "security/vpd.html",
            {
                "request": request,
                "username": username,
                "projects": [],
                "vpd_policies": [],
                "error": str(e),
            }
        )


@router.get("/security/audit", response_class=HTMLResponse)
async def audit_page(request: Request):
    """Audit - hiển thị nhật ký FGA và Unified Audit."""
    username = require_auth(request)
    
    try:
        conn = await db.get_connection()
        cursor = conn.cursor()
        
        # FGA Audit Trail - Oracle 23ai stores FGA logs in unified_audit_trail with fga_policy_name set
        fga_logs = []
        try:
            # Query FGA logs from unified_audit_trail using fga_policy_name column
            # This gets REAL FGA logs, not just DML operations
            await cursor.execute("""
                SELECT 
                    TO_CHAR(event_timestamp, 'YYYY-MM-DD HH24:MI:SS') as timestamp,
                    dbusername as db_user,
                    object_schema,
                    object_name,
                    fga_policy_name as policy_name,
                    DBMS_LOB.SUBSTR(sql_text, 200, 1) as sql_text,
                    action_name as statement_type
                FROM unified_audit_trail
                WHERE fga_policy_name IS NOT NULL
                ORDER BY event_timestamp DESC
                FETCH FIRST 20 ROWS ONLY
            """)
            fga_cols = [desc[0].lower() for desc in cursor.description]
            fga_rows = await cursor.fetchall()
            fga_logs = [dict(zip(fga_cols, row)) for row in fga_rows]
        except Exception as e:
            print(f"FGA query error: {e}")
        
        # Unified Audit Trail
        unified_logs = []
        try:
            await cursor.execute("""
                SELECT 
                    TO_CHAR(event_timestamp, 'YYYY-MM-DD HH24:MI:SS') as event_timestamp,
                    dbusername,
                    action_name,
                    object_schema,
                    object_name,
                    DBMS_LOB.SUBSTR(sql_text, 100, 1) as sql_text,
                    return_code
                FROM unified_audit_trail
                WHERE object_name = 'PROJECTS'
                   OR action_name IN ('LOGON', 'LOGOFF')
                   OR action_name LIKE '%USER' 
                   OR action_name LIKE '%ROLE'
                   OR action_name LIKE '%PROFILE'
                ORDER BY event_timestamp DESC
                FETCH FIRST 30 ROWS ONLY
            """)
            ua_cols = [desc[0].lower() for desc in cursor.description]
            ua_rows = await cursor.fetchall()
            unified_logs = [dict(zip(ua_cols, row)) for row in ua_rows]
        except Exception as e:
            print(f"Unified audit query error: {e}")
        
        # Lấy các audit policies
        audit_policies = []
        try:
            await cursor.execute("""
                SELECT policy_name, enabled_option, entity_name
                FROM audit_unified_enabled_policies
            """)
            ap_cols = [desc[0].lower() for desc in cursor.description]
            ap_rows = await cursor.fetchall()
            audit_policies = [dict(zip(ap_cols, row)) for row in ap_rows]
        except Exception:
            pass
        
        await db.release_connection(conn)
        
        return templates.TemplateResponse(
            "security/audit.html",
            {
                "request": request,
                "username": username,
                "fga_logs": fga_logs,
                "unified_logs": unified_logs,
                "audit_policies": audit_policies,
                "error": None,
            }
        )
    except Exception as e:
        return templates.TemplateResponse(
            "security/audit.html",
            {
                "request": request,
                "username": username,
                "fga_logs": [],
                "unified_logs": [],
                "audit_policies": [],
                "error": str(e),
            }
        )

@router.get("/security/redaction", response_class=HTMLResponse)
async def redaction_page(request: Request):
    """Data Redaction Demo - hiển thị chính sách và dữ liệu bị che."""
    username = require_auth(request)
    
    try:
        conn = await db.get_connection()
        cursor = conn.cursor()
        
        # 1. Lấy Policy Info (Admin View)
        policies = []
        try:
            await cursor.execute("""
                SELECT policy_name, object_name, expression, enable
                FROM redaction_policies
                WHERE object_owner = 'SYSTEM'
            """)
            cols = [desc[0].lower() for desc in cursor.description]
            rows = await cursor.fetchall()
            policies = [dict(zip(cols, row)) for row in rows]
        except Exception:
            pass
            
        # 2. Lấy Columns Info (Admin View)
        columns = []
        try:
            # Use SELECT * to avoid ORA-00904 if column names vary across versions
            await cursor.execute("""
                SELECT *
                FROM redaction_columns
                WHERE object_owner = 'SYSTEM'
            """)
            cols = [desc[0].lower() for desc in cursor.description]
            rows = await cursor.fetchall()
            columns = [dict(zip(cols, row)) for row in rows]
        except Exception as e:
            print(f"Error fetching columns: {e}")
            pass

        await db.release_connection(conn)

        # 3. Lấy dữ liệu mẫu từ USER_INFO với tư cách APP_ADMIN (User thường - bị REDACT)
        # Tạo connection riêng rẽ để demo
        demo_data = []
        demo_error = None
        
        try:
            # Connect as APP_ADMIN - SYNCHRONOUS connection
            dsn = f"{settings.ORACLE_HOST}:{settings.ORACLE_PORT}/{settings.ORACLE_SERVICE_NAME}"
            app_conn = oracledb.connect(
                user="app_admin",
                password="app_admin123", # Password from setup script
                dsn=dsn
            )
            app_cursor = app_conn.cursor()
            
            # Query dữ liệu (APP_ADMIN cần quyền SELECT trên SYSTEM.USER_INFO)
            # This is synchronous, DO NOT AWAIT
            app_cursor.execute("""
                SELECT username, full_name, email, phone 
                FROM SYSTEM.USER_INFO 
                ORDER BY created_at DESC 
                FETCH FIRST 5 ROWS ONLY
            """)
            
            d_cols = [desc[0].lower() for desc in app_cursor.description]
            d_rows = app_cursor.fetchall()
            demo_data = [dict(zip(d_cols, row)) for row in d_rows]
            
            app_cursor.close()
            app_conn.close()
            
        except Exception as e:
            demo_error = f"Lỗi kết nối User thường: {str(e)}"

        return templates.TemplateResponse(
            "security/redaction.html",
            {
                "request": request,
                "username": username,
                "policies": policies,
                "columns": columns,
                "demo_data": demo_data,
                "demo_error": demo_error,
                "error": None,
            }
        )
    except Exception as e:
        return templates.TemplateResponse(
            "security/redaction.html",
            {
                "request": request,
                "username": username,
                "policies": [],
                "columns": [],
                "demo_data": [],
                "demo_error": None,
                "error": str(e),
            }
        )

