"""
Multi-data source functionality test script
Used to test data source manager and configuration loader functionality
"""

import sys
from pathlib import Path
from typing import Optional

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.factory.datasource_manager import get_manager

manager = get_manager()


def list_tables(datasource: Optional[str] = None) -> str:
    """List all tables in the database"""
    try:
        strategy = manager.get_data_source(datasource)
        return strategy.list_tables()
    except Exception as e:
        return f"Failed to list tables: {str(e)}"


def describe_table(table_name: str, datasource: Optional[str] = None) -> str:
    """Show the schema and column information for a given table

    Args:
        table_name: Name of the table to describe
        datasource: Optional data source name, uses default if None
    """
    try:
        strategy = manager.get_data_source(datasource)
        return strategy.describe_Table(table_name)
    except Exception as e:
        return f"Failed to describe table: {str(e)}"


def compare_table_structure(
        table_name: str,
        source1: str,
        source2: str,
        generate_sql: bool = False
) -> str:
    """Compare the structure of a table between two data sources

    Args:
        table_name: Name of the table to compare
        source1: First data source name
        source2: Second data source name
        generate_sql: Whether to generate ALTER TABLE SQL statements

    Returns:
        Detailed comparison report showing differences in table structure
    """
    try:
        # Get strategy objects for both data sources
        strategy1 = manager.get_data_source(source1)
        strategy2 = manager.get_data_source(source2)

        # Use MySQLStrategy's compare_table_with method
        if hasattr(strategy1, 'compare_table_with'):
            return strategy1.compare_table_with(table_name, strategy2, generate_sql)
        else:
            return f"Data source {source1} does not support table structure comparison"

    except Exception as e:
        return f"Table structure comparison failed: {str(e)}"


def execute_sql(
        sql: str,
        datasource: Optional[str] = None,
        params: Optional[tuple] = None
) -> str:
    """Execute SQL statement and return results

    Args:
        sql: SQL query to execute
        datasource: Optional data source name, uses default if None
        params: Optional parameters for parameterized queries
    """
    try:
        strategy = manager.get_data_source(datasource)
        return strategy.execute_sql(sql, params)
    except Exception as e:
        return f"Failed to execute SQL: {str(e)}"


def export_data(
        table_name: str,
        datasource: Optional[str] = None,
        file_path: Optional[str] = None
) -> str:
    """Export table data to SQL file

    Args:
        table_name: Name of the table to export
        datasource: Optional data source name, uses default if None
        file_path: Optional file path, defaults to export_data/ directory
    """
    try:
        strategy = manager.get_data_source(datasource)
        return strategy.export_data(table_name, file_path)
    except Exception as e:
        return f"Failed to export data: {str(e)}"


def execute_sql_file(
        file_path: str,
        datasource: Optional[str] = None
) -> str:
    """Execute SQL from file(s) - supports single .sql file or directory

    Args:
        file_path: Path to .sql file or directory with .sql files
        datasource: Optional data source name, uses default if None
    """
    try:
        strategy = manager.get_data_source(datasource)
        return strategy.execute_sql_file(file_path)
    except Exception as e:
        return f"Failed to execute SQL file: {str(e)}"


def main():
    print(compare_table_structure('order', 'postgresql_test_db', 'postgresql_db', generate_sql=True))


if __name__ == "__main__":
    main()
