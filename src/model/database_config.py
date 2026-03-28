from dataclasses import dataclass
from typing import Optional


@dataclass
class DatabaseConfig:
    """Database configuration class"""

    host: str
    port: int
    user: str
    password: str
    database: str
    schema: Optional[str] = None
    minCached: Optional[int] = None
    maxCached: Optional[int] = None
    maxConnections: Optional[int] = None
