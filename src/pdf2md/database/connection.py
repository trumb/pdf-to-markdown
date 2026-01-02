"""SQLite database connection management."""

import asyncio
import logging
from pathlib import Path
from typing import Any, Optional

import aiosqlite

logger = logging.getLogger(__name__)


class Database:
    """
    Async SQLite database connection manager.
    
    Handles connection pooling, schema initialization, and query execution.
    """

    def __init__(self, strDbPath: str) -> None:
        """
        Initialize database connection.
        
        Args:
            strDbPath: Path to SQLite database file
        """
        self.strDbPath: str = strDbPath
        self.connection: Optional[aiosqlite.Connection] = None
        self._lock: asyncio.Lock = asyncio.Lock()

    async def connect(self) -> None:
        """
        Open database connection and initialize schema.
        
        Creates database file if it doesn't exist and runs schema.sql.
        """
        async with self._lock:
            if self.connection is not None:
                return

            # Create parent directory if needed
            pathDb = Path(self.strDbPath)
            pathDb.parent.mkdir(parents=True, exist_ok=True)

            # Connect to database
            self.connection = await aiosqlite.connect(self.strDbPath)
            self.connection.row_factory = aiosqlite.Row

            # Enable foreign keys
            await self.connection.execute("PRAGMA foreign_keys = ON")

            # Initialize schema
            await self._initialize_schema()

            logger.info(f"Database connected: {self.strDbPath}")

    async def _initialize_schema(self) -> None:
        """Load and execute schema.sql if tables don't exist."""
        assert self.connection is not None

        # Check if tables exist
        cursor = await self.connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='tokens'"
        )
        row = await cursor.fetchone()
        await cursor.close()

        if row is None:
            # Load schema
            pathSchema = Path(__file__).parent / "schema.sql"
            strSchemaContent = pathSchema.read_text()

            # Execute schema
            await self.connection.executescript(strSchemaContent)
            await self.connection.commit()
            logger.info("Database schema initialized")

    async def disconnect(self) -> None:
        """Close database connection."""
        async with self._lock:
            if self.connection is not None:
                await self.connection.close()
                self.connection = None
                logger.info("Database disconnected")

    async def execute(self, strQuery: str, tupleParams: tuple[Any, ...] = ()) -> None:
        """
        Execute a write query (INSERT, UPDATE, DELETE).
        
        Args:
            strQuery: SQL query string
            tupleParams: Query parameters
        """
        assert self.connection is not None
        await self.connection.execute(strQuery, tupleParams)
        await self.connection.commit()

    async def fetch_one(
        self, strQuery: str, tupleParams: tuple[Any, ...] = ()
    ) -> Optional[aiosqlite.Row]:
        """
        Fetch single row from database.
        
        Args:
            strQuery: SQL query string
            tupleParams: Query parameters
            
        Returns:
            Row dict or None if not found
        """
        assert self.connection is not None
        cursor = await self.connection.execute(strQuery, tupleParams)
        row = await cursor.fetchone()
        await cursor.close()
        return row

    async def fetch_all(
        self, strQuery: str, tupleParams: tuple[Any, ...] = ()
    ) -> list[aiosqlite.Row]:
        """
        Fetch all rows from database.
        
        Args:
            strQuery: SQL query string
            tupleParams: Query parameters
            
        Returns:
            List of row dicts
        """
        assert self.connection is not None
        cursor = await self.connection.execute(strQuery, tupleParams)
        listRows = await cursor.fetchall()
        await cursor.close()
        return listRows

    async def execute_many(
        self, strQuery: str, listParams: list[tuple[Any, ...]]
    ) -> None:
        """
        Execute multiple write queries in batch.
        
        Args:
            strQuery: SQL query string
            listParams: List of parameter tuples
        """
        assert self.connection is not None
        await self.connection.executemany(strQuery, listParams)
        await self.connection.commit()
