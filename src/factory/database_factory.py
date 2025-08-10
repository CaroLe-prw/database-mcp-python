from typing import Dict, Type

from src.model import DatabaseConfig
from src.strategy import DatabaseStrategy, MySQLStrategy


class DatabaseStrategyFactory:
    _strategies: Dict[str, Type[DatabaseStrategy]] = {
        "mysql": MySQLStrategy,
    }

    @classmethod
    def create_strategy(cls, db_type: str, **kwargs) -> DatabaseStrategy:
        strategy_class = cls._strategies[db_type.lower()]
        if not strategy_class:
            raise ValueError("Database type not supported")

        return strategy_class(DatabaseConfig(**kwargs))

    @classmethod
    def get_database_strategy(cls, database_type: str, **connection_params):
        return cls.create_strategy(database_type, **connection_params)
