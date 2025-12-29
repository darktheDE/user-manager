"""Oracle database connection management."""

import oracledb
from app.config import settings


class OracleConnection:
    """Oracle database connection manager."""

    def __init__(self):
        """Initialize connection pool."""
        self.pool: oracledb.ConnectionPool | None = None

    async def create_pool(self) -> None:
        """Create connection pool."""
        dsn = oracledb.makedsn(
            host=settings.ORACLE_HOST,
            port=settings.ORACLE_PORT,
            service_name=settings.ORACLE_SERVICE_NAME,
        )

        self.pool = await oracledb.create_pool_async(
            user=settings.ORACLE_USER,
            password=settings.ORACLE_PASSWORD,
            dsn=dsn,
            min=1,
            max=10,
            increment=1,
        )

    async def close_pool(self) -> None:
        """Close connection pool."""
        if self.pool:
            await self.pool.close()
            self.pool = None

    async def get_connection(self) -> oracledb.Connection:
        """Get connection from pool."""
        if not self.pool:
            raise RuntimeError("Connection pool not initialized")
        return await self.pool.acquire()

    async def release_connection(self, conn: oracledb.Connection) -> None:
        """Release connection back to pool."""
        if self.pool:
            await self.pool.release(conn)


# Global connection instance
db = OracleConnection()

