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
        "phone": "0901234567"
    },
    {
        "username": "HR_USER",
        "password": "hr123",
        "full_name": "HR Manager",
        "email": "hr@company.com",
        "department": "HR",
        "default_tablespace": "USERS",
        "temp_tablespace": "TEMP",
        "phone": "0912345678"
    },
    {
        "username": "IT_USER",
        "password": "it123",
        "full_name": "IT Developer",
        "email": "itdev@company.com",
        "department": "IT",
        "default_tablespace": "USERS",
        "temp_tablespace": "TEMP",
        "phone": "0934567890"
    },
    {
        "username": "FINANCE_USER",
        "password": "finance123",
        "full_name": "Finance Analyst",
        "email": "finance@company.com",
        "department": "FINANCE",
        "default_tablespace": "USERS",
        "temp_tablespace": "TEMP",
        "phone": "0987654321"
    },
    {
        "username": "MARKETING_USER",
        "password": "marketing123",
        "full_name": "Marketing Manager",
        "email": "marketing@company.com",
        "department": "MARKETING",
        "default_tablespace": "USERS",
        "temp_tablespace": "TEMP",
        "phone": "0966888999"
    },
    {
        "username": "nhanvien01",
        "password": "Password123",
        "full_name": "Nhan Vien Demo",
        "email": "nhanvien01@gmail.com",
        "department": "IT",
        "default_tablespace": "USERS",
        "temp_tablespace": "TEMP",
        "phone": "0999888777"
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
    
    cursor = conn.cursor()
    
    # Create Roles
    print("\n[2/6] Creating Roles...")
    for role in TEST_ROLES:
        try:
            if role["password"]:
                await cursor.execute(f"CREATE ROLE {role['name']} IDENTIFIED BY \"{role['password']}\"")
            else:
                await cursor.execute(f"CREATE ROLE {role['name']}")
            print(f"    ✓ Created role: {role['name']}")
        except oracledb.Error as e:
            if "ORA-01921" in str(e):  # Role already exists
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
    
    # Create Oracle Users
    print("\n[4/6] Creating Oracle Users...")
    for user in TEST_USERS:
        try:
            sql = f"""
                CREATE USER {user['username']} IDENTIFIED BY "{user['password']}"
                DEFAULT TABLESPACE {user['default_tablespace']}
                TEMPORARY TABLESPACE {user['temp_tablespace']}
                QUOTA UNLIMITED ON {user['default_tablespace']}
            """
            await cursor.execute(sql)
            await cursor.execute(f"GRANT CREATE SESSION TO {user['username']}")
            print(f"    ✓ Created user: {user['username']}")
        except oracledb.Error as e:
            if "ORA-01920" in str(e):  # User already exists
                print(f"    - User exists: {user['username']}")
            else:
                print(f"    ✗ Error creating {user['username']}: {e}")
    
    # Grant roles to users
    print("\n[5/6] Granting roles to users...")
    for username, role in ROLE_GRANTS:
        try:
            await cursor.execute(f"GRANT {role} TO {username}")
            print(f"    ✓ Granted {role} to {username}")
        except oracledb.Error as e:
            print(f"    - {username} <- {role}: {e}")
    
    # Insert user_info with bcrypt hashes
    print("\n[6/6] Creating user_info records with bcrypt passwords...")
    for user in TEST_USERS:
        password_hash = hash_password(user["password"])
        try:
            # Check if exists
            await cursor.execute(
                "SELECT COUNT(*) FROM user_info WHERE username = :username",
                username=user["username"]
            )
            row = await cursor.fetchone()
            
            if row[0] == 0:
                await cursor.execute("""
                    INSERT INTO user_info (username, password_hash, full_name, email, department)
                    VALUES (:username, :password_hash, :full_name, :email, :department)
                """,
                    username=user["username"],
                    password_hash=password_hash,
                    full_name=user["full_name"],
                    email=user["email"],
                    department=user["department"],
                )
                print(f"    ✓ Created user_info: {user['username']} (hash: {password_hash[:20]}...)")
            else:
                print(f"    - User_info exists: {user['username']}")
        except oracledb.Error as e:
            print(f"    ✗ Error: {e}")
    
    # Insert projects
    print("\n[+] Creating sample projects...")
    for proj in TEST_PROJECTS:
        try:
            await cursor.execute(
                "SELECT COUNT(*) FROM projects WHERE project_name = :name",
                name=proj["name"]
            )
            row = await cursor.fetchone()
            if row[0] == 0:
                await cursor.execute("""
                    INSERT INTO projects (project_name, department, budget, status, owner_username)
                    VALUES (:name, :dept, :budget, 'ACTIVE', :owner)
                """,
                    name=proj["name"],
                    dept=proj["department"],
                    budget=proj["budget"],
                    owner=proj["owner"],
                )
                print(f"    ✓ Created project: {proj['name']}")
        except oracledb.Error as e:
            print(f"    - {proj['name']}: {e}")
    
    await conn.commit()
    await conn.close()
    
    print("\n" + "=" * 60)
    print("✅ Database seeding completed!")
    print("=" * 60)
    print("\nTest Credentials:")
    print("-" * 40)
    for user in TEST_USERS:
        print(f"  {user['username']:15} / {user['password']}")
    print("-" * 40)


if __name__ == "__main__":
    asyncio.run(main())
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
        print("    ✓ Connected to Oracle Database as SYSTEM")
    except Exception as e:
        print(f"    ✗ Connection failed: {e}")
        return

    try:
        cursor = conn.cursor()

        # 1. Create Users
        print("\n[2/6] Creating Oracle Users...")
        for user_data in TEST_USERS:
            username = user_data['username']
            password = user_data['password']
            
            try:
                # Check if user exists
                await cursor.execute("SELECT count(*) FROM dba_users WHERE username = :1", [username.upper()])
                exists = (await cursor.fetchone())[0]
                
                if exists:
                    print(f"    → User {username} already exists")
                    # Reset password to ensure we know it
                    await cursor.execute(f"ALTER USER {username} IDENTIFIED BY \"{password}\"")
                else:
                    print(f"    + Creating user {username}...")
                    await cursor.execute(f"CREATE USER {username} IDENTIFIED BY \"{password}\"")
                    await cursor.execute(f"GRANT CONNECT, RESOURCE TO {username}")
                    await cursor.execute(f"GRANT UNLIMITED TABLESPACE TO {username}")
            except Exception as e:
                print(f"    ✗ Error managing user {username}: {e}")

        # 2. Populate USER_INFO table (with hashed passwords)
        print("\n[3/6] Populating USER_INFO table...")
        # Clear existing data first? Maybe not needed if we want to preserve
        # But for seed script, usually safe to clear valid test data or UPSERT
        
        for user_data in TEST_USERS:
            username = user_data['username']
            # Only insert if not exists in USER_INFO
            try:
                await cursor.execute("SELECT count(*) FROM user_info WHERE username = :1", [username])
                exists = (await cursor.fetchone())[0]
                
                if not exists:
                    print(f"    + Inserting {username} into USER_INFO...")
                    pwd_hash = hash_password(user_data['password'])
                    phone = user_data.get('phone', '')
                    await cursor.execute("""
                        INSERT INTO user_info 
                        (username, password_hash, full_name, email, phone, department, created_at)
                        VALUES (:1, :2, :3, :4, :5, :6, CURRENT_TIMESTAMP)
                    """, [
                        username, 
                        pwd_hash, 
                        user_data['full_name'], 
                        user_data['email'],
                        phone,
                        user_data['department']
                    ])
                else:
                    # Update phone/email if needed (to ensure test data is correct)
                    print(f"    → Updating {username} info...")
                    phone = user_data.get('phone', '')
                    await cursor.execute("""
                        UPDATE user_info 
                        SET email = :1, phone = :2, updated_at = CURRENT_TIMESTAMP
                        WHERE username = :3
                    """, [user_data['email'], phone, username])
                    
            except Exception as e:
                 print(f"    ✗ Error inserting {username} into USER_INFO: {e}")

        # 3. Create Roles and Grants
        print("\n[4/6] Creating Roles & Grants...")
        for role in TEST_ROLES:
            role_name = role['name']
            try:
                await cursor.execute("SELECT count(*) FROM dba_roles WHERE role = :1", [role_name])
                exists = (await cursor.fetchone())[0]
                
                if not exists:
                    print(f"    + Creating role {role_name}...")
                    if role['password']:
                        await cursor.execute(f"CREATE ROLE {role_name} IDENTIFIED BY \"{role['password']}\"")
                    else:
                        await cursor.execute(f"CREATE ROLE {role_name}")
            except Exception as e:
                print(f"    ✗ Error creating role {role_name}: {e}")

        # Grants
        for user, role in ROLE_GRANTS:
            try:
                await cursor.execute(f"GRANT {role} TO {user}")
                print(f"    + Granted {role} to {user}")
            except Exception:
                pass # Ignore if already granted

        # 4. Populate PROJECTS
        print("\n[5/6] Populating PROJECTS table...")
        for proj in TEST_PROJECTS:
            try:
                await cursor.execute("""
                    MERGE INTO projects p
                    USING dual ON (p.project_name = :p_name)
                    WHEN NOT MATCHED THEN
                        INSERT (project_name, department, budget, owner_username)
                        VALUES (:p_name, :p_dept, :p_budget, :p_owner)
                """, {
                    "p_name": proj['name'], 
                    "p_dept": proj['department'], 
                    "p_budget": proj['budget'], 
                    "p_owner": proj['owner']
                })
                print(f"    + Project: {proj['name']}")
            except Exception as e:
                print(f"    ✗ Error inserting project {proj['name']}: {e}")

        await conn.commit()
        print("\n[6/6] Committing changes...")

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        await conn.rollback()
    finally:
        # Cursor.close() is synchronous in python-oracledb even for async connections
        if cursor:
            cursor.close()
        await conn.close()
        print("\nDone!")


if __name__ == "__main__":
    # Fix for Windows asyncio loop
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
