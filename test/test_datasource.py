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
    # Test table structure comparison and generate ALTER TABLE SQL
    print("\n" + "=" * 60)
    print("Table Structure Comparison (Generate ALTER TABLE SQL):")
    print("=" * 60)
    result = compare_table_structure("undo_log", "admin_db", "order_db", generate_sql=True)

    # Filter out lines with special characters, only print key information
    lines = result.split('\n')
    for line in lines:
        try:
            print(line)
        except UnicodeEncodeError:
            # Skip lines that cannot be printed
            if '✅' in line:
                print("Table structures are identical in both data sources!")
            elif '⚠' in line:
                print("Structural differences found, please check details above.")
            else:
                pass


if __name__ == "__main__":
    main()
