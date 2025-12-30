"""Token management with bcrypt hashing."""

import base64
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Optional

import bcrypt

from pdf2md.auth.models import Role, Token, User
from pdf2md.database import Database


class TokenManager:
    """
    Manage API tokens with bcrypt hashing.
    
    Handles token creation, validation, and CRUD operations.
    """

    def __init__(self, database: Database) -> None:
        """
        Initialize token manager.
        
        Args:
            database: Database connection
        """
        self.database: Database = database

    def generate_token(self) -> str:
        """
        Generate a new API token.
        
        Format: pdf2md_<base64_encoded_random_256_bits>
        
        Returns:
            Token string (e.g., "pdf2md_aGVsbG93b3JsZC4uLg==")
        """
        bytesRandom = secrets.token_bytes(32)  # 256 bits
        strBase64 = base64.urlsafe_b64encode(bytesRandom).decode("ascii").rstrip("=")
        return f"pdf2md_{strBase64}"

    async def create_token(
        self,
        strUserId: str,
        role: Role,
        optExpiresDays: Optional[int] = None,
        optCreatedBy: Optional[str] = None,
        intRateLimit: Optional[int] = None,
    ) -> tuple[str, str]:
        """
        Create a new API token.
        
        Args:
            strUserId: Human-readable user identifier
            role: User role
            optExpiresDays: Days until expiration (None = never expires)
            optCreatedBy: token_id of creator (for audit)
            intRateLimit: Custom rate limit (default based on role)
            
        Returns:
            Tuple of (token_id, token_string)
        """
        # Generate token
        strToken = self.generate_token()
        strTokenId = str(uuid.uuid4())

        # Hash token
        bytesTokenHash = bcrypt.hashpw(strToken.encode("utf-8"), bcrypt.gensalt())
        strTokenHash = bytesTokenHash.decode("utf-8")

        # Calculate expiry
        datetimeNow = datetime.now()
        optExpiresAt: Optional[datetime] = None
        if optExpiresDays is not None:
            optExpiresAt = datetimeNow + timedelta(days=optExpiresDays)

        # Set rate limit based on role if not provided
        if intRateLimit is None:
            dictRateLimits = {
                Role.ADMIN: 1000,
                Role.JOB_MANAGER: 500,
                Role.JOB_WRITER: 100,
                Role.JOB_READER: 50,
            }
            intRateLimit = dictRateLimits[role]

        # Insert into database
        await self.database.execute(
            """
            INSERT INTO tokens (
                token_id, token_hash, user_id, role, created_at, expires_at,
                is_active, rate_limit, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                strTokenId,
                strTokenHash,
                strUserId,
                role.value,
                datetimeNow.isoformat(),
                optExpiresAt.isoformat() if optExpiresAt else None,
                1,
                intRateLimit,
                optCreatedBy,
            ),
        )

        return strTokenId, strToken

    async def validate_token(self, strToken: str) -> Optional[User]:
        """
        Validate API token and return User if valid.
        
        Args:
            strToken: Token string to validate
            
        Returns:
            User object if valid, None otherwise
        """
        # Check token format
        if not strToken.startswith("pdf2md_"):
            return None

        # Get all tokens from database
        listRows = await self.database.fetch_all("SELECT * FROM tokens WHERE is_active = 1")

        # Check each token hash
        for row in listRows:
            strStoredHash = row["token_hash"]
            
            # Verify bcrypt hash
            boolMatches = bcrypt.checkpw(
                strToken.encode("utf-8"), strStoredHash.encode("utf-8")
            )

            if boolMatches:
                # Check expiry
                strExpiresAt = row["expires_at"]
                if strExpiresAt:
                    datetimeExpiresAt = datetime.fromisoformat(strExpiresAt)
                    if datetime.now() > datetimeExpiresAt:
                        return None

                # Return user
                return User(
                    strTokenId=row["token_id"],
                    strUserId=row["user_id"],
                    role=Role(row["role"]),
                    intRateLimit=row["rate_limit"],
                    boolIsActive=bool(row["is_active"]),
                    optExpiresAt=datetime.fromisoformat(strExpiresAt) if strExpiresAt else None,
                )

        return None

    async def get_token_by_id(self, strTokenId: str) -> Optional[Token]:
        """
        Get token by token_id.
        
        Args:
            strTokenId: Token UUID
            
        Returns:
            Token object or None
        """
        row = await self.database.fetch_one(
            "SELECT * FROM tokens WHERE token_id = ?", (strTokenId,)
        )

        if row is None:
            return None

        strExpiresAt = row["expires_at"]
        return Token(
            strTokenId=row["token_id"],
            strTokenHash=row["token_hash"],
            strUserId=row["user_id"],
            role=Role(row["role"]),
            datetimeCreatedAt=datetime.fromisoformat(row["created_at"]),
            optExpiresAt=datetime.fromisoformat(strExpiresAt) if strExpiresAt else None,
            boolIsActive=bool(row["is_active"]),
            intRateLimit=row["rate_limit"],
            optScopes=row["scopes"],
            optCreatedBy=row["created_by"],
        )

    async def list_tokens(self) -> list[Token]:
        """
        List all tokens.
        
        Returns:
            List of Token objects
        """
        listRows = await self.database.fetch_all("SELECT * FROM tokens ORDER BY created_at DESC")

        listTokens: list[Token] = []
        for row in listRows:
            strExpiresAt = row["expires_at"]
            listTokens.append(
                Token(
                    strTokenId=row["token_id"],
                    strTokenHash=row["token_hash"],
                    strUserId=row["user_id"],
                    role=Role(row["role"]),
                    datetimeCreatedAt=datetime.fromisoformat(row["created_at"]),
                    optExpiresAt=datetime.fromisoformat(strExpiresAt) if strExpiresAt else None,
                    boolIsActive=bool(row["is_active"]),
                    intRateLimit=row["rate_limit"],
                    optScopes=row["scopes"],
                    optCreatedBy=row["created_by"],
                )
            )

        return listTokens

    async def revoke_token(self, strTokenId: str) -> bool:
        """
        Permanently delete a token.
        
        Args:
            strTokenId: Token UUID to revoke
            
        Returns:
            True if token was revoked, False if not found
        """
        token = await self.get_token_by_id(strTokenId)
        if token is None:
            return False

        await self.database.execute("DELETE FROM tokens WHERE token_id = ?", (strTokenId,))
        return True

    async def disable_token(self, strTokenId: str) -> bool:
        """
        Temporarily disable a token (reversible).
        
        Args:
            strTokenId: Token UUID to disable
            
        Returns:
            True if token was disabled, False if not found
        """
        token = await self.get_token_by_id(strTokenId)
        if token is None:
            return False

        await self.database.execute(
            "UPDATE tokens SET is_active = 0 WHERE token_id = ?", (strTokenId,)
        )
        return True

    async def enable_token(self, strTokenId: str) -> bool:
        """
        Re-enable a disabled token.
        
        Args:
            strTokenId: Token UUID to enable
            
        Returns:
            True if token was enabled, False if not found
        """
        token = await self.get_token_by_id(strTokenId)
        if token is None:
            return False

        await self.database.execute(
            "UPDATE tokens SET is_active = 1 WHERE token_id = ?", (strTokenId,)
        )
        return True

    async def update_rate_limit(self, strTokenId: str, intRateLimit: int) -> bool:
        """
        Update token rate limit.
        
        Args:
            strTokenId: Token UUID
            intRateLimit: New rate limit (requests per minute)
            
        Returns:
            True if updated, False if not found
        """
        token = await self.get_token_by_id(strTokenId)
        if token is None:
            return False

        await self.database.execute(
            "UPDATE tokens SET rate_limit = ? WHERE token_id = ?", (intRateLimit, strTokenId)
        )
        return True

    async def log_token_usage(
        self,
        strTokenId: str,
        strEndpoint: str,
        strMethod: str,
        intStatusCode: int,
        optRequestSizeBytes: Optional[int] = None,
        optResponseTimeMs: Optional[int] = None,
    ) -> None:
        """
        Log token usage for audit trail.
        
        Args:
            strTokenId: Token UUID
            strEndpoint: API endpoint path
            strMethod: HTTP method
            intStatusCode: HTTP status code
            optRequestSizeBytes: Request size in bytes
            optResponseTimeMs: Response time in milliseconds
        """
        await self.database.execute(
            """
            INSERT INTO token_usage (
                token_id, timestamp, endpoint, method, request_size_bytes,
                response_time_ms, status_code
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                strTokenId,
                datetime.now().isoformat(),
                strEndpoint,
                strMethod,
                optRequestSizeBytes,
                optResponseTimeMs,
                intStatusCode,
            ),
        )

    async def get_token_usage(
        self, strTokenId: str, intDays: int = 7
    ) -> list[dict[str, any]]:
        """
        Get token usage audit trail.
        
        Args:
            strTokenId: Token UUID
            intDays: Number of days to look back
            
        Returns:
            List of usage records
        """
        datetimeCutoff = datetime.now() - timedelta(days=intDays)
        listRows = await self.database.fetch_all(
            """
            SELECT * FROM token_usage
            WHERE token_id = ? AND timestamp >= ?
            ORDER BY timestamp DESC
            """,
            (strTokenId, datetimeCutoff.isoformat()),
        )

        return [dict(row) for row in listRows]