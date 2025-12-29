"""Quản lý kết nối Oracle Database."""

import oracledb
from app.config import settings


class OracleConnection:
    """Lớp quản lý kết nối Oracle Database."""

    def __init__(self):
        """Khởi tạo connection pool."""
        self.pool: oracledb.AsyncConnectionPool | None = None

    async def create_pool(self) -> None:
        """Tạo connection pool."""
        dsn = oracledb.makedsn(
            host=settings.ORACLE_HOST,
            port=settings.ORACLE_PORT,
            service_name=settings.ORACLE_SERVICE_NAME,
        )

        # create_pool_async() là hàm đồng bộ nhưng trả về AsyncConnectionPool
        # Đây là hàm đồng bộ tạo pool bất đồng bộ
        self.pool = oracledb.create_pool_async(
            user=settings.ORACLE_USER,
            password=settings.ORACLE_PASSWORD,
            dsn=dsn,
            min=1,
            max=10,
            increment=1,
        )

    async def close_pool(self) -> None:
        """Đóng connection pool."""
        if self.pool:
            await self.pool.close()
            self.pool = None

    async def get_connection(self) -> oracledb.Connection:
        """Lấy connection từ pool."""
        if not self.pool:
            raise RuntimeError("Connection pool chưa được khởi tạo")
        return await self.pool.acquire()

    async def release_connection(self, conn: oracledb.Connection) -> None:
        """Trả connection về pool."""
        if self.pool:
            await self.pool.release(conn)


# Instance kết nối toàn cục
db = OracleConnection()
