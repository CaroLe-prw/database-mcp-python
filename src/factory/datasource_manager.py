from typing import Dict, Optional, Any

from src.factory.config_loader import load_config
from src.factory.database_factory import DatabaseStrategyFactory
from src.strategy import DatabaseStrategy


class DataSourceManager:
    """Multi-data source manager"""

    # Class-level configuration cache
    _cached_config: Optional[Dict[str, Any]] = None
    _config_loaded: bool = False

    def __init__(self):
        self._data_sources: Dict[str, DatabaseStrategy] = {}
        self._default_source: Optional[str] = None
        self._config: Dict[str, Any] = {}

        # Automatically load configuration
        self._load_config()

    def _load_config(self):
        """Load configuration and initialize data sources (using cache to avoid repeated reads)"""
        # If configuration is already cached, use cache directly
        if DataSourceManager._cached_config is not None:
            self._config = DataSourceManager._cached_config
        else:
            # First load, read from file and cache
            self._config = load_config()
            DataSourceManager._cached_config = self._config
            DataSourceManager._config_loaded = True

        # Load all data sources
        for name, ds_config in self._config.get('datasources', {}).items():
            # Create configuration copy to avoid modifying original
            config_copy = ds_config.copy()
            db_type = config_copy.pop('type', None)
            if not db_type:
                raise ValueError(f"Data source '{name}' missing 'type' field")

            # Create data source strategy and add to dictionary
            strategy = DatabaseStrategyFactory.get_database_strategy(
                db_type, **config_copy
            )
            self._data_sources[name] = strategy

        # Set default data source
        default = self._config.get('default')
        if default and default in self._data_sources:
            self._default_source = default
        elif self._data_sources:
            # If no default specified, use first data source
            self._default_source = next(iter(self._data_sources.keys()))

    def get_data_source(self, name: str = None) -> DatabaseStrategy:
        """
        Get data source
        :param name: Data source name, returns default data source when None
        :return: Database strategy instance
        """
        if name is None:
            name = self._default_source

        if not name:
            raise ValueError("No available data sources")

        if name not in self._data_sources:
            available = list(self._data_sources.keys())
            raise ValueError(
                f"Data source '{name}' does not exist. Available data sources: {', '.join(available)}"
            )

        return self._data_sources[name]

    def set_default(self, name: str) -> str:
        """
        Set default data source
        :param name: Data source name
        :return: Success message
        """
        if name not in self._data_sources:
            available = list(self._data_sources.keys())
            raise ValueError(
                f"Data source '{name}' does not exist. Available data sources: {', '.join(available)}"
            )

        self._default_source = name
        return f"Default data source switched to: {name}"

    def list_data_sources(self) -> Dict[str, Dict[str, Any]]:
        """
        List all data sources
        :return: Data source information dictionary
        """
        result = {}
        for name, strategy in self._data_sources.items():
            # Get data source type
            strategy_type = strategy.__class__.__name__.replace('Strategy', '')

            # Get configuration info (excluding password)
            config = self._config['datasources'].get(name, {})
            safe_config = {
                'type': strategy_type.lower(),
                'host': config.get('host', 'unknown'),
                'port': config.get('port', 'unknown'),
                'database': config.get('database', 'unknown'),
                'user': config.get('user', 'unknown'),
                'is_default': name == self._default_source
            }

            result[name] = safe_config

        return result

    def get_current_datasource(self) -> str:
        """
        Get current default data source name
        :return: Current default data source name
        """
        if not self._default_source:
            raise ValueError("No default data source set")
        return self._default_source

    def execute_on_datasource(self, name: str, method: str, *args, **kwargs):
        """
        Execute method on specified data source
        :param name: Data source name
        :param method: Method name
        :param args: Positional arguments
        :param kwargs: Keyword arguments
        :return: Method execution result
        """
        strategy = self.get_data_source(name)
        if not hasattr(strategy, method):
            raise AttributeError(f"Data source does not support method: {method}")

        return getattr(strategy, method)(*args, **kwargs)

    def get_datasource_info(self, name: str = None) -> Dict[str, Any]:
        """
        Get detailed data source information
        :param name: Data source name, returns default data source info when None
        :return: Data source information
        """
        if name is None:
            name = self._default_source

        if name not in self._data_sources:
            raise ValueError(f"Data source '{name}' does not exist")

        config = self._config['datasources'].get(name, {})
        strategy = self._data_sources[name]

        return {
            'name': name,
            'type': strategy.__class__.__name__.replace('Strategy', '').lower(),
            'host': config.get('host'),
            'port': config.get('port'),
            'database': config.get('database'),
            'user': config.get('user'),
            'is_default': name == self._default_source,
            'connection_pool': {
                'minCached': config.get('minCached'),
                'maxCached': config.get('maxCached'),
                'maxConnections': config.get('maxConnections')
            } if config.get('minCached') else None
        }


# Global data source manager instance
_manager_instance: Optional[DataSourceManager] = None


def get_manager() -> DataSourceManager:
    """Get global data source manager instance"""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = DataSourceManager()
    return _manager_instance


def reset_manager():
    """Reset manager (mainly used for testing)"""
    global _manager_instance
    _manager_instance = None
    # Also clear configuration cache
    DataSourceManager._cached_config = None
    DataSourceManager._config_loaded = False
