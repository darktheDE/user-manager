"""
Database Seed Script
====================
Tạo test users, roles, và dữ liệu mẫu với bcrypt password hash.

Usage:
    cd server
    python scripts/seed_database.py
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bcrypt
import oracledb

# Oracle connection settings
ORACLE_DSN = "localhost:1521/FREEPDB1"
ORACLE_USER = "system"
ORACLE_PASSWORD = "oracle123"


def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')


# Test Users Configuration
TEST_USERS = [
    {
        "username": "ADMIN",
        "password": "admin123",
        "full_name": "System Administrator",
        "email": "admin@company.com",
        "department": "IT",
        "default_tablespace": "USERS",
        "temp_tablespace": "TEMP",
        "phone": "0901234567",
        "address": "123 Main St, IT District"
    },
    {
        "username": "HR_USER",
        "password": "hr123",
        "full_name": "HR Manager",
        "email": "hr@company.com",
        "department": "HR",
        "default_tablespace": "USERS",
        "temp_tablespace": "TEMP",
        "phone": "0912345678",
        "address": "456 Office Rd, HR Park"
    },
    {
        "username": "IT_USER",
        "password": "it123",
        "full_name": "IT Developer",
        "email": "itdev@company.com",
        "department": "IT",
        "default_tablespace": "USERS",
        "temp_tablespace": "TEMP",
        "phone": "0934567890",
        "address": "789 Dev Ave, Tech Zone"
    },
    {
        "username": "FINANCE_USER",
        "password": "finance123",
        "full_name": "Finance Analyst",
        "email": "finance@company.com",
        "department": "FINANCE",
        "default_tablespace": "USERS",
        "temp_tablespace": "TEMP",
        "phone": "0987654321",
        "address": "321 Money Way, Finance Square"
    },
    {
        "username": "MARKETING_USER",
        "password": "marketing123",
        "full_name": "Marketing Manager",
        "email": "marketing@company.com",
        "department": "MARKETING",
        "default_tablespace": "USERS",
        "temp_tablespace": "TEMP",
        "phone": "0966888999",
        "address": "654 Market St, Promo Area"
    },
    {
        "username": "nhanvien01",
        "password": "Password123",
        "full_name": "Nhan Vien Demo",
        "email": "nhanvien01@gmail.com",
        "department": "IT",
        "default_tablespace": "USERS",
        "temp_tablespace": "TEMP",
        "phone": "0999888777",
        "address": "987 Demo Ln, Testing Ground"
    },
]

# Test Roles Configuration
TEST_ROLES = [
    {"name": "ADMIN_ROLE", "password": None},
    {"name": "HR_ROLE", "password": None},
    {"name": "IT_ROLE", "password": None},
    {"name": "FINANCE_ROLE", "password": None},
    {"name": "MARKETING_ROLE", "password": None},
    {"name": "READONLY_ROLE", "password": None},
    {"name": "SECURE_ROLE", "password": "secure123"},  # Role với password
]

# Role Grants
ROLE_GRANTS = [
    ("ADMIN", "ADMIN_ROLE"),
    ("HR_USER", "HR_ROLE"),
    ("IT_USER", "IT_ROLE"),
    ("FINANCE_USER", "FINANCE_ROLE"),
    ("MARKETING_USER", "MARKETING_ROLE"),
    # Grant READONLY_ROLE cho tất cả
    ("HR_USER", "READONLY_ROLE"),
    ("IT_USER", "READONLY_ROLE"),
    ("FINANCE_USER", "READONLY_ROLE"),
    ("MARKETING_USER", "READONLY_ROLE"),
]

# Test Projects
TEST_PROJECTS = [
    {"name": "Website Redesign", "department": "IT", "budget": 50000, "owner": "IT_USER"},
    {"name": "Mobile App", "department": "IT", "budget": 150000, "owner": "IT_USER"},
    {"name": "HR System Upgrade", "department": "HR", "budget": 75000, "owner": "HR_USER"},
    {"name": "Marketing Campaign Q1", "department": "MARKETING", "budget": 25000, "owner": "MARKETING_USER"},
    {"name": "Financial Audit 2024", "department": "FINANCE", "budget": 100000, "owner": "FINANCE_USER"},
    {"name": "Employee Training", "department": "HR", "budget": 30000, "owner": "HR_USER"},
]


import subprocess


async def run_setup_scripts():
    """Run SQL scripts in scripts/setup folder via SQLPlus in Docker."""
    print("\n[0/6] Executing Setup SQL Scripts...")
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    setup_dir = os.path.join(current_dir, 'setup')
    
    if not os.path.exists(setup_dir):
        print("    ⚠ Setup directory not found!")
        return

    # Get .sql files, sorted by name
    sql_files = sorted([f for f in os.listdir(setup_dir) if f.endswith('.sql')])
    
    if not sql_files:
        print("    → No SQL scripts found")
        return
    
    for sql_file in sql_files:
        file_path = os.path.join(setup_dir, sql_file)
        print(f"    Target: {sql_file}...")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()

            # Standard SYSTEM connection for all scripts
            cmd = ["docker", "exec", "-i", "oracle-db-23ai", "sqlplus", "-S", 
                   "system/oracle123@FREEPDB1"]
            process = subprocess.Popen(
                cmd, 
                stdin=subprocess.PIPE, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8'
            )
            
            stdout, stderr = process.communicate(input=sql_content, timeout=120)
            
            if process.returncode != 0:
                print(f"    ✗ Failed to execute {sql_file}")
                print(f"    ERROR: {stderr}")
            else:
                # Check for common SQLPlus errors in output even if return code is 0
                # Filter out benign errors
                benign_errors = ['ORA-01920', 'ORA-00955', 'ORA-01921', 'ORA-00942', 'ORA-46358']
                has_real_error = "ORA-" in stdout and not any(e in stdout for e in benign_errors)
                
                if has_real_error:
                    # Extract error line
                    error_lines = [l for l in stdout.split('\n') if 'ORA-' in l][:3]
                    print(f"    ⚠ Warnings in {sql_file}:")
                    for line in error_lines:
                        print(f"      {line.strip()}")
                else:
                    print(f"    ✓ Executed {sql_file}")
                     
        except subprocess.TimeoutExpired:
            print(f"    ✗ Timeout executing {sql_file}")
            process.kill()
        except Exception as e:
            print(f"    ✗ Error running script: {e}")



async def main():
    """Main seed function."""
    print("=" * 60)
    print("Database Seed Script")
    print("=" * 60)
    
    # 0. Run Setup Scripts
    await run_setup_scripts()
    
    # Connect to Oracle
    print("\n[1/6] Connecting to Oracle (Runtime Data)...")
    try:
        conn = await oracledb.connect_async(
            user=ORACLE_USER,
            password=ORACLE_PASSWORD,
            dsn=ORACLE_DSN,
        )
        print(f"    ✓ Connected as {ORACLE_USER}")
    except Exception as e:
        print(f"    ✗ Connection failed: {e}")
        return
    
    try:
        cursor = conn.cursor()

        # 1. Create Roles
        print("\n[2/6] Creating Roles...")
        for role in TEST_ROLES:
            try:
                if role["password"]:
                    await cursor.execute(f"CREATE ROLE {role['name']} IDENTIFIED BY \"{role['password']}\"")
                else:
                    await cursor.execute(f"CREATE ROLE {role['name']}")
                print(f"    ✓ Created role: {role['name']}")
            except oracledb.Error as e:
                if "ORA-01921" in str(e):
                    print(f"    - Role exists: {role['name']}")
                else:
                    print(f"    ✗ Error creating {role['name']}: {e}")

        # Grant privileges to roles
        print("\n[3/6] Granting privileges to roles...")
        role_privs = {
            "ADMIN_ROLE": ["CREATE SESSION", "CREATE USER", "ALTER USER", "DROP USER", "CREATE ROLE"],
            "HR_ROLE": ["CREATE SESSION"],
            "IT_ROLE": ["CREATE SESSION", "CREATE TABLE"],
            "FINANCE_ROLE": ["CREATE SESSION"],
            "MARKETING_ROLE": ["CREATE SESSION"],
            "READONLY_ROLE": ["CREATE SESSION"],
        }
        for role, privs in role_privs.items():
            for priv in privs:
                try:
                    await cursor.execute(f"GRANT {priv} TO {role}")
                except oracledb.Error:
                    pass
        print("    ✓ Privileges granted to roles")

        # 2. Create Oracle Users
        print("\n[4/6] Creating Oracle Users...")
        for user_data in TEST_USERS:
            username = user_data['username']
            password = user_data['password']
            try:
                sql = f"""
                    CREATE USER {username} IDENTIFIED BY "{password}"
                    DEFAULT TABLESPACE {user_data['default_tablespace']}
                    TEMPORARY TABLESPACE {user_data['temp_tablespace']}
                    QUOTA UNLIMITED ON {user_data['default_tablespace']}
                """
                await cursor.execute(sql)
                await cursor.execute(f"GRANT CREATE SESSION, RESOURCE TO {username}")
                print(f"    ✓ Created user: {username}")
            except oracledb.Error as e:
                if "ORA-01920" in str(e):
                    print(f"    - User exists: {username}")
                else:
                    print(f"    ✗ Error creating {username}: {e}")

        # Grants
        print("\n[5/6] Granting roles to users...")
        for user, role in ROLE_GRANTS:
            try:
                await cursor.execute(f"GRANT {role} TO {user}")
                print(f"    ✓ Granted {role} to {user}")
            except oracledb.Error:
                pass

        # 3. Populate USER_INFO table
        print("\n[3/6] Populating USER_INFO table...")
        for user_data in TEST_USERS:
            username = user_data['username']
            try:
                await cursor.execute("SELECT count(*) FROM user_info WHERE username = :1", [username])
                exists = (await cursor.fetchone())[0]
                
                pwd_hash = hash_password(user_data['password'])
                phone = user_data.get('phone', '')
                address = user_data.get('address', '')
                
                if not exists:
                    await cursor.execute("""
                        INSERT INTO user_info 
                        (username, password_hash, full_name, email, phone, address, department, created_at)
                        VALUES (:1, :2, :3, :4, :5, :6, :7, CURRENT_TIMESTAMP)
                    """, [username, pwd_hash, user_data['full_name'], user_data['email'], phone, address, user_data['department']])
                    print(f"    ✓ Created user_info: {username}")
                else:
                    await cursor.execute("""
                        UPDATE user_info 
                        SET email = :1, phone = :2, address = :3, updated_at = CURRENT_TIMESTAMP
                        WHERE username = :4
                    """, [user_data['email'], phone, address, username])
                    print(f"    → Updated user_info: {username}")
            except Exception as e:
                 print(f"    ✗ Error managing user_info for {username}: {e}")

        # 4. Populate PROJECTS
        print("\n[+] Populating PROJECTS table...")
        for proj in TEST_PROJECTS:
            try:
                # Check if exists first (to avoid ORA-28138 during MERGE)
                await cursor.execute("SELECT count(*) FROM projects WHERE project_name = :p_name", {"p_name": proj['name']})
                exists = (await cursor.fetchone())[0]
                
                if not exists:
                    await cursor.execute("""
                        INSERT INTO projects (project_name, department, budget, owner_username)
                        VALUES (:p_name, :p_dept, :p_budget, :p_owner)
                    """, {
                        "p_name": proj['name'], 
                        "p_dept": proj['department'], 
                        "p_budget": proj['budget'], 
                        "p_owner": proj['owner']
                    })
                    print(f"    ✓ Created project: {proj['name']}")
                else:
                    print(f"    - Project exists: {proj['name']}")
            except Exception as e:
                print(f"    ✗ Error managing project {proj['name']}: {e}")

        await conn.commit()
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        await conn.rollback()
    finally:
        if cursor:
            cursor.close()
        await conn.close()
        print("\nDone!")


if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
