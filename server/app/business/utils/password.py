"""Tiện ích mã hóa mật khẩu sử dụng bcrypt."""

import bcrypt


def hash_password(password: str) -> str:
    """
    Mã hóa mật khẩu sử dụng bcrypt.
    
    Args:
        password: Mật khẩu dạng plain text
        
    Returns:
        Chuỗi hash bcrypt
    """
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=12)  # 12 rounds đảm bảo bảo mật và hiệu suất
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """
    Xác minh mật khẩu với bcrypt hash.
    
    Args:
        password: Mật khẩu dạng plain text
        password_hash: Chuỗi hash bcrypt
        
    Returns:
        True nếu mật khẩu khớp, False nếu không
    """
    try:
        password_bytes = password.encode('utf-8')
        hash_bytes = password_hash.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hash_bytes)
    except Exception:
        return False
