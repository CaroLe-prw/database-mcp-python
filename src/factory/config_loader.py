import json
import os
from typing import Dict, Any

import yaml


class ConfigLoader:
    """Configuration loader supporting both yaml and env configuration methods"""

    @staticmethod
    def load() -> Dict[str, Any]:
        """
        Load configuration, priority:
        1. If DATABASE_CONFIG_FILE environment variable exists and file exists -> use yaml/json
        2. If yaml/json file doesn't exist but .env has database config -> use .env (single data source)
        3. Neither exists -> throw configuration error
        """
        # Try to load yaml/json configuration
        config_file = os.getenv('DATABASE_CONFIG_FILE', './database-config.yaml')

        if os.path.exists(config_file):
            return ConfigLoader._load_from_file(config_file)

        # Try default database-config.json
        if os.path.exists('./database-config.json'):
            return ConfigLoader._load_from_file('./database-config.json')

        # yaml/json doesn't exist, check .env configuration
        if os.getenv('db_type'):
            return ConfigLoader._load_from_env()

        # Neither exists
        raise ValueError(
            "Database configuration not found. Please configure one of the following:\n"
            "1. Create database-config.yaml or database-config.json\n"
            "2. Configure database connection info in .env"
        )

    @staticmethod
    def _load_from_file(config_file: str) -> Dict[str, Any]:
        """Load from configuration file"""
        print(f"[Config] Using configuration file: {config_file}")

        with open(config_file, 'r', encoding='utf-8') as f:
            if config_file.endswith('.yaml') or config_file.endswith('.yml'):
                config = yaml.safe_load(f)
            elif config_file.endswith('.json'):
                config = json.load(f)
            else:
                raise ValueError(f"Unsupported configuration file format: {config_file}")

        # Validate configuration format
        if 'datasources' not in config:
            raise ValueError("Configuration file must contain 'datasources' field")

        # Set default data source
        if 'default' not in config:
            # If no default specified, use first data source
            config['default'] = next(iter(config['datasources'].keys()))

        return config

    @staticmethod
    def _load_from_env() -> Dict[str, Any]:
        """Load from environment variables (backward compatible)"""
        print("[Config] Using .env configuration (single data source mode)")

        config = {
            'datasources': {
                'default': {
                    'type': os.getenv('db_type'),
                    'host': os.getenv('host'),
                    'port': int(os.getenv('port')),
                    'user': os.getenv('user'),
                    'password': os.getenv('password'),
                    'database': os.getenv('database')
                }
            },
            'default': 'default'
        }

        # Add optional connection pool configuration
        optional_fields = ['minCached', 'maxCached', 'maxConnections']
        for field in optional_fields:
            value = os.getenv(field)
            if value:
                config['datasources']['default'][field] = int(value)

        return config


def load_config() -> Dict[str, Any]:
    """Convenience function: load configuration"""
    return ConfigLoader.load()
