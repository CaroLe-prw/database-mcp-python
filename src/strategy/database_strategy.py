import os
from abc import ABC, abstractmethod
from typing import Any, List, Tuple

from dbutils.pooled_db import PooledDB

from src.model import DatabaseConfig


class DatabaseStrategy(ABC):
    """Database connection strategy abstract base class"""

    def __init__(self, config: DatabaseConfig):
        self.config = config

    @abstractmethod
    def create_pool(self) -> PooledDB:
        """Create and return database connection pool"""
        pass

    @abstractmethod
    def get_connection(self) -> Any:
        """Get a database connection from connection pool"""
        pass

    @abstractmethod
    def list_tables(self) -> str:
        """
        Get list of all tables in current database

        Features:
        - Query information_schema.tables to get table names and comments
        - Only return tables from current database
        - Return in formatted table format

        Returns:
            str: Formatted table string containing table names and comments

        Raises:
            Exception: Thrown when database connection or query fails
        """
        pass

    @abstractmethod
    def describe_Table(self, table_name: str) -> str:
        """
        Get detailed structure information of specified table

        Features:
        - Query all field information of table (field name, type, default value, etc.)
        - Query index information for each field
        - Add index names to KEY column display
        - Return in formatted table format

        Args:
            table_name (str): Table name to query

        Returns:
            str: Formatted table string containing complete field information

        Raises:
            Exception: Thrown when database connection or query fails
        """
        pass

    @abstractmethod
    def close_connection(self, connection: object) -> None:
        """Close connection"""
        pass

    @abstractmethod
    def execute_sql(self, sql: str, params: tuple = None) -> str:
        """
        Execute single SQL statement

        Features:
        - Support SELECT query and DML/DDL statement execution
        - SELECT statements return formatted table results
        - Other statements return number of affected rows
        - Automatically handle transactions (non-SELECT statements)

        Args:
            sql (str): SQL statement to execute
            params (tuple, optional): SQL parameters for parameterized queries

        Returns:
            str: SELECT queries return formatted tables, others return affected rows info

        Raises:
            Exception: Thrown when SQL execution fails or database connection fails
        """
        pass

    @abstractmethod
    def export_data(self, table_name: str, file_path: str = None) -> str:
        """
        Export table data as INSERT SQL statement files

        Features:
        - Export all data in table as INSERT statements
        - Support batch export for large tables (1000 records per file)
        - Automatically handle SQL escaping for various data types
        - Support custom export path, default export to project's export_data directory

        Args:
            table_name (str): Table name to export
            file_path (str, optional): Export file path, use default path when None

        Returns:
            str: Export result information, including exported row count and file path

        Raises:
            ValueError: Thrown when table name is invalid
            Exception: Thrown when database connection or query fails
        """
        pass

    @abstractmethod
    def execute_sql_file(self, file_path: str) -> str:
        """
         Execute SQL file or all SQL files in directory

         Features:
         - Support executing single .sql file
         - Support executing all .sql files in directory
         - Automatically split multiple SQL statements (split by semicolon)
         - Execute in transaction, automatically rollback on error
         - Special handling of ALTER TABLE statement return values (count as 1 affected record)

         Args:
             file_path (str): SQL file path or directory path containing SQL files

         Returns:
             str: Execution result information, including affected row count

         Raises:
             FileNotFoundError: Thrown when file or directory does not exist
             ValueError: Thrown when file type is invalid (non-.sql file)
             Exception: Thrown when SQL execution fails or database connection fails
         """
        pass

    @abstractmethod
    def get_table_structure(self, table_name: str) -> dict:
        """
        Get table structure information, return dictionary format for easy comparison

        Args:
            table_name: Table name

        Returns:
            Dictionary with field names as keys and field attribute dictionaries as values
        """
        pass

    @abstractmethod
    def compare_table_with(self, table_name: str, other_strategy: 'DatabaseStrategy',
                           generate_sql: bool = False) -> str:
        """
        Compare structure differences of same table between current data source and another data source

        Args:
            table_name: Table name to compare
            other_strategy: Strategy object of another data source
            generate_sql: Whether to generate ALTER TABLE SQL statements

        Returns:
            Formatted string containing difference information
        """
        pass

    @staticmethod
    def format_table(headers: List[str], rows: List[Tuple]) -> str:
        result = []

        if not rows:
            return ""

        def get_display_width(text: str) -> int:
            """Calculate display width of string, Chinese characters count as 2 width units"""
            width = 0
            for char in text:
                if ord(char) > 127:
                    width += 2
                else:
                    width += 1
            return width

        def pad_string(text: str, target_width: int) -> str:
            """Pad string according to display width"""
            current_width = get_display_width(text)
            padding_needed = target_width - current_width
            return text + " " * padding_needed

        col_widths = []
        for i, header in enumerate(headers):
            max_width = get_display_width(header)
            for row in rows:
                cell_value = str(row[i]) if row[i] is not None else ""
                max_width = max(max_width, get_display_width(cell_value))
            col_widths.append(max_width)

        header_parts = []
        for i in range(len(headers)):
            padded_header = pad_string(headers[i], col_widths[i])
            header_parts.append(padded_header)
        header_line = " | ".join(header_parts)
        result.append(header_line)

        separator = " | ".join("-" * col_widths[i] for i in range(len(headers)))
        result.append(separator)

        for row in rows:
            row_parts = []
            for i in range(len(headers)):
                cell_value = str(row[i]) if row[i] is not None else ""
                padded_cell = pad_string(cell_value, col_widths[i])
                row_parts.append(padded_cell)
            row_line = " | ".join(row_parts)
            result.append(row_line)

        return "\n".join(result)

    @staticmethod
    def format_update(affected_rows: int) -> str:
        return f"Successfully modified {affected_rows} rows"

    @staticmethod
    def read_all_files(file_path: str) -> List[str]:
        """Check files in directory"""
        files = os.listdir(file_path)
        sql_content = []
        for file in files:
            full_path = os.path.join(file_path, file)
            if os.path.isdir(full_path):
                sql_content.extend(DatabaseStrategy.read_all_files(full_path))
            else:
                if not file.endswith('.sql'):
                    continue
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    sql_content.append(content)

        return sql_content

    def format_comparison_result(self, table_name: str, my_structure: dict, other_structure: dict,
                                 other_strategy: 'DatabaseStrategy', sql_file_path: str = None) -> str:
        """Format table structure comparison result

        Args:
            table_name: Table name
            my_structure: Current data source table structure
            other_structure: Another data source table structure
            other_strategy: Another data source strategy object
            sql_file_path: SQL file save path (optional)

        Returns:
            Formatted comparison result string
        """
        result = [f"Table Structure Comparison: {table_name}", "=" * 60, f"Data Source 1: {self.config.database}@{self.config.host}",
                  f"Data Source 2: {other_strategy.config.database}@{other_strategy.config.host}", "=" * 60]

        # Get column sets
        my_cols = set(my_structure.keys())
        other_cols = set(other_structure.keys())

        # Columns only in source 1
        only_in_mine = my_cols - other_cols
        if only_in_mine:
            result.append(f"\nColumns only in Data Source 1:")
            for col in sorted(only_in_mine):
                col_info = my_structure[col]
                result.append(f"  + {col} ({col_info['type']})")

        # Columns only in source 2
        only_in_other = other_cols - my_cols
        if only_in_other:
            result.append(f"\nColumns only in Data Source 2:")
            for col in sorted(only_in_other):
                col_info = other_structure[col]
                result.append(f"  - {col} ({col_info['type']})")

        # Common columns with different attributes
        common_cols = my_cols & other_cols
        different_cols = []

        for col in common_cols:
            my_info = my_structure[col]
            other_info = other_structure[col]

            differences = []
            if my_info['type'] != other_info['type']:
                differences.append(f"Type: {my_info['type']} vs {other_info['type']}")
            if my_info['nullable'] != other_info['nullable']:
                differences.append(f"Nullable: {my_info['nullable']} vs {other_info['nullable']}")
            if my_info.get('key', '') != other_info.get('key', ''):
                differences.append(f"Key: {my_info.get('key', '')} vs {other_info.get('key', '')}")
            if my_info.get('default', 'NULL') != other_info.get('default', 'NULL'):
                differences.append(f"Default: {my_info.get('default', 'NULL')} vs {other_info.get('default', 'NULL')}")
            if my_info.get('extra', '') != other_info.get('extra', ''):
                differences.append(f"Extra: {my_info.get('extra', '')} vs {other_info.get('extra', '')}")

            if differences:
                different_cols.append((col, differences))

        if different_cols:
            result.append(f"\nColumns with different attributes:")
            for col, diffs in sorted(different_cols):
                result.append(f"  Column: {col}")
                for diff in diffs:
                    result.append(f"    - {diff}")

        # SQL file path (if provided)
        if sql_file_path:
            result.append(f"\nSQL statements saved to: {sql_file_path}")

        # Statistics
        result.append("\n" + "=" * 60)
        result.append("Statistics:")
        result.append(f"  Data Source 1 columns: {len(my_cols)}")
        result.append(f"  Data Source 2 columns: {len(other_cols)}")
        result.append(f"  Common columns: {len(common_cols)}")
        result.append(f"  Only in Data Source 1: {len(only_in_mine)}")
        result.append(f"  Only in Data Source 2: {len(only_in_other)}")
        result.append(f"  Columns with different attributes: {len(different_cols)}")

        if not only_in_mine and not only_in_other and not different_cols:
            result.append("\n✅ Table structures are identical in both data sources!")
        else:
            result.append("\n⚠️ Structural differences found, please check details above.")

        return "\n".join(result)
