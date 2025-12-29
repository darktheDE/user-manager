"""Oracle Security Features routes - VPD, Audit, Database Vault."""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse

from app.presentation.middleware import get_session
from app.presentation.templates import templates
from app.data.oracle.connection import db

router = APIRouter()


def require_auth(request: Request) -> str:
    """Require authentication and return username."""
    session = get_session(request)
    username = session.get("username")
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return username


@router.get("/security", response_class=HTMLResponse)
async def security_index(request: Request):
    """Security features overview page."""
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
    """VPD - show filtered projects based on user department."""
    username = require_auth(request)
    
    try:
        conn = await db.get_connection()
        cursor = conn.cursor()
        
        # Set user context for VPD
        try:
            await cursor.execute("BEGIN set_user_dept_proc(:username); END;", username=username)
        except Exception:
            pass
        
        # Query projects (VPD will filter automatically if policy is active)
        await cursor.execute("""
            SELECT project_id, project_name, department, budget, status, owner_username
            FROM projects
            ORDER BY project_id
        """)
        
        columns = [desc[0].lower() for desc in cursor.description]
        rows = await cursor.fetchall()
        projects = [dict(zip(columns, row)) for row in rows]
        
        # Get VPD policy info
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
    """Audit - show FGA and Unified Audit logs."""
    username = require_auth(request)
    
    try:
        conn = await db.get_connection()
        cursor = conn.cursor()
        
        # FGA Audit Trail
        fga_logs = []
        try:
            await cursor.execute("""
                SELECT 
                    timestamp,
                    db_user,
                    object_schema,
                    object_name,
                    policy_name,
                    sql_text,
                    statement_type
                FROM dba_fga_audit_trail
                WHERE object_name = 'PROJECTS'
                ORDER BY timestamp DESC
                FETCH FIRST 20 ROWS ONLY
            """)
            fga_cols = [desc[0].lower() for desc in cursor.description]
            fga_rows = await cursor.fetchall()
            fga_logs = [dict(zip(fga_cols, row)) for row in fga_rows]
        except Exception:
            pass
        
        # Unified Audit Trail
        unified_logs = []
        try:
            await cursor.execute("""
                SELECT 
                    event_timestamp,
                    dbusername,
                    action_name,
                    object_schema,
                    object_name,
                    sql_text,
                    return_code
                FROM unified_audit_trail
                WHERE object_name = 'PROJECTS'
                   OR action_name IN ('LOGON', 'LOGOFF')
                ORDER BY event_timestamp DESC
                FETCH FIRST 30 ROWS ONLY
            """)
            ua_cols = [desc[0].lower() for desc in cursor.description]
            ua_rows = await cursor.fetchall()
            unified_logs = [dict(zip(ua_cols, row)) for row in ua_rows]
        except Exception:
            pass
        
        # Get audit policies
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


@router.get("/security/dbvault", response_class=HTMLResponse)
async def dbvault_page(request: Request):
    """Database Vault - show realms and command rules."""
    username = require_auth(request)
    
    try:
        conn = await db.get_connection()
        cursor = conn.cursor()
        
        # Check DV status
        dv_status = []
        try:
            await cursor.execute("SELECT * FROM DBA_DV_STATUS")
            dv_cols = [desc[0].lower() for desc in cursor.description]
            dv_rows = await cursor.fetchall()
            dv_status = [dict(zip(dv_cols, row)) for row in dv_rows]
        except Exception:
            pass
        
        # Get Realms
        realms = []
        try:
            await cursor.execute("""
                SELECT realm_name, description, enabled, audit_options
                FROM dvsys.dba_dv_realm
            """)
            r_cols = [desc[0].lower() for desc in cursor.description]
            r_rows = await cursor.fetchall()
            realms = [dict(zip(r_cols, row)) for row in r_rows]
        except Exception:
            pass
        
        # Get Realm Objects
        realm_objects = []
        try:
            await cursor.execute("""
                SELECT realm_name, owner, object_name, object_type
                FROM dvsys.dba_dv_realm_object
            """)
            ro_cols = [desc[0].lower() for desc in cursor.description]
            ro_rows = await cursor.fetchall()
            realm_objects = [dict(zip(ro_cols, row)) for row in ro_rows]
        except Exception:
            pass
        
        # Get Command Rules
        command_rules = []
        try:
            await cursor.execute("""
                SELECT command, rule_set_name, object_owner, object_name, enabled
                FROM dvsys.dba_dv_command_rule
            """)
            cr_cols = [desc[0].lower() for desc in cursor.description]
            cr_rows = await cursor.fetchall()
            command_rules = [dict(zip(cr_cols, row)) for row in cr_rows]
        except Exception:
            pass
        
        await db.release_connection(conn)
        
        return templates.TemplateResponse(
            "security/dbvault.html",
            {
                "request": request,
                "username": username,
                "dv_status": dv_status,
                "realms": realms,
                "realm_objects": realm_objects,
                "command_rules": command_rules,
                "error": None,
            }
        )
    except Exception as e:
        return templates.TemplateResponse(
            "security/dbvault.html",
            {
                "request": request,
                "username": username,
                "dv_status": [],
                "realms": [],
                "realm_objects": [],
                "command_rules": [],
                "error": str(e),
            }
        )
